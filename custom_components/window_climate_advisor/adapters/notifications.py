"""Native Home Assistant notification delivery boundary."""

from __future__ import annotations

import logging
from collections.abc import Collection

from homeassistant.components.notify.const import (
    ATTR_MESSAGE,
    ATTR_TITLE,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.components.notify.const import (
    DOMAIN as NOTIFY_DOMAIN,
)
from homeassistant.components.person import ATTR_DEVICE_TRACKERS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_HOME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations

from ..application.notifications import (
    ArrivalNotificationCandidate,
    recipient_persons_from_mappings,
)
from ..application.state import NotificationCandidate
from ..const import (
    CONF_HAS_BLIND,
    CONF_ROOM_SUBENTRY_ID,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
    SUBENTRY_TYPE_ROOM,
)
from ..domain.policy import recommendation_for_state

_LOGGER = logging.getLogger(__name__)
_RECOMMENDATION_STATE_KEY = (
    f"component.{DOMAIN}.entity.sensor.recommendation.state.{{state}}"
)
_BLIND_NAME_KEY = f"component.{DOMAIN}.entity.sensor.recommended_blind_position.name"
_MANUAL_BLIND_NOTE = {
    "en": "manual position not observable",
    "es": "posición manual no observable",
}


def _opening_label(entry: ConfigEntry, opening_id: str) -> tuple[str, str, str] | None:
    """Return sortable room/opening labels for a configured opening."""
    opening = entry.subentries.get(opening_id)
    if opening is None or opening.subentry_type != SUBENTRY_TYPE_OPENING:
        return None
    room_id = opening.data.get(CONF_ROOM_SUBENTRY_ID)
    room = entry.subentries.get(room_id) if isinstance(room_id, str) else None
    room_title = (
        room.title
        if room is not None and room.subentry_type == SUBENTRY_TYPE_ROOM
        else ""
    )
    label = " / ".join(part for part in (room_title, opening.title) if part)
    return room_title, opening.title, label


def _message_rows(
    entry: ConfigEntry,
    candidate: NotificationCandidate,
    translations: dict[str, str],
) -> tuple[str, ...]:
    """Render changed openings in deterministic room/opening order."""
    rows: list[tuple[tuple[str, str, str], str]] = []
    for change in candidate.changes:
        labels = _opening_label(entry, change.opening_id)
        if labels is None:
            continue
        room_title, opening_title, label = labels
        opening = entry.subentries[change.opening_id]
        state = recommendation_for_state(change.state.window).value
        state_label = translations.get(
            _RECOMMENDATION_STATE_KEY.format(state=state), state
        )
        row = f"{label}: {state_label}"
        if opening.data.get(CONF_HAS_BLIND) is True:
            blind_label = translations.get(_BLIND_NAME_KEY, "Blind")
            row += f" · {blind_label}: {change.state.blind.percent:g} %"
        rows.append(
            ((room_title.casefold(), opening_title.casefold(), change.opening_id), row)
        )
    rows.sort(key=lambda item: item[0])
    return tuple(row for _, row in rows)


def _arrival_message_rows(
    entry: ConfigEntry,
    candidate: ArrivalNotificationCandidate,
    translations: dict[str, str],
    language: str,
) -> tuple[str, ...]:
    """Render only still-actionable arrival advice in stable order."""
    rows: list[tuple[tuple[str, str, str], str]] = []
    manual_note = _MANUAL_BLIND_NOTE.get(
        language.split("-", 1)[0], _MANUAL_BLIND_NOTE["en"]
    )
    blind_label = translations.get(_BLIND_NAME_KEY, "Blind")
    for advice in candidate.openings:
        labels = _opening_label(entry, advice.opening_id)
        if labels is None:
            continue
        room_title, opening_title, label = labels
        actions: list[str] = []
        if advice.window is not None:
            state = recommendation_for_state(advice.window).value
            actions.append(
                translations.get(_RECOMMENDATION_STATE_KEY.format(state=state), state)
            )
        if advice.blind is not None:
            blind = f"{blind_label}: {advice.blind.percent:g} %"
            if advice.manual_blind_unobserved:
                blind += f" ({manual_note})"
            actions.append(blind)
        rows.append(
            (
                (room_title.casefold(), opening_title.casefold(), advice.opening_id),
                f"{label}: {' · '.join(actions)}",
            )
        )
    rows.sort(key=lambda item: item[0])
    return tuple(row for _, row in rows)


def _recipients(entry: ConfigEntry) -> tuple[str, ...]:
    """Decode configured recipients at the delivery boundary."""
    return recipient_persons_from_mappings(
        subentry.data
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_RECIPIENT
    )


def notification_targets_for_person(
    hass: HomeAssistant,
    person_entity_id: str,
    *,
    home_only: bool,
) -> tuple[str, ...]:
    """Resolve a person's Mobile App notification entities through registries."""
    person = hass.states.get(person_entity_id)
    if person is None:
        return ()
    tracker_ids = person.attributes.get(ATTR_DEVICE_TRACKERS)
    if not isinstance(tracker_ids, list | tuple):
        return ()

    registry = er.async_get(hass)
    targets: set[str] = set()
    for tracker_id in tracker_ids:
        if not isinstance(tracker_id, str):
            continue
        if home_only and not hass.states.is_state(tracker_id, STATE_HOME):
            continue
        tracker = registry.async_get(tracker_id)
        if (
            tracker is None
            or tracker.platform != "mobile_app"
            or tracker.disabled_by is not None
            or tracker.device_id is None
        ):
            continue
        targets.update(
            sibling.entity_id
            for sibling in er.async_entries_for_device(registry, tracker.device_id)
            if sibling.domain == NOTIFY_DOMAIN and sibling.platform == "mobile_app"
        )
    return tuple(sorted(targets))


async def _async_send_message(
    hass: HomeAssistant,
    entry: ConfigEntry,
    notify_entity_id: str,
    message: str,
) -> bool:
    """Send one native message when the resolved target remains available."""
    target = hass.states.get(notify_entity_id)
    if target is None or target.state == STATE_UNAVAILABLE:
        return False
    try:
        await hass.services.async_call(
            NOTIFY_DOMAIN,
            SERVICE_SEND_MESSAGE,
            {
                ATTR_ENTITY_ID: notify_entity_id,
                ATTR_MESSAGE: message,
                ATTR_TITLE: entry.title,
            },
            blocking=True,
        )
    except HomeAssistantError:
        _LOGGER.warning("Notification delivery failed for a configured recipient")
        return False
    return True


async def async_deliver_notification_candidate(
    hass: HomeAssistant,
    entry: ConfigEntry,
    candidate: NotificationCandidate | None,
    excluded_person_entity_ids: Collection[str] = (),
) -> int:
    """Deliver one grouped change to each currently home valid recipient."""
    if candidate is None or not candidate.changes:
        return 0
    if not hass.services.has_service(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE):
        return 0
    try:
        recipients = _recipients(entry)
    except ValueError:
        _LOGGER.warning(
            "Skipped notification delivery: invalid recipient configuration"
        )
        return 0
    if not recipients:
        return 0
    translations = await async_get_translations(
        hass, hass.config.language, "entity", (DOMAIN,)
    )
    rows = _message_rows(entry, candidate, translations)
    if not rows:
        return 0
    message = "\n".join(rows)
    delivered = 0
    seen_targets: set[str] = set()
    for person_entity_id in sorted(recipients):
        if person_entity_id in excluded_person_entity_ids:
            continue
        for target in notification_targets_for_person(
            hass, person_entity_id, home_only=True
        ):
            if target in seen_targets:
                continue
            seen_targets.add(target)
            if await _async_send_message(hass, entry, target, message):
                delivered += 1
    return delivered


async def async_deliver_arrival_candidate(
    hass: HomeAssistant,
    entry: ConfigEntry,
    person_entity_id: str,
    candidate: ArrivalNotificationCandidate | None,
) -> int:
    """Deliver fresh actionable advice only to one arriving recipient."""
    if candidate is None or not candidate.openings:
        return 0
    if not hass.services.has_service(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE):
        return 0
    try:
        configured = person_entity_id in _recipients(entry)
    except ValueError:
        _LOGGER.warning(
            "Skipped notification delivery: invalid recipient configuration"
        )
        return 0
    if not configured:
        return 0
    translations = await async_get_translations(
        hass, hass.config.language, "entity", (DOMAIN,)
    )
    rows = _arrival_message_rows(entry, candidate, translations, hass.config.language)
    if not rows:
        return 0
    message = "\n".join(rows)
    delivered = 0
    for target in notification_targets_for_person(
        hass, person_entity_id, home_only=True
    ):
        if await _async_send_message(hass, entry, target, message):
            delivered += 1
    return delivered
