"""Tests for contextual native notification delivery."""

import logging

import pytest
from homeassistant.components.notify.const import (
    ATTR_MESSAGE,
    ATTR_TITLE,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.components.notify.const import (
    DOMAIN as NOTIFY_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor.adapters.notifications import (
    async_deliver_notification_candidate,
)
from custom_components.window_climate_advisor.application.state import (
    NotificationCandidate,
    OpeningChange,
)
from custom_components.window_climate_advisor.const import (
    CONF_HAS_BLIND,
    CONF_NOTIFY_ENTITY_ID,
    CONF_PERSON_ENTITY_ID,
    CONF_ROOM_SUBENTRY_ID,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
    SUBENTRY_TYPE_ROOM,
    VERSION,
)
from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    WindowState,
)
from custom_components.window_climate_advisor.domain.state_machine import (
    OpeningStabilityState,
)


def _entry() -> MockConfigEntry:
    """Create a delivery-only entry with mixed recipients and two rooms."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Casa",
        version=VERSION,
        subentries_data=[
            {
                "subentry_type": SUBENTRY_TYPE_ROOM,
                "title": "Salón",
                "data": {},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_ROOM,
                "title": "Dormitorio",
                "data": {},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Sur",
                "data": {CONF_ROOM_SUBENTRY_ID: "room_living", CONF_HAS_BLIND: True},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Norte",
                "data": {
                    CONF_ROOM_SUBENTRY_ID: "room_bedroom",
                    CONF_HAS_BLIND: False,
                },
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "first",
                "data": {
                    CONF_PERSON_ENTITY_ID: "person.first",
                    CONF_NOTIFY_ENTITY_ID: "notify.first",
                },
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "away",
                "data": {
                    CONF_PERSON_ENTITY_ID: "person.away",
                    CONF_NOTIFY_ENTITY_ID: "notify.away",
                },
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "second",
                "data": {
                    CONF_PERSON_ENTITY_ID: "person.second",
                    CONF_NOTIFY_ENTITY_ID: "notify.second",
                },
                "unique_id": None,
            },
        ],
    )
    rooms = {
        subentry.title: subentry_id
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    }
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_OPENING:
            continue
        room_id = rooms["Salón" if subentry.title == "Sur" else "Dormitorio"]
        object.__setattr__(
            subentry,
            "data",
            type(subentry.data)({**subentry.data, CONF_ROOM_SUBENTRY_ID: room_id}),
        )
    return entry


def _change(
    entry: MockConfigEntry,
    opening_title: str,
    window: WindowState,
    blind_percent: float,
) -> OpeningChange:
    opening_id = next(
        subentry_id
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
        and subentry.title == opening_title
    )
    return OpeningChange(
        opening_id,
        OpeningStabilityState(window, BlindOpening(blind_percent)),
        True,
        True,
    )


def _candidate(entry: MockConfigEntry) -> NotificationCandidate:
    return NotificationCandidate(
        (
            _change(entry, "Sur", WindowState.OPEN, 70),
            _change(entry, "Norte", WindowState.TILT, 100),
        )
    )


def _set_recipient_states(hass: HomeAssistant) -> None:
    hass.states.async_set("person.first", STATE_HOME)
    hass.states.async_set("person.away", STATE_NOT_HOME)
    hass.states.async_set("person.second", STATE_HOME)
    hass.states.async_set("notify.first", "unknown")
    hass.states.async_set("notify.away", "unknown")
    hass.states.async_set("notify.second", "unavailable")


async def test_delivery_filters_presence_and_consolidates_in_stable_order(
    hass: HomeAssistant,
) -> None:
    """Send one translated grouped summary only to an available home target."""
    entry = _entry()
    _set_recipient_states(hass)
    calls: list[ServiceCall] = []

    async def send_message(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)

    assert (
        await async_deliver_notification_candidate(hass, entry, _candidate(entry)) == 1
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "notify.first",
        ATTR_MESSAGE: (
            "Dormitorio / Norte: Tilt\n"
            "Salón / Sur: Open · Recommended blind position: 70 %"
        ),
        ATTR_TITLE: "Casa",
    }


async def test_delivery_skips_empty_away_and_unavailable_surfaces(
    hass: HomeAssistant,
) -> None:
    """Discard unchanged or away-time advice without a queue or fallback."""
    entry = _entry()
    _set_recipient_states(hass)
    assert await async_deliver_notification_candidate(hass, entry, None) == 0
    assert (
        await async_deliver_notification_candidate(
            hass, entry, NotificationCandidate(())
        )
        == 0
    )
    assert (
        await async_deliver_notification_candidate(hass, entry, _candidate(entry)) == 0
    )

    async def send_message(_: ServiceCall) -> None:
        raise AssertionError("no recipient should be called")

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    hass.states.async_set("person.first", STATE_NOT_HOME)
    assert (
        await async_deliver_notification_candidate(hass, entry, _candidate(entry)) == 0
    )


async def test_delivery_failure_is_redacted_and_does_not_block_other_recipient(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Isolate a failing target while continuing with the remaining recipient."""
    entry = _entry()
    _set_recipient_states(hass)
    hass.states.async_set("notify.second", "unknown")
    calls: list[str] = []

    async def send_message(call: ServiceCall) -> None:
        target = call.data[ATTR_ENTITY_ID]
        calls.append(target)
        if target == "notify.first":
            raise HomeAssistantError("private failure")

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    with caplog.at_level(logging.WARNING):
        delivered = await async_deliver_notification_candidate(
            hass, entry, _candidate(entry)
        )

    assert delivered == 1
    assert calls == ["notify.first", "notify.second"]
    assert "Notification delivery failed for a configured recipient" in caplog.text
    assert all(private not in caplog.text for private in calls)
    assert "private failure" not in caplog.text
