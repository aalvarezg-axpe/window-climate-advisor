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
from homeassistant.components.person import ATTR_DEVICE_TRACKERS
from homeassistant.const import ATTR_ENTITY_ID, STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor.adapters.notifications import (
    _opening_label,
    async_deliver_arrival_candidate,
    async_deliver_notification_candidate,
    home_notification_recipient_persons,
    notification_targets_for_person,
)
from custom_components.window_climate_advisor.application.notifications import (
    ArrivalNotificationCandidate,
    ArrivalOpeningAdvice,
)
from custom_components.window_climate_advisor.application.state import (
    NotificationCandidate,
    OpeningChange,
)
from custom_components.window_climate_advisor.const import (
    CONF_HAS_BLIND,
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
from custom_components.window_climate_advisor.domain.policy import ReasonCode
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
                "subentry_type": SUBENTRY_TYPE_ROOM,
                "title": "Cocina",
                "data": {},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Salón · SE",
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
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Cocina · NO",
                "data": {CONF_ROOM_SUBENTRY_ID: "room_kitchen", CONF_HAS_BLIND: True},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Cocina · SO",
                "data": {CONF_ROOM_SUBENTRY_ID: "room_kitchen", CONF_HAS_BLIND: True},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "first",
                "data": {CONF_PERSON_ENTITY_ID: "person.first"},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "away",
                "data": {CONF_PERSON_ENTITY_ID: "person.away"},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "second",
                "data": {CONF_PERSON_ENTITY_ID: "person.second"},
                "unique_id": None,
            },
        ],
    )
    rooms = {
        subentry.title: subentry_id
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    }
    opening_rooms = {
        "Salón · SE": "Salón",
        "Norte": "Dormitorio",
        "Cocina · NO": "Cocina",
        "Cocina · SO": "Cocina",
    }
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_OPENING:
            continue
        room_id = rooms[opening_rooms[subentry.title]]
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
    reason: ReasonCode = ReasonCode.OPTIMIZER,
    *,
    window_changed: bool = True,
    blind_changed: bool = True,
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
        reason,
        window_changed,
        blind_changed,
    )


def _candidate(entry: MockConfigEntry) -> NotificationCandidate:
    return NotificationCandidate(
        (
            _change(
                entry,
                "Salón · SE",
                WindowState.TILT,
                70,
                ReasonCode.SOLAR_GAIN,
            ),
            _change(entry, "Norte", WindowState.OPEN, 100),
            _change(
                entry,
                "Cocina · NO",
                WindowState.CLOSED,
                0,
                ReasonCode.RAIN_CLOSE,
            ),
            _change(
                entry,
                "Cocina · SO",
                WindowState.CLOSED,
                0,
                ReasonCode.RAIN_CLOSE,
            ),
        )
    )


def test_multiple_openings_use_the_shortest_unique_configured_suffix() -> None:
    """Drop physical qualifiers once orientation already distinguishes a row."""
    entry = _entry()
    expected = {
        "Cocina · NO": ("Cocina · NO sin alero", "Cocina NO"),
        "Cocina · SO": ("Cocina · SO con alero", "Cocina SO"),
    }
    labels: set[str] = set()
    for opening_id, subentry in entry.subentries.items():
        if subentry.title not in expected:
            continue
        verbose_title, expected_label = expected[subentry.title]
        object.__setattr__(subentry, "title", verbose_title)
        labelled = _opening_label(entry, opening_id)
        assert labelled is not None
        labels.add(labelled[1])
        assert labelled[1] == expected_label

    assert labels == {"Cocina NO", "Cocina SO"}


def _add_mobile_device(
    hass: HomeAssistant,
    person_entity_id: str,
    suffix: str,
    tracker_state: str,
    notify_state: str,
    *,
    notify_disabled: bool = False,
) -> tuple[str, str]:
    """Register one Mobile App tracker and sibling notify entity for a person."""
    mobile_entry = MockConfigEntry(domain="mobile_app", unique_id=f"mobile-{suffix}")
    mobile_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=mobile_entry.entry_id,
        identifiers={("mobile_app", f"device-{suffix}")},
    )
    registry = er.async_get(hass)
    tracker = registry.async_get_or_create(
        "device_tracker",
        "mobile_app",
        f"tracker-{suffix}",
        suggested_object_id=suffix,
        disabled_by=er.RegistryEntryDisabler.USER if notify_disabled else None,
        config_entry=mobile_entry,
        device_id=device.id,
    )
    target = registry.async_get_or_create(
        NOTIFY_DOMAIN,
        "mobile_app",
        f"notify-{suffix}",
        suggested_object_id=suffix,
        config_entry=mobile_entry,
        device_id=device.id,
    )
    person = hass.states.get(person_entity_id)
    trackers = list(person.attributes.get(ATTR_DEVICE_TRACKERS, ())) if person else []
    trackers.append(tracker.entity_id)
    hass.states.async_set(
        person_entity_id,
        person.state if person else STATE_NOT_HOME,
        {ATTR_DEVICE_TRACKERS: trackers},
    )
    hass.states.async_set(tracker.entity_id, tracker_state)
    hass.states.async_set(target.entity_id, notify_state)
    return tracker.entity_id, target.entity_id


def _set_recipient_states(hass: HomeAssistant) -> dict[str, str]:
    hass.states.async_set("person.first", STATE_HOME)
    hass.states.async_set("person.away", STATE_NOT_HOME)
    hass.states.async_set("person.second", STATE_HOME)
    return {
        "first": _add_mobile_device(
            hass, "person.first", "first", STATE_HOME, "unknown"
        )[1],
        "away": _add_mobile_device(
            hass, "person.away", "away", STATE_NOT_HOME, "unknown"
        )[1],
        "second": _add_mobile_device(
            hass, "person.second", "second", STATE_HOME, "unavailable"
        )[1],
    }


def test_target_resolution_skips_missing_and_disabled_registry_paths(
    hass: HomeAssistant,
) -> None:
    """Fail closed when a tracker or its sibling notification target is unusable."""
    hass.states.async_set(
        "person.missing",
        STATE_HOME,
        {ATTR_DEVICE_TRACKERS: ["device_tracker.missing"]},
    )
    assert not notification_targets_for_person(hass, "person.missing", home_only=False)

    hass.states.async_set("person.disabled", STATE_HOME)
    _add_mobile_device(
        hass,
        "person.disabled",
        "disabled",
        STATE_HOME,
        "unknown",
        notify_disabled=True,
    )
    assert not notification_targets_for_person(hass, "person.disabled", home_only=False)


async def test_delivery_filters_presence_and_consolidates_in_stable_order(
    hass: HomeAssistant,
) -> None:
    """Send one translated grouped summary only to an available home target."""
    entry = _entry()
    hass.config.language = "es"
    targets = _set_recipient_states(hass)
    calls: list[ServiceCall] = []

    async def send_message(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)

    assert (
        await async_deliver_notification_candidate(hass, entry, _candidate(entry)) == 1
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: targets["first"],
        ATTR_MESSAGE: (
            "Ventanas:\n"
            "- Cocina NO: Cerrada (Lluvia y viento)\n"
            "- Cocina SO: Cerrada (Lluvia y viento)\n"
            "- Dormitorio: Abierta\n"
            "- Salón: Oscilobatiente "
            "(La radiación estimada en fachada supera la refrigeración al ventilar)\n\n"
            "Persianas:\n"
            "- Cocina NO: 0% (Lluvia y viento)\n"
            "- Cocina SO: 0% (Lluvia y viento)\n"
            "- Salón: 70% "
            "(La radiación estimada en fachada supera la refrigeración al ventilar)"
        ),
        ATTR_TITLE: "Casa",
    }


async def test_delivery_lists_only_changed_components_and_skips_degraded_rows(
    hass: HomeAssistant,
) -> None:
    """Keep window/blind sections truthful to the accepted grouped change."""
    entry = _entry()
    targets = _set_recipient_states(hass)
    calls: list[ServiceCall] = []

    async def send_message(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    candidate = NotificationCandidate(
        (
            _change(
                entry,
                "Salón · SE",
                WindowState.OPEN,
                70,
                window_changed=False,
            ),
            _change(
                entry,
                "Cocina · NO",
                WindowState.CLOSED,
                0,
                ReasonCode.WIND_CLOSE,
                blind_changed=False,
            ),
            _change(
                entry,
                "Norte",
                WindowState.CLOSED,
                100,
                blind_changed=False,
            ),
            _change(
                entry,
                "Cocina · SO",
                WindowState.CLOSED,
                0,
                ReasonCode.STALE_SAFETY_DATA,
            ),
        )
    )

    assert await async_deliver_notification_candidate(hass, entry, candidate) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: targets["first"],
        ATTR_MESSAGE: (
            "Windows:\n"
            "- Cocina NO: Closed (Wind)\n"
            "- Dormitorio: Closed\n\n"
            "Blinds:\n- Salón: 70%"
        ),
        ATTR_TITLE: "Casa",
    }


async def test_delivery_calls_a_shared_mobile_target_only_once(
    hass: HomeAssistant,
) -> None:
    """Deduplicate a malformed cross-person tracker relationship at runtime."""
    entry = _entry()
    targets = _set_recipient_states(hass)
    first = hass.states.get("person.first")
    second = hass.states.get("person.second")
    assert first is not None and second is not None
    first_tracker = first.attributes[ATTR_DEVICE_TRACKERS][0]
    second_trackers = list(second.attributes[ATTR_DEVICE_TRACKERS])
    hass.states.async_set(
        "person.second",
        STATE_HOME,
        {ATTR_DEVICE_TRACKERS: [*second_trackers, first_tracker]},
    )
    calls: list[ServiceCall] = []

    async def send_message(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)

    assert (
        await async_deliver_notification_candidate(hass, entry, _candidate(entry)) == 1
    )
    assert [call.data[ATTR_ENTITY_ID] for call in calls] == [targets["first"]]


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
    targets = _set_recipient_states(hass)
    hass.states.async_set(targets["second"], "unknown")
    caplog.clear()
    calls: list[str] = []

    async def send_message(call: ServiceCall) -> None:
        target = call.data[ATTR_ENTITY_ID]
        calls.append(target)
        if target == targets["first"]:
            raise HomeAssistantError("private failure")

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    with caplog.at_level(logging.WARNING):
        delivered = await async_deliver_notification_candidate(
            hass, entry, _candidate(entry)
        )

    assert delivered == 1
    assert calls == [targets["first"], targets["second"]]
    assert "Notification delivery failed for a configured recipient" in caplog.text
    assert all(private not in caplog.text for private in calls)
    assert "private failure" not in caplog.text


async def test_arrival_delivery_targets_only_arriving_person_and_marks_manual_blind(
    hass: HomeAssistant,
) -> None:
    """Send fresh advice to one person with explicit unobserved manual wording."""
    entry = _entry()
    targets = _set_recipient_states(hass)
    _, second_home_target = _add_mobile_device(
        hass, "person.first", "first-tablet", STATE_HOME, "unknown"
    )
    calls: list[ServiceCall] = []

    async def send_message(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    opening_id = next(
        subentry_id
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
        and subentry.title == "Salón · SE"
    )
    candidate = ArrivalNotificationCandidate(
        (
            ArrivalOpeningAdvice(
                opening_id,
                WindowState.TILT,
                BlindOpening(70),
                manual_blind_unobserved=True,
                reason=ReasonCode.SOLAR_GAIN,
            ),
        )
    )

    assert (
        await async_deliver_arrival_candidate(hass, entry, "person.first", candidate)
        == 2
    )
    assert len(calls) == 2
    expected = {
        ATTR_MESSAGE: (
            "Windows:\n- Salón: Tilt "
            "(Estimated facade radiation exceeds ventilation cooling)\n\n"
            "Blinds:\n- Salón: 70% "
            "(Estimated facade radiation exceeds ventilation cooling; "
            "manual position not observable)"
        ),
        ATTR_TITLE: "Casa",
    }
    assert {call.data[ATTR_ENTITY_ID] for call in calls} == {
        targets["first"],
        second_home_target,
    }
    assert all(
        {key: value for key, value in call.data.items() if key != ATTR_ENTITY_ID}
        == expected
        for call in calls
    )


async def test_ordinary_delivery_uses_only_people_retained_by_the_batch(
    hass: HomeAssistant,
) -> None:
    """Deliver only to the batch's event-time eligible recipient set."""
    entry = _entry()
    targets = _set_recipient_states(hass)
    hass.states.async_set(targets["second"], "unknown")
    calls: list[ServiceCall] = []

    async def send_message(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)

    assert (
        await async_deliver_notification_candidate(
            hass,
            entry,
            _candidate(entry),
            included_person_entity_ids={"person.second"},
        )
        == 1
    )
    assert [call.data[ATTR_ENTITY_ID] for call in calls] == [targets["second"]]


async def test_event_time_presence_requires_a_usable_home_mobile_route(
    hass: HomeAssistant,
) -> None:
    """Retain a batch only for recipients reachable when its change occurs."""
    entry = _entry()
    targets = _set_recipient_states(hass)

    assert home_notification_recipient_persons(hass, entry) == ()

    async def send_message(_: ServiceCall) -> None:
        pass

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    assert home_notification_recipient_persons(hass, entry) == ("person.first",)

    hass.states.async_set(targets["second"], "unknown")
    assert home_notification_recipient_persons(hass, entry) == (
        "person.first",
        "person.second",
    )
