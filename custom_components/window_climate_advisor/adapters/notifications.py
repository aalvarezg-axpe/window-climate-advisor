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

from ..application.notifications import (
    ArrivalNotificationCandidate,
    recipient_persons_from_mappings,
)
from ..application.state import NotificationCandidate
from ..const import (
    CONF_HAS_BLIND,
    CONF_ROOM_SUBENTRY_ID,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
    SUBENTRY_TYPE_ROOM,
)
from ..domain.policy import ReasonCode

_LOGGER = logging.getLogger(__name__)
_NOTIFICATION_TEXT = {
    "en": {
        "windows": "Windows",
        "blinds": "Blinds",
        "closed": "Closed",
        "tilt": "Tilt",
        "open": "Open",
        "manual": "manual position not observable",
        ReasonCode.SUMMER_COMFORT_FLOOR.value: "Lower comfort limit",
        ReasonCode.OUTDOOR_NOT_COOLER.value: "Outdoor air is not cooler",
        ReasonCode.SOLAR_GAIN.value: (
            "Estimated facade radiation exceeds ventilation cooling"
        ),
        ReasonCode.DIFFUSE_HEAT_PROTECTION.value: (
            "Outdoor heat and diffuse radiation protection"
        ),
        ReasonCode.STABILITY_MARGIN.value: (
            "Opening benefit is below the stability margin"
        ),
        ReasonCode.STABILITY_CONFIRMATION.value: (
            "Waiting for stable confirmation before opening further"
        ),
        ReasonCode.WIND_CLOSE.value: "Wind",
        ReasonCode.WIND_TILT_ONLY.value: "Wind",
        ReasonCode.RAIN_CLOSE.value: "Rain and wind",
        ReasonCode.RAIN_TILT_ONLY.value: "Rain and wind",
    },
    "es": {
        "windows": "Ventanas",
        "blinds": "Persianas",
        "closed": "Cerrada",
        "tilt": "Oscilobatiente",
        "open": "Abierta",
        "manual": "posición manual no observable",
        ReasonCode.SUMMER_COMFORT_FLOOR.value: "Límite inferior de confort",
        ReasonCode.OUTDOOR_NOT_COOLER.value: "El aire exterior no está más fresco",
        ReasonCode.SOLAR_GAIN.value: (
            "La radiación estimada en fachada supera la refrigeración al ventilar"
        ),
        ReasonCode.DIFFUSE_HEAT_PROTECTION.value: (
            "Protección ante calor exterior y radiación difusa"
        ),
        ReasonCode.STABILITY_MARGIN.value: (
            "La mejora de abrir no supera el margen de estabilidad"
        ),
        ReasonCode.STABILITY_CONFIRMATION.value: (
            "Esperando confirmación estable para abrir más"
        ),
        ReasonCode.WIND_CLOSE.value: "Viento",
        ReasonCode.WIND_TILT_ONLY.value: "Viento",
        ReasonCode.RAIN_CLOSE.value: "Lluvia y viento",
        ReasonCode.RAIN_TILT_ONLY.value: "Lluvia y viento",
    },
}
_UNACTIONABLE_REASONS = {
    ReasonCode.MISSING_SAFETY_DATA,
    ReasonCode.STALE_SAFETY_DATA,
}


def _text(language: str) -> dict[str, str]:
    return _NOTIFICATION_TEXT.get(language.split("-", 1)[0], _NOTIFICATION_TEXT["en"])


def _opening_label(
    entry: ConfigEntry, opening_id: str
) -> tuple[tuple[str, str, str], str, bool] | None:
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
    opening_count = sum(
        subentry.subentry_type == SUBENTRY_TYPE_OPENING
        and subentry.data.get(CONF_ROOM_SUBENTRY_ID) == room_id
        for subentry in entry.subentries.values()
    )
    if room_title and opening_count == 1:
        label = room_title
    elif room_title:

        def suffix(title: str) -> str:
            remainder = title[len(room_title) :]
            return (
                remainder.lstrip(" /·:-")
                if title[: len(room_title)].casefold() == room_title.casefold()
                and (not remainder or remainder[0] in " /·:-")
                else title
            )

        opening_suffix = suffix(opening.title)
        sibling_suffixes = tuple(
            suffix(subentry.title)
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_OPENING
            and subentry.data.get(CONF_ROOM_SUBENTRY_ID) == room_id
        )
        parts = opening_suffix.split()
        for end in range(1, len(parts) + 1):
            candidate = " ".join(parts[:end])
            if (
                sum(
                    item.casefold().startswith(candidate.casefold())
                    for item in sibling_suffixes
                )
                == 1
            ):
                opening_suffix = candidate
                break
        label = " ".join(part for part in (room_title, opening_suffix) if part)
    else:
        label = opening.title
    return (
        (room_title.casefold(), opening.title.casefold(), opening_id),
        label,
        opening.data.get(CONF_HAS_BLIND) is True,
    )


def _note(reason: ReasonCode, text: dict[str, str], *, manual: bool = False) -> str:
    notes = [text[reason.value]] if reason.value in text else []
    if manual:
        notes.append(text["manual"])
    return f" ({'; '.join(notes)})" if notes else ""


def _format_message(
    windows: tuple[str, ...], blinds: tuple[str, ...], language: str
) -> str:
    text = _text(language)
    sections = [
        f"{text[title]}:\n" + "\n".join(f"- {row}" for row in rows)
        for title, rows in (("windows", windows), ("blinds", blinds))
        if rows
    ]
    return "\n\n".join(sections)


def _message_rows(
    entry: ConfigEntry,
    candidate: NotificationCandidate,
    language: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Render changed window and blind rows in deterministic order."""
    text = _text(language)
    windows: list[tuple[tuple[str, str, str], str]] = []
    blinds: list[tuple[tuple[str, str, str], str]] = []
    for change in candidate.changes:
        labelled = _opening_label(entry, change.opening_id)
        if labelled is None or change.reason in _UNACTIONABLE_REASONS:
            continue
        sort_key, label, has_blind = labelled
        if change.window_changed:
            windows.append(
                (
                    sort_key,
                    f"{label}: {text[change.state.window.value]}"
                    f"{_note(change.reason, text)}",
                )
            )
        if change.blind_changed and has_blind:
            blinds.append(
                (
                    sort_key,
                    f"{label}: {change.state.blind.percent:g}%"
                    f"{_note(change.reason, text)}",
                )
            )
    windows.sort(key=lambda item: item[0])
    blinds.sort(key=lambda item: item[0])
    return (
        tuple(row for _, row in windows),
        tuple(row for _, row in blinds),
    )


def _arrival_message_rows(
    entry: ConfigEntry,
    candidate: ArrivalNotificationCandidate,
    language: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Render only still-actionable arrival advice in stable order."""
    text = _text(language)
    windows: list[tuple[tuple[str, str, str], str]] = []
    blinds: list[tuple[tuple[str, str, str], str]] = []
    for advice in candidate.openings:
        labelled = _opening_label(entry, advice.opening_id)
        if labelled is None:
            continue
        sort_key, label, _ = labelled
        if advice.window is not None:
            windows.append(
                (
                    sort_key,
                    f"{label}: {text[advice.window.value]}{_note(advice.reason, text)}",
                )
            )
        if advice.blind is not None:
            note = _note(
                advice.reason,
                text,
                manual=advice.manual_blind_unobserved,
            )
            blinds.append(
                (
                    sort_key,
                    f"{label}: {advice.blind.percent:g}%{note}",
                )
            )
    windows.sort(key=lambda item: item[0])
    blinds.sort(key=lambda item: item[0])
    return (
        tuple(row for _, row in windows),
        tuple(row for _, row in blinds),
    )


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


def home_notification_recipient_persons(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> tuple[str, ...]:
    """Return configured people with a usable Mobile App route currently home."""
    if not hass.services.has_service(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE):
        return ()
    try:
        recipients = _recipients(entry)
    except ValueError:
        _LOGGER.warning(
            "Skipped notification delivery: invalid recipient configuration"
        )
        return ()
    return tuple(
        person_entity_id
        for person_entity_id in sorted(recipients)
        if any(
            (target := hass.states.get(target_entity_id)) is not None
            and target.state != STATE_UNAVAILABLE
            for target_entity_id in notification_targets_for_person(
                hass,
                person_entity_id,
                home_only=True,
            )
        )
    )


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
    *,
    included_person_entity_ids: Collection[str] | None = None,
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
    windows, blinds = _message_rows(entry, candidate, hass.config.language)
    message = _format_message(windows, blinds, hass.config.language)
    if not message:
        return 0
    delivered = 0
    seen_targets: set[str] = set()
    for person_entity_id in sorted(recipients):
        if (
            included_person_entity_ids is not None
            and person_entity_id not in included_person_entity_ids
        ):
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
    windows, blinds = _arrival_message_rows(entry, candidate, hass.config.language)
    message = _format_message(windows, blinds, hass.config.language)
    if not message:
        return 0
    delivered = 0
    for target in notification_targets_for_person(
        hass, person_entity_id, home_only=True
    ):
        if await _async_send_message(hass, entry, target, message):
            delivered += 1
    return delivered
