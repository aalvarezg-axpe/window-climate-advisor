"""Native Home Assistant notification delivery boundary."""

from __future__ import annotations

import logging

from homeassistant.components.notify.const import (
    ATTR_MESSAGE,
    ATTR_TITLE,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.components.notify.const import (
    DOMAIN as NOTIFY_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_HOME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.translation import async_get_translations

from ..application.notifications import notification_recipients_from_mappings
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


def _message_rows(
    entry: ConfigEntry,
    candidate: NotificationCandidate,
    translations: dict[str, str],
) -> tuple[str, ...]:
    """Render changed openings in deterministic room/opening order."""
    rows: list[tuple[tuple[str, str, str], str]] = []
    for change in candidate.changes:
        opening = entry.subentries.get(change.opening_id)
        if opening is None or opening.subentry_type != SUBENTRY_TYPE_OPENING:
            continue
        room_id = opening.data.get(CONF_ROOM_SUBENTRY_ID)
        room = entry.subentries.get(room_id) if isinstance(room_id, str) else None
        room_title = (
            room.title
            if room is not None and room.subentry_type == SUBENTRY_TYPE_ROOM
            else ""
        )
        state = recommendation_for_state(change.state.window).value
        state_label = translations.get(
            _RECOMMENDATION_STATE_KEY.format(state=state), state
        )
        label = " / ".join(part for part in (room_title, opening.title) if part)
        row = f"{label}: {state_label}"
        if opening.data.get(CONF_HAS_BLIND) is True:
            blind_label = translations.get(_BLIND_NAME_KEY, "Blind")
            row += f" · {blind_label}: {change.state.blind.percent:g} %"
        rows.append(
            ((room_title.casefold(), opening.title.casefold(), change.opening_id), row)
        )
    rows.sort(key=lambda item: item[0])
    return tuple(row for _, row in rows)


async def async_deliver_notification_candidate(
    hass: HomeAssistant,
    entry: ConfigEntry,
    candidate: NotificationCandidate | None,
) -> int:
    """Deliver one grouped change to each currently home valid recipient."""
    if candidate is None or not candidate.changes:
        return 0
    if not hass.services.has_service(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE):
        return 0
    try:
        recipients = notification_recipients_from_mappings(
            subentry.data
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_RECIPIENT
        )
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
    for recipient in sorted(recipients, key=lambda item: item.person_entity_id):
        if not hass.states.is_state(recipient.person_entity_id, STATE_HOME):
            continue
        target = hass.states.get(recipient.notify_entity_id)
        if target is None or target.state == STATE_UNAVAILABLE:
            continue
        try:
            await hass.services.async_call(
                NOTIFY_DOMAIN,
                SERVICE_SEND_MESSAGE,
                {
                    ATTR_ENTITY_ID: recipient.notify_entity_id,
                    ATTR_MESSAGE: message,
                    ATTR_TITLE: entry.title,
                },
                blocking=True,
            )
        except HomeAssistantError:
            _LOGGER.warning("Notification delivery failed for a configured recipient")
        else:
            delivered += 1
    return delivered
