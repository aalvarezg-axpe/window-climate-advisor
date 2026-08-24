"""Tests for entry setup and lifecycle handling."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor import async_migrate_entry
from custom_components.window_climate_advisor.const import (
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HEIGHT_M,
    CONF_NAME,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
    CONF_WIDTH_M,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_ROOM,
    VERSION,
)
from tests.integration.test_adapters import entry as advisor_entry
from tests.integration.test_adapters import set_ready_states


async def test_entry_setup_unload_and_update_listener_reload(
    hass: HomeAssistant,
) -> None:
    """Set up, update, reload, and unload the advisor platforms."""
    entry = advisor_entry()
    entry.add_to_hass(hass)
    set_ready_states(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == VERSION

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
    assert opening_id in entry.subentries
    assert entry.subentries[opening_id].data == {
        CONF_NAME: "Ventana",
        CONF_FACADE_AZIMUTH_DEG: 180,
        CONF_WIDTH_M: 1.6,
        CONF_HEIGHT_M: 1.2,
        CONF_OVERHANG_DEPTH_M: 0.5,
        CONF_OVERHANG_GAP_M: 0.2,
    }
    assert await async_migrate_entry(hass, entry)

    unsupported = MockConfigEntry(domain=DOMAIN, version=VERSION + 1)
    assert not await async_migrate_entry(hass, unsupported)
