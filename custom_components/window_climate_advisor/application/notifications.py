"""Typed notification recipient configuration."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from ..const import CONF_NOTIFY_ENTITY_ID, CONF_PERSON_ENTITY_ID


@dataclass(frozen=True, slots=True)
class NotificationRecipient:
    """One explicit person-to-notify-entity mapping."""

    person_entity_id: str
    notify_entity_id: str

    def __post_init__(self) -> None:
        if not self.person_entity_id.startswith("person."):
            raise ValueError("recipient person must be a person entity")
        if not self.notify_entity_id.startswith("notify."):
            raise ValueError("recipient target must be a notify entity")


def notification_recipient_from_mapping(
    value: Mapping[str, object],
) -> NotificationRecipient:
    """Decode one persisted recipient without importing Home Assistant."""
    person_entity_id = value.get(CONF_PERSON_ENTITY_ID)
    notify_entity_id = value.get(CONF_NOTIFY_ENTITY_ID)
    if not isinstance(person_entity_id, str) or not isinstance(notify_entity_id, str):
        raise ValueError("recipient entity IDs must be strings")
    return NotificationRecipient(person_entity_id, notify_entity_id)


def notification_recipients_from_mappings(
    values: Iterable[Mapping[str, object]],
) -> tuple[NotificationRecipient, ...]:
    """Decode recipients and reject duplicate people or notification targets."""
    recipients = tuple(notification_recipient_from_mapping(value) for value in values)
    if len({recipient.person_entity_id for recipient in recipients}) != len(recipients):
        raise ValueError("recipient persons must be unique")
    if len({recipient.notify_entity_id for recipient in recipients}) != len(recipients):
        raise ValueError("recipient notification targets must be unique")
    return recipients
