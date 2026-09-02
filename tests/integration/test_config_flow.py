"""Tests for the parent dwelling configuration flow."""

import math
from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.components.notify.const import (
    DOMAIN as NOTIFY_DOMAIN,
)
from homeassistant.components.notify.const import (
    SERVICE_SEND_MESSAGE,
)
from homeassistant.components.person import ATTR_DEVICE_TRACKERS
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntry,
    ConfigSubentry,
)
from homeassistant.const import CONF_NAME, STATE_HOME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from voluptuous_serialize import convert

from custom_components.window_climate_advisor.config_flow import (
    CONFIG_SCHEMA,
    OPTIONS_SCHEMA,
    RECIPIENT_SCHEMA,
    ROOM_SCHEMA,
    day_start_time_from_options,
    settings_from_options,
)
from custom_components.window_climate_advisor.const import (
    CONF_BLIND_DEADBAND_PERCENT,
    CONF_BLIND_FULL_TRAVEL_PENALTY_W,
    CONF_BLIND_STEP_PERCENT,
    CONF_CO2_ENTITY_ID,
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_DAY_START_TIME,
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HAS_BLIND,
    CONF_HEIGHT_M,
    CONF_HUMIDITY_ENTITY_ID,
    CONF_MINIMUM_BENEFIT_W,
    CONF_MISSING_FORECAST_CHANGE_PENALTY_W,
    CONF_OCCUPANCY_PERSON_ENTITY_IDS,
    CONF_OUTDOOR_TEMPERATURE_ENTITY_ID,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
    CONF_PERSON_ENTITY_ID,
    CONF_RAIN_ENTITY_ID,
    CONF_RAIN_PROTECTED,
    CONF_ROOM_SUBENTRY_ID,
    CONF_ROOM_TEMPERATURE_STALE_MINUTES,
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
    DEFAULT_DAY_START_TIME,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
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
RECIPIENT_INPUT = {
    CONF_PERSON_ENTITY_ID: "person.resident",
}
VALID_OPTIONS = {
    CONF_SELECTION_MODE: "auto",
    CONF_DAY_START_TIME: DEFAULT_DAY_START_TIME,
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
    CONF_ROOM_TEMPERATURE_STALE_MINUTES: 60,
}


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Allow the built-in sun dependency's interval timer in flow-only tests."""
    return True


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


def _register_mobile_recipient(
    hass: HomeAssistant,
    person_entity_id: str,
    suffix: str,
    *,
    notify_state: str = "unknown",
) -> None:
    """Register the native person-to-Mobile-App registry relationship."""
    mobile_entry = MockConfigEntry(domain="mobile_app", unique_id=f"mobile-{suffix}")
    mobile_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=mobile_entry.entry_id,
        identifiers={("mobile_app", f"device-{suffix}")},
    )
    registry = er.async_get(hass)
    tracker = registry.async_get_or_create(
        "device_tracker",
        "mobile_app",
        f"tracker-{suffix}",
        suggested_object_id=suffix,
        config_entry=mobile_entry,
        device_id=device.id,
    )
    target = registry.async_get_or_create(
        NOTIFY_DOMAIN,
        "mobile_app",
        f"notify-{suffix}",
        suggested_object_id=suffix,
        config_entry=mobile_entry,
        device_id=device.id,
    )
    hass.states.async_set(
        person_entity_id,
        STATE_HOME,
        {ATTR_DEVICE_TRACKERS: [tracker.entity_id]},
    )
    hass.states.async_set(tracker.entity_id, STATE_HOME)
    hass.states.async_set(target.entity_id, notify_state)


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
        CONF_OCCUPANCY_PERSON_ENTITY_IDS,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_INPUT
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Casa"
    assert result["data"] == VALID_INPUT


async def test_flows_reject_duplicate_entity_links(hass: HomeAssistant) -> None:
    """Prevent one physical entity from filling multiple semantic inputs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            **VALID_INPUT,
            CONF_SOLAR_RADIATION_ENTITY_ID: VALID_INPUT[
                CONF_OUTDOOR_TEMPERATURE_ENTITY_ID
            ],
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "duplicate_entity_link"}

    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ROOM), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            **ROOM_INPUT,
            CONF_TEMPERATURE_ENTITY_ID: VALID_INPUT[CONF_OUTDOOR_TEMPERATURE_ENTITY_ID],
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "duplicate_entity_link"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=ROOM_INPUT
    )
    assert result["type"] == "create_entry"
    room = next(iter(entry.subentries.values()))

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            **VALID_INPUT,
            CONF_OUTDOOR_TEMPERATURE_ENTITY_ID: ROOM_INPUT[CONF_TEMPERATURE_ENTITY_ID],
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "duplicate_entity_link"}

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_OPENING), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Ventana sur",
            CONF_ROOM_SUBENTRY_ID: room.subentry_id,
            CONF_FACADE_AZIMUTH_DEG: 180,
            CONF_WIDTH_M: 1.6,
            CONF_HEIGHT_M: 1.2,
            CONF_OVERHANG_DEPTH_M: 0.5,
            CONF_OVERHANG_GAP_M: 0.2,
            CONF_SUPPORTS_TILT: True,
            CONF_RAIN_PROTECTED: False,
            CONF_HAS_BLIND: False,
            CONF_CONTACT_ENTITY_ID: VALID_INPUT[CONF_RAIN_ENTITY_ID],
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "duplicate_entity_link"}


async def test_reconfigure_flow_updates_existing_entry(hass: HomeAssistant) -> None:
    """Reconfigure a dwelling without replacing its config-entry identity."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    hass.states.async_set("person.antonio", STATE_HOME)
    hass.states.async_set("person.elisa", STATE_HOME)
    updated_input = {
        **VALID_INPUT,
        CONF_NAME: "Casa actualizada",
        CONF_OUTDOOR_TEMPERATURE_ENTITY_ID: "sensor.outdoor_temperature_2",
        CONF_OCCUPANCY_PERSON_ENTITY_IDS: ["person.antonio", "person.elisa"],
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
    await hass.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Casa actualizada"
    assert entry.data == updated_input


async def test_flow_rejects_invalid_or_duplicate_occupancy_people(
    hass: HomeAssistant,
) -> None:
    """Store only existing unique person entities for thermal occupancy."""
    hass.states.async_set("person.antonio", STATE_HOME)
    for people in (
        ["person.missing"],
        ["person.antonio", "person.antonio"],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                **VALID_INPUT,
                CONF_OCCUPANCY_PERSON_ENTITY_IDS: people,
            },
        )
        assert result["type"] == "form"
        assert result["errors"] == {"base": "invalid_occupancy_people"}


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
    with pytest.raises(vol.Invalid):
        CONFIG_SCHEMA(
            {
                **VALID_INPUT,
                CONF_OCCUPANCY_PERSON_ENTITY_IDS: ["device_tracker.antonio"],
            }
        )


def test_blank_dwelling_name_is_rejected() -> None:
    """Reject a dwelling name containing no visible text."""
    with pytest.raises(vol.Invalid):
        CONFIG_SCHEMA({**VALID_INPUT, CONF_NAME: "   "})


def test_root_schemas_serialize_for_home_assistant_frontend() -> None:
    """Keep config forms convertible by Home Assistant's HTTP flow API."""
    for schema in (CONFIG_SCHEMA, ROOM_SCHEMA, RECIPIENT_SCHEMA, OPTIONS_SCHEMA):
        assert convert(schema, custom_serializer=cv.custom_serializer)


def test_recipient_schema_rejects_wrong_entity_domains() -> None:
    """Constrain recipient selection to the native person domain."""
    with pytest.raises(vol.Invalid):
        RECIPIENT_SCHEMA(
            {**RECIPIENT_INPUT, CONF_PERSON_ENTITY_ID: "device_tracker.resident"}
        )


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
    with pytest.raises(vol.Invalid):
        OPTIONS_SCHEMA({**VALID_OPTIONS, CONF_ROOM_TEMPERATURE_STALE_MINUTES: 0})
    with pytest.raises(vol.Invalid):
        OPTIONS_SCHEMA({**VALID_OPTIONS, CONF_DAY_START_TIME: "25:00:00"})

    assert day_start_time_from_options({}).isoformat() == DEFAULT_DAY_START_TIME
    for invalid_time in (8, "08:00:00+02:00", "08:00:00.500000"):
        with pytest.raises(ValueError):
            day_start_time_from_options(
                {**VALID_OPTIONS, CONF_DAY_START_TIME: invalid_time}
            )

    for blind_step in (True, "10", 10.5):
        with pytest.raises(ValueError):
            settings_from_options(
                {**VALID_OPTIONS, CONF_BLIND_STEP_PERCENT: blind_step}
            )
    for age_key in (
        CONF_SOURCE_STALE_MINUTES,
        CONF_ROOM_TEMPERATURE_STALE_MINUTES,
    ):
        for source_age in (0, math.nan):
            with pytest.raises(ValueError):
                settings_from_options({**VALID_OPTIONS, age_key: source_age})


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


async def test_recipient_subentry_validates_native_action_and_reconfigures(
    hass: HomeAssistant,
) -> None:
    """Require a native Mobile App relationship and preserve subentry identity."""
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_INPUT, title="Casa")
    entry.add_to_hass(hass)
    _register_mobile_recipient(hass, RECIPIENT_INPUT[CONF_PERSON_ENTITY_ID], "resident")

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_RECIPIENT), context={"source": SOURCE_USER}
    )
    assert result["type"] == "form"
    assert set(result["data_schema"].schema) == set(RECIPIENT_INPUT)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=RECIPIENT_INPUT
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "notification_target_unavailable"}

    async def send_message(_: object) -> None:
        pass

    hass.services.async_register(NOTIFY_DOMAIN, SERVICE_SEND_MESSAGE, send_message)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=RECIPIENT_INPUT
    )
    assert result["type"] == "create_entry"
    recipient = next(
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_RECIPIENT
    )
    recipient_id = recipient.subentry_id
    assert recipient.data == RECIPIENT_INPUT

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_RECIPIENT), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=RECIPIENT_INPUT
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "duplicate_entity_link"}

    replacement = {CONF_PERSON_ENTITY_ID: "person.replacement"}
    hass.states.async_set(replacement[CONF_PERSON_ENTITY_ID], STATE_HOME)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_RECIPIENT),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": recipient_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=replacement
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "notification_target_unavailable"}
    _register_mobile_recipient(
        hass,
        replacement[CONF_PERSON_ENTITY_ID],
        "replacement",
        notify_state="unavailable",
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=replacement
    )
    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert recipient_id in entry.subentries
    assert entry.subentries[recipient_id].data == replacement


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
        CONF_HAS_BLIND: True,
        CONF_CONTACT_ENTITY_ID: "binary_sensor.south_window",
        CONF_COVER_ENTITY_ID: "cover.south_blind",
    }

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_OPENING), context={"source": SOURCE_USER}
    )
    assert result["type"] == "form"
    assert convert(result["data_schema"], custom_serializer=cv.custom_serializer)
    schema = result["data_schema"]
    with pytest.raises(vol.Invalid):
        schema({**opening_input, CONF_ROOM_SUBENTRY_ID: "missing"})
    with pytest.raises(vol.Invalid):
        schema({**opening_input, CONF_WIDTH_M: 0})

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={**opening_input, CONF_HAS_BLIND: False},
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "cover_without_blind"}

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
        result["flow_id"],
        user_input={**updated, CONF_HAS_BLIND: False},
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "cover_without_blind"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=updated
    )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[opening_id].title == "Ventana sur principal"
    assert entry.subentries[opening_id].data == updated
