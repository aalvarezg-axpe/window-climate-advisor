"""Tests for typed notification recipient configuration."""

import pytest

from custom_components.window_climate_advisor.application.notifications import (
    NotificationRecipient,
    notification_recipient_from_mapping,
    notification_recipients_from_mappings,
)
from custom_components.window_climate_advisor.const import (
    CONF_NOTIFY_ENTITY_ID,
    CONF_PERSON_ENTITY_ID,
)


def _mapping(person: str, target: str) -> dict[str, object]:
    return {
        CONF_PERSON_ENTITY_ID: person,
        CONF_NOTIFY_ENTITY_ID: target,
    }


def test_recipient_mapping_is_typed_and_ordered() -> None:
    """Decode persisted mappings without Home Assistant objects."""
    assert notification_recipient_from_mapping(
        _mapping("person.one", "notify.one")
    ) == NotificationRecipient("person.one", "notify.one")
    assert notification_recipients_from_mappings(
        [_mapping("person.two", "notify.two"), _mapping("person.one", "notify.one")]
    ) == (
        NotificationRecipient("person.two", "notify.two"),
        NotificationRecipient("person.one", "notify.one"),
    )


def test_recipient_mapping_rejects_missing_and_duplicate_targets() -> None:
    """Reject malformed, repeated-person, and repeated-target mappings."""
    for value in ({}, {CONF_PERSON_ENTITY_ID: "person.one"}):
        with pytest.raises(ValueError):
            notification_recipient_from_mapping(value)
    for value in (
        _mapping("sensor.one", "notify.one"),
        _mapping("person.one", "sensor.one"),
    ):
        with pytest.raises(ValueError):
            notification_recipient_from_mapping(value)
    with pytest.raises(ValueError, match="persons must be unique"):
        notification_recipients_from_mappings(
            [_mapping("person.one", "notify.one"), _mapping("person.one", "notify.two")]
        )
    with pytest.raises(ValueError, match="targets must be unique"):
        notification_recipients_from_mappings(
            [_mapping("person.one", "notify.one"), _mapping("person.two", "notify.one")]
        )
