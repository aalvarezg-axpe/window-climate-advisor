"""Tests for the parent dwelling configuration flow."""

import math
from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntry,
    ConfigSubentry,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor.config_flow import (
    CONFIG_SCHEMA,
    OPTIONS_SCHEMA,
    ROOM_SCHEMA,
    settings_from_options,
)
from custom_components.window_climate_advisor.const import (
    CONF_BLIND_DEADBAND_PERCENT,
    CONF_BLIND_FULL_TRAVEL_PENALTY_W,
    CONF_BLIND_STEP_PERCENT,
    CONF_CO2_ENTITY_ID,
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HEIGHT_M,
    CONF_HUMIDITY_ENTITY_ID,
    CONF_MINIMUM_BENEFIT_W,
    CONF_MISSING_FORECAST_CHANGE_PENALTY_W,
    CONF_OUTDOOR_TEMPERATURE_ENTITY_ID,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
    CONF_RAIN_ENTITY_ID,
    CONF_RAIN_PROTECTED,
    CONF_ROOM_SUBENTRY_ID,
    CONF_SELECTION_MODE,
    CONF_SHOULDER_HYSTERESIS_C,
    CONF_SHOULDER_LOWER_C,
    CONF_SHOULDER_PRECONDITIONING_TARGET_C,
    CONF_SHOULDER_UPPER_C,
    CONF_SOLAR_RADIATION_ENTITY_ID,
    CONF_SOURCE_STALE_MINUTES,
    CONF_SUMMER_HYSTERESIS_C,
    CONF_SUMMER_LOWER_C,
    CONF_SUMMER_PRECONDITIONING_TARGET_C,
    CONF_SUMMER_UPPER_C,
    CONF_SUPPORTS_TILT,
    CONF_TEMPERATURE_ENTITY_ID,
    CONF_WEATHER_ENTITY_ID,
    CONF_WIDTH_M,
    CONF_WIND_DIRECTION_ENTITY_ID,
    CONF_WIND_GUST_ENTITY_ID,
    CONF_WIND_SPEED_ENTITY_ID,
    CONF_WINDOW_MOVEMENT_PENALTY_W,
    CONF_WINTER_HYSTERESIS_C,
    CONF_WINTER_LOWER_C,
    CONF_WINTER_PRECONDITIONING_TARGET_C,
    CONF_WINTER_UPPER_C,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_ROOM,
)

VALID_INPUT = {
    CONF_NAME: "Casa",
    CONF_OUTDOOR_TEMPERATURE_ENTITY_ID: "sensor.outdoor_temperature",
    CONF_WEATHER_ENTITY_ID: "weather.home",
    CONF_SOLAR_RADIATION_ENTITY_ID: "sensor.solar_radiation",
    CONF_WIND_SPEED_ENTITY_ID: "sensor.wind_speed",
    CONF_WIND_DIRECTION_ENTITY_ID: "sensor.wind_direction",
    CONF_WIND_GUST_ENTITY_ID: "sensor.wind_gust",
    CONF_RAIN_ENTITY_ID: "binary_sensor.rain",
}
ROOM_INPUT = {
    CONF_NAME: "Salón",
    CONF_TEMPERATURE_ENTITY_ID: "sensor.living_room_temperature",
    CONF_HUMIDITY_ENTITY_ID: "sensor.living_room_humidity",
    CONF_CO2_ENTITY_ID: "sensor.living_room_co2",
}
VALID_OPTIONS = {
    CONF_SELECTION_MODE: "auto",
    CONF_SUMMER_LOWER_C: 22,
    CONF_SUMMER_UPPER_C: 25,
    CONF_SUMMER_PRECONDITIONING_TARGET_C: 23,
    CONF_SUMMER_HYSTERESIS_C: 0.5,
    CONF_SHOULDER_LOWER_C: 20,
    CONF_SHOULDER_UPPER_C: 24,
    CONF_SHOULDER_PRECONDITIONING_TARGET_C: 22,
    CONF_SHOULDER_HYSTERESIS_C: 0.5,
    CONF_WINTER_LOWER_C: 19,
    CONF_WINTER_UPPER_C: 23,
    CONF_WINTER_PRECONDITIONING_TARGET_C: 21,
    CONF_WINTER_HYSTERESIS_C: 0.5,
    CONF_BLIND_STEP_PERCENT: 10,
    CONF_WINDOW_MOVEMENT_PENALTY_W: 20,
    CONF_BLIND_FULL_TRAVEL_PENALTY_W: 10,
    CONF_MISSING_FORECAST_CHANGE_PENALTY_W: 30,
    CONF_MINIMUM_BENEFIT_W: 50,
    CONF_BLIND_DEADBAND_PERCENT: 10,
    CONF_SOURCE_STALE_MINUTES: 15,
}


async def _create_room(hass: HomeAssistant, entry: ConfigEntry) -> ConfigSubentry:
    """Create and return one room through the production subentry flow."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ROOM), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=ROOM_INPUT
    )
    assert result["type"] == "create_entry"
    return next(iter(entry.subentries.values()))


async def test_user_flow_shows_typed_form_and_creates_entry(
    hass: HomeAssistant,
) -> None:
    """Show the parent form and create a valid dwelling entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] is None
    assert set(result["data_schema"].schema) == {
        CONF_NAME,
        CONF_OUTDOOR_TEMPERATURE_ENTITY_ID,
        CONF_WEATHER_ENTITY_ID,
        CONF_SOLAR_RADIATION_ENTITY_ID,
        CONF_WIND_SPEED_ENTITY_ID,
        CONF_WIND_DIRECTION_ENTITY_ID,
        CONF_WIND_GUST_ENTITY_ID,
        CONF_RAIN_ENTITY_ID,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_INPUT
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Casa"
    assert result["data"] == VALID_INPUT


async def test_reconfigure_flow_updates_existing_entry(hass: HomeAssistant) -> None:
    """Reconfigure a dwelling without replacing its config-entry identity."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    updated_input = {
        **VALID_INPUT,
        CONF_NAME: "Casa actualizada",
        CONF_OUTDOOR_TEMPERATURE_ENTITY_ID: "sensor.outdoor_temperature_2",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=updated_input
    )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Casa actualizada"
    assert entry.data == updated_input


def test_invalid_entity_domain_is_rejected() -> None:
    """Reject an entity that does not belong to its typed selector domain."""
    invalid_input = {
        **VALID_INPUT,
        CONF_WEATHER_ENTITY_ID: "sensor.weather_home",
    }

    with pytest.raises(vol.Invalid):
        CONFIG_SCHEMA(invalid_input)

    assert (
        CONFIG_SCHEMA({**VALID_INPUT, CONF_RAIN_ENTITY_ID: "sensor.rain_rate"})[
            CONF_RAIN_ENTITY_ID
        ]
        == "sensor.rain_rate"
    )


def test_blank_dwelling_name_is_rejected() -> None:
    """Reject a dwelling name containing no visible text."""
    with pytest.raises(vol.Invalid):
        CONFIG_SCHEMA({**VALID_INPUT, CONF_NAME: "   "})


def test_room_schema_rejects_wrong_sensor_domain() -> None:
    """Reject non-sensor room sources through native selectors."""
    with pytest.raises(vol.Invalid):
        ROOM_SCHEMA({**ROOM_INPUT, CONF_TEMPERATURE_ENTITY_ID: "weather.living_room"})


def test_options_schema_rejects_invalid_mode_and_numeric_bounds() -> None:
    """Use native selectors for enum and individual numeric bounds."""
    with pytest.raises(vol.Invalid):
        OPTIONS_SCHEMA({**VALID_OPTIONS, CONF_SELECTION_MODE: "legacy"})
    with pytest.raises(vol.Invalid):
        OPTIONS_SCHEMA({**VALID_OPTIONS, CONF_SUMMER_LOWER_C: 4.9})
    with pytest.raises(vol.Invalid):
        OPTIONS_SCHEMA({**VALID_OPTIONS, CONF_SOURCE_STALE_MINUTES: 0})

    for blind_step in (True, "10", 10.5):
        with pytest.raises(ValueError):
            settings_from_options(
                {**VALID_OPTIONS, CONF_BLIND_STEP_PERCENT: blind_step}
            )
    for source_age in (0, math.nan):
        with pytest.raises(ValueError):
            settings_from_options(
                {**VALID_OPTIONS, CONF_SOURCE_STALE_MINUTES: source_age}
            )


async def test_options_flow_validates_and_stores_complete_profiles(
    hass: HomeAssistant,
) -> None:
    """Reject cross-field errors and reload after storing valid options."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert set(result["data_schema"].schema) == set(VALID_OPTIONS)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            **VALID_OPTIONS,
            CONF_SUMMER_LOWER_C: 26,
            CONF_SUMMER_UPPER_C: 25,
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_options"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**VALID_OPTIONS, CONF_BLIND_STEP_PERCENT: 30},
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_options"}

    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as async_reload:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=VALID_OPTIONS
        )
        await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert entry.options == VALID_OPTIONS
    async_reload.assert_awaited_once_with(entry.entry_id)


async def test_room_subentry_create_and_reconfigure(hass: HomeAssistant) -> None:
    """Create and reconfigure a room without changing its stable ID."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    room = await _create_room(hass, entry)
    room_id = room.subentry_id

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ROOM),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": room_id},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure"

    updated = {**ROOM_INPUT, CONF_NAME: "Salón principal"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=updated
    )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[room_id].title == "Salón principal"
    assert entry.subentries[room_id].data == updated


async def test_opening_subentry_requires_an_existing_room(
    hass: HomeAssistant,
) -> None:
    """Do not offer an opening with no stable room target."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_OPENING),
        context={"source": SOURCE_USER},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "no_rooms"


async def test_opening_subentry_create_validate_and_reconfigure(
    hass: HomeAssistant,
) -> None:
    """Validate geometry and preserve the room link while reconfiguring."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    room = await _create_room(hass, entry)
    opening_input = {
        CONF_NAME: "Ventana sur",
        CONF_ROOM_SUBENTRY_ID: room.subentry_id,
        CONF_FACADE_AZIMUTH_DEG: 180,
        CONF_WIDTH_M: 1.6,
        CONF_HEIGHT_M: 1.2,
        CONF_OVERHANG_DEPTH_M: 0.5,
        CONF_OVERHANG_GAP_M: 0.2,
        CONF_SUPPORTS_TILT: True,
        CONF_RAIN_PROTECTED: False,
        CONF_CONTACT_ENTITY_ID: "binary_sensor.south_window",
        CONF_COVER_ENTITY_ID: "cover.south_blind",
    }

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_OPENING), context={"source": SOURCE_USER}
    )
    assert result["type"] == "form"
    schema = result["data_schema"]
    with pytest.raises(vol.Invalid):
        schema({**opening_input, CONF_ROOM_SUBENTRY_ID: "missing"})
    with pytest.raises(vol.Invalid):
        schema({**opening_input, CONF_WIDTH_M: 0})

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=opening_input
    )
    assert result["type"] == "create_entry"
    opening = next(
        item
        for item in entry.subentries.values()
        if item.subentry_type == SUBENTRY_TYPE_OPENING
    )
    opening_id = opening.subentry_id

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_OPENING),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": opening_id},
    )
    assert result["type"] == "form"
    updated = {**opening_input, CONF_NAME: "Ventana sur principal"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=updated
    )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[opening_id].title == "Ventana sur principal"
    assert entry.subentries[opening_id].data == updated
