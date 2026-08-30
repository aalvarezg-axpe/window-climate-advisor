"""Tests for entry setup and lifecycle handling."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor import async_migrate_entry
from custom_components.window_climate_advisor.const import (
    CONF_COVER_ENTITY_ID,
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HAS_BLIND,
    CONF_HEIGHT_M,
    CONF_NAME,
    CONF_NOTIFY_ENTITY_ID,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
    CONF_PERSON_ENTITY_ID,
    CONF_ROOM_TEMPERATURE_STALE_MINUTES,
    CONF_SOURCE_STALE_MINUTES,
    CONF_WIDTH_M,
    DOMAIN,
    MINOR_VERSION,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
    SUBENTRY_TYPE_ROOM,
    VERSION,
)
from tests.integration.test_adapters import entry as advisor_entry
from tests.integration.test_adapters import set_ready_states


async def test_entry_setup_unload_and_update_listener_reload(
    hass: HomeAssistant,
) -> None:
    """Set up, update, reload, and unload the advisor platforms."""
    entry = advisor_entry(recipient=True)
    entry.add_to_hass(hass)
    set_ready_states(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == VERSION
    assert entry.minor_version == MINOR_VERSION

    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as async_reload:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_NAME: "Casa actualizada"}
        )
        await hass.async_block_till_done()
        async_reload.assert_awaited_once_with(entry.entry_id)

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_v1_geometry_migration_preserves_subentry_identity(
    hass: HomeAssistant,
) -> None:
    """Rename only unit-implicit geometry keys and reject unknown versions."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "Casa"},
        version=1,
        subentries_data=[
            {
                "subentry_type": SUBENTRY_TYPE_ROOM,
                "title": "Salón",
                "data": {CONF_NAME: "Salón"},
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Ventana",
                "data": {
                    CONF_NAME: "Ventana",
                    "facade_azimuth": 180,
                    "width": 1.6,
                    "height": 1.2,
                    "overhang_depth": 0.5,
                    "overhang_gap": 0.2,
                },
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Ventana incompleta",
                "data": {CONF_NAME: "Ventana incompleta"},
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)
    opening = next(
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    opening_id = opening.subentry_id

    assert await async_migrate_entry(hass, entry)
    assert entry.version == VERSION
    assert entry.minor_version == MINOR_VERSION
    assert opening_id in entry.subentries
    assert entry.subentries[opening_id].data == {
        CONF_NAME: "Ventana",
        CONF_FACADE_AZIMUTH_DEG: 180,
        CONF_WIDTH_M: 1.6,
        CONF_HEIGHT_M: 1.2,
        CONF_OVERHANG_DEPTH_M: 0.5,
        CONF_OVERHANG_GAP_M: 0.2,
        CONF_HAS_BLIND: False,
    }
    assert await async_migrate_entry(hass, entry)

    unsupported = MockConfigEntry(domain=DOMAIN, version=VERSION + 1)
    assert not await async_migrate_entry(hass, unsupported)
    unsupported_minor = MockConfigEntry(
        domain=DOMAIN,
        version=VERSION,
        minor_version=MINOR_VERSION + 1,
    )
    assert not await async_migrate_entry(hass, unsupported_minor)


async def test_v2_migration_derives_physical_blind_from_existing_cover(
    hass: HomeAssistant,
) -> None:
    """Preserve legacy automated-cover capability through current schema."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        subentries_data=[
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Con persiana",
                "data": {
                    CONF_NAME: "Con persiana",
                    CONF_COVER_ENTITY_ID: "cover.blind",
                },
                "unique_id": None,
            },
            {
                "subentry_type": SUBENTRY_TYPE_OPENING,
                "title": "Sin persiana conocida",
                "data": {CONF_NAME: "Sin persiana conocida"},
                "unique_id": None,
            },
        ],
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == VERSION
    assert entry.minor_version == MINOR_VERSION
    migrated = {
        subentry.title: subentry.data[CONF_HAS_BLIND]
        for subentry in entry.subentries.values()
    }
    assert migrated == {"Con persiana": True, "Sin persiana conocida": False}


async def test_v3_migration_preserves_shared_source_age_semantics(
    hass: HomeAssistant,
) -> None:
    """Copy the old shared age into the new room boundary without guessing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        options={CONF_SOURCE_STALE_MINUTES: 15},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == VERSION
    assert entry.minor_version == MINOR_VERSION
    assert entry.options == {
        CONF_SOURCE_STALE_MINUTES: 15,
        CONF_ROOM_TEMPERATURE_STALE_MINUTES: 15,
    }


async def test_v4_recipient_migration_removes_redundant_notification_target(
    hass: HomeAssistant,
) -> None:
    """Retain the person and subentry identity while migrating the beta schema."""
    data = {
        CONF_PERSON_ENTITY_ID: "person.resident",
        CONF_NOTIFY_ENTITY_ID: "notify.phone",
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=4,
        minor_version=1,
        subentries_data=[
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "person.resident",
                "data": data,
                "unique_id": None,
            }
        ],
    )
    entry.add_to_hass(hass)
    recipient_id = next(iter(entry.subentries))

    assert await async_migrate_entry(hass, entry)
    assert entry.version == VERSION
    assert entry.minor_version == MINOR_VERSION
    assert entry.subentries[recipient_id].data == {
        CONF_PERSON_ENTITY_ID: "person.resident"
    }
