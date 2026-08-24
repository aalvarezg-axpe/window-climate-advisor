"""Window Climate Advisor integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HEIGHT_M,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
    CONF_WIDTH_M,
    SUBENTRY_TYPE_OPENING,
    VERSION,
)

_V1_GEOMETRY_KEYS = {
    "facade_azimuth": CONF_FACADE_AZIMUTH_DEG,
    "width": CONF_WIDTH_M,
    "height": CONF_HEIGHT_M,
    "overhang_depth": CONF_OVERHANG_DEPTH_M,
    "overhang_gap": CONF_OVERHANG_GAP_M,
}


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate unit-implicit v1 opening geometry without changing identity."""
    if entry.version == VERSION:
        return True
    if entry.version != 1:
        return False

    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_OPENING:
            continue
        data = dict(subentry.data)
        for old_key, new_key in _V1_GEOMETRY_KEYS.items():
            if old_key in data:
                data[new_key] = data.pop(old_key)
        hass.config_entries.async_update_subentry(entry, subentry, data=data)
    hass.config_entries.async_update_entry(entry, version=VERSION)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a behaviour-free configuration entry."""
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a behaviour-free configuration entry."""
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload an entry after configuration changes."""
    await hass.config_entries.async_reload(entry.entry_id)
