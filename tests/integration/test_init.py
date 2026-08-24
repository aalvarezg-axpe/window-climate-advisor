"""Tests for entry setup and lifecycle handling."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor.const import (
    CONF_NAME,
    DOMAIN,
)


async def test_entry_setup_unload_and_update_listener_reload(
    hass: HomeAssistant,
) -> None:
    """Set up, update, reload, and unload a behaviour-free entry."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_NAME: "Casa"})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED

    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as async_reload:
        hass.config_entries.async_update_entry(
            entry, data={CONF_NAME: "Casa actualizada"}
        )
        await hass.async_block_till_done()
        async_reload.assert_awaited_once_with(entry.entry_id)

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
