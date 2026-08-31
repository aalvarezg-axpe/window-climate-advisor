"""Tests for Home Assistant state and forecast adapter boundaries."""

from datetime import timedelta

import pytest
from homeassistant.components.cover import ATTR_CURRENT_POSITION
from homeassistant.components.weather import SERVICE_GET_FORECASTS
from homeassistant.components.weather.const import (
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED_UNIT,
)
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    UnitOfIrradiance,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.window_climate_advisor.adapters.forecast import (
    async_daily_forecast,
)
from custom_components.window_climate_advisor.adapters.home_assistant import (
    build_snapshot,
    configured_entity_ids,
)
from custom_components.window_climate_advisor.application.evaluator import InputIssue
from custom_components.window_climate_advisor.application.state import AdvisorState
from custom_components.window_climate_advisor.const import (
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HAS_BLIND,
    CONF_HEIGHT_M,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY_ID,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
    CONF_PERSON_ENTITY_ID,
    CONF_RAIN_ENTITY_ID,
    CONF_RAIN_PROTECTED,
    CONF_ROOM_SUBENTRY_ID,
    CONF_SOLAR_RADIATION_ENTITY_ID,
    CONF_SUPPORTS_TILT,
    CONF_TEMPERATURE_ENTITY_ID,
    CONF_WEATHER_ENTITY_ID,
    CONF_WIDTH_M,
    CONF_WIND_DIRECTION_ENTITY_ID,
    CONF_WIND_GUST_ENTITY_ID,
    CONF_WIND_SPEED_ENTITY_ID,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
    SUBENTRY_TYPE_ROOM,
    VERSION,
)
from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    WindowState,
)
from custom_components.window_climate_advisor.domain.policy import (
    DEFAULT_SAFETY_SETTINGS,
)
from custom_components.window_climate_advisor.domain.state_machine import (
    OpeningStabilityState,
)


def entry(
    *,
    gust_sensor: bool = True,
    cover: bool = True,
    contact: bool = True,
    has_blind: bool = True,
    recipient: bool = False,
) -> MockConfigEntry:
    """Create a current-version dwelling with one room and opening."""
    data = {
        CONF_NAME: "Casa",
        CONF_OUTDOOR_TEMPERATURE_ENTITY_ID: "sensor.outdoor",
        CONF_WEATHER_ENTITY_ID: "weather.home",
        CONF_SOLAR_RADIATION_ENTITY_ID: "sensor.solar",
        CONF_WIND_SPEED_ENTITY_ID: "sensor.wind",
        CONF_WIND_DIRECTION_ENTITY_ID: "sensor.direction",
        CONF_RAIN_ENTITY_ID: "binary_sensor.rain",
    }
    if gust_sensor:
        data[CONF_WIND_GUST_ENTITY_ID] = "sensor.gust"
    opening_data = {
        CONF_NAME: "Ventana",
        CONF_ROOM_SUBENTRY_ID: "ROOM_ID",
        CONF_FACADE_AZIMUTH_DEG: 180,
        CONF_WIDTH_M: 1.6,
        CONF_HEIGHT_M: 1.2,
        CONF_OVERHANG_DEPTH_M: 0.5,
        CONF_OVERHANG_GAP_M: 0.2,
        CONF_SUPPORTS_TILT: True,
        CONF_RAIN_PROTECTED: True,
        CONF_HAS_BLIND: has_blind,
    }
    if contact:
        opening_data[CONF_CONTACT_ENTITY_ID] = "binary_sensor.window"
    if cover:
        opening_data[CONF_COVER_ENTITY_ID] = "cover.blind"
    subentries_data = [
        {
            "subentry_type": SUBENTRY_TYPE_ROOM,
            "title": "Salón",
            "data": {
                CONF_NAME: "Salón",
                CONF_TEMPERATURE_ENTITY_ID: "sensor.indoor",
            },
            "unique_id": "ROOM_ID",
        },
        {
            "subentry_type": SUBENTRY_TYPE_OPENING,
            "title": "Ventana",
            "data": opening_data,
            "unique_id": None,
        },
    ]
    if recipient:
        subentries_data.append(
            {
                "subentry_type": SUBENTRY_TYPE_RECIPIENT,
                "title": "person.resident",
                "data": {CONF_PERSON_ENTITY_ID: "person.resident"},
                "unique_id": None,
            },
        )
    result = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        version=VERSION,
        subentries_data=subentries_data,
    )
    room_id = next(
        subentry_id
        for subentry_id, subentry in result.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    )
    opening = next(
        subentry
        for subentry in result.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    object.__setattr__(
        opening,
        "data",
        type(opening.data)({**opening.data, CONF_ROOM_SUBENTRY_ID: room_id}),
    )
    return result


def set_ready_states(hass: HomeAssistant, *, gust_sensor: bool = True) -> None:
    """Populate every configured source in accepted units."""
    hass.states.async_set(
        "sensor.outdoor",
        "20",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "sensor.indoor",
        "27",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "sensor.solar",
        "300",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfIrradiance.WATTS_PER_SQUARE_METER},
    )
    hass.states.async_set(
        "sensor.wind",
        "5",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfSpeed.KILOMETERS_PER_HOUR},
    )
    hass.states.async_set("sensor.direction", "180")
    if gust_sensor:
        hass.states.async_set(
            "sensor.gust",
            "8",
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfSpeed.KILOMETERS_PER_HOUR},
        )
    else:
        hass.states.async_set(
            "weather.home",
            "sunny",
            {
                ATTR_WEATHER_WIND_GUST_SPEED: 8,
                ATTR_WEATHER_WIND_SPEED_UNIT: UnitOfSpeed.KILOMETERS_PER_HOUR,
            },
        )
    hass.states.async_set("binary_sensor.rain", "off")
    hass.states.async_set("binary_sensor.window", "off")
    hass.states.async_set("cover.blind", "open", {ATTR_CURRENT_POSITION: 80})
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"azimuth": 180, "elevation": 30},
    )


def test_ready_snapshot_normalizes_sources_and_current_action(
    hass: HomeAssistant,
) -> None:
    """Convert units and discard Home Assistant state objects at the boundary."""
    config_entry = entry()
    set_ready_states(hass)
    now = dt_util.utcnow()

    built = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        now,
        timedelta(minutes=15),
        timedelta(minutes=60),
    )
    opening = built.openings[0]

    assert opening.input_issue is None
    assert opening.current_conditions is not None
    assert opening.current_conditions.indoor_temperature_c == 27
    assert opening.current_conditions.facade_irradiance_w_m2 > 300
    assert opening.direct_sun_on_opening
    assert opening.current_action.window_state is WindowState.CLOSED
    assert opening.current_action.blind == BlindOpening(80)
    assert opening.safety.gust_kmh == 8
    assert opening.safety.wind_direction_deg == 180
    assert set(built.source_quality.values()) == {"ready"}
    assert built.indoor_temperatures_c == (27,)
    assert "sensor.outdoor" in configured_entity_ids(config_entry)
    assert "sun.sun" in configured_entity_ids(config_entry)


def test_snapshot_distinguishes_diffuse_load_from_direct_sun(
    hass: HomeAssistant,
) -> None:
    """Keep diffuse thermal load but do not authorize blind shading behind the sun."""
    config_entry = entry()
    set_ready_states(hass)
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"azimuth": 0, "elevation": 30},
    )

    opening = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        dt_util.utcnow(),
        timedelta(minutes=15),
        timedelta(minutes=60),
    ).openings[0]

    assert opening.current_conditions is not None
    assert opening.current_conditions.facade_irradiance_w_m2 == pytest.approx(45)
    assert not opening.direct_sun_on_opening


def test_no_cover_uses_persisted_window_and_weather_gust(
    hass: HomeAssistant,
) -> None:
    """Use only real capabilities while keeping optional sources explicit."""
    config_entry = entry(
        gust_sensor=False,
        cover=False,
        contact=False,
        has_blind=False,
    )
    set_ready_states(hass, gust_sensor=False)
    opening_id = next(
        subentry_id
        for subentry_id, subentry in config_entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    previous = AdvisorState(
        {opening_id: OpeningStabilityState(WindowState.TILT, BlindOpening(60))}
    )
    opening = build_snapshot(
        hass,
        config_entry,
        previous,
        dt_util.utcnow(),
        None,
        None,
    ).openings[0]

    assert not opening.has_blind
    assert opening.current_action.window_state is WindowState.TILT
    assert opening.current_action.blind == BlindOpening(100)
    assert opening.current_conditions is not None
    assert opening.current_conditions.gust_speed_kmh == 8


def test_manual_blind_uses_persisted_position_without_cover(
    hass: HomeAssistant,
) -> None:
    """Retain manual blind capability and memory without inventing a cover."""
    config_entry = entry(cover=False, contact=False)
    set_ready_states(hass)
    opening_id = next(
        subentry_id
        for subentry_id, subentry in config_entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    previous = AdvisorState(
        {opening_id: OpeningStabilityState(WindowState.CLOSED, BlindOpening(60))}
    )

    opening = build_snapshot(
        hass,
        config_entry,
        previous,
        dt_util.utcnow(),
        None,
        None,
    ).openings[0]

    assert opening.has_blind
    assert opening.current_action.blind == BlindOpening(60)
    assert "cover.blind" not in configured_entity_ids(config_entry)


def test_binary_rain_is_conservative_and_stale_thermal_data_is_explicit(
    hass: HomeAssistant,
) -> None:
    """Never turn wet or old observations into favourable input."""
    config_entry = entry()
    set_ready_states(hass)
    now = dt_util.utcnow()
    hass.states.async_set("binary_sensor.rain", "on")
    hass.states.async_set(
        "sensor.outdoor",
        "20",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        timestamp=(now - timedelta(minutes=20)).timestamp(),
    )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"azimuth": 180, "elevation": 30},
        timestamp=(now - timedelta(minutes=20)).timestamp(),
    )

    opening = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        now,
        timedelta(minutes=15),
        timedelta(minutes=60),
    ).openings[0]

    assert opening.safety.rain_rate_mm_h is not None
    assert opening.safety.rain_rate_mm_h > DEFAULT_SAFETY_SETTINGS.light_rain_max_mm_h
    assert opening.input_issue is InputIssue.STALE_INPUT
    assert opening.current_conditions is None


@pytest.mark.parametrize(
    ("entity_id", "state", "attributes"),
    [
        ("sensor.solar", "-1", {ATTR_UNIT_OF_MEASUREMENT: "wrong"}),
        ("sensor.wind", "bad", {ATTR_UNIT_OF_MEASUREMENT: "wrong"}),
        ("sensor.direction", "360", {}),
        ("cover.blind", "open", {ATTR_CURRENT_POSITION: True}),
        ("binary_sensor.window", "neither", {}),
        ("sun.sun", "above_horizon", {"azimuth": True, "elevation": 30}),
    ],
)
def test_malformed_required_sources_degrade_opening(
    hass: HomeAssistant,
    entity_id: str,
    state: str,
    attributes: dict[str, object],
) -> None:
    """Reject malformed values, units, ranges, contacts, and positions."""
    config_entry = entry()
    set_ready_states(hass)
    hass.states.async_set(entity_id, state, attributes)

    opening = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        dt_util.utcnow(),
        timedelta(minutes=15),
        timedelta(minutes=60),
    ).openings[0]

    if entity_id == "sensor.direction":
        assert opening.input_issue is None
        assert opening.safety.wind_direction_deg is None
    else:
        assert opening.input_issue is InputIssue.MISSING_INPUT
        assert opening.current_conditions is None


def test_room_temperature_has_independent_stale_age(
    hass: HomeAssistant,
) -> None:
    """Allow slower room reports without relaxing environmental freshness."""
    config_entry = entry()
    set_ready_states(hass)
    now = dt_util.utcnow()
    hass.states.async_set(
        "sensor.indoor",
        "27",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        timestamp=(now - timedelta(minutes=30)).timestamp(),
    )

    ready = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        now,
        timedelta(minutes=15),
        timedelta(minutes=60),
    ).openings[0]
    stale = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        now,
        timedelta(minutes=15),
        timedelta(minutes=15),
    ).openings[0]

    assert ready.input_issue is None
    assert ready.current_conditions is not None
    assert stale.input_issue is InputIssue.STALE_ROOM_TEMPERATURE
    assert stale.current_conditions is None


def test_missing_room_temperature_has_a_specific_input_issue(
    hass: HomeAssistant,
) -> None:
    """Identify the room source instead of reporting an unspecified input."""
    config_entry = entry()
    set_ready_states(hass)
    hass.states.async_set("sensor.indoor", "unavailable")

    opening = build_snapshot(
        hass,
        config_entry,
        AdvisorState(),
        dt_util.utcnow(),
        timedelta(minutes=15),
        timedelta(minutes=125),
    ).openings[0]

    assert opening.input_issue is InputIssue.MISSING_ROOM_TEMPERATURE
    assert opening.current_conditions is None


async def test_daily_forecast_handles_service_success_failure_and_shape(
    hass: HomeAssistant,
) -> None:
    """Use only complete response forecasts and convert configured units."""
    unavailable = await async_daily_forecast(hass, "weather.home")
    assert not unavailable.available

    async def valid(_: ServiceCall) -> dict[str, object]:
        return {
            "weather.home": {"forecast": [{"temperature": 25}, {"temperature": 26}]}
        }

    hass.services.async_register(
        "weather",
        SERVICE_GET_FORECASTS,
        valid,
        supports_response=SupportsResponse.ONLY,
    )
    result = await async_daily_forecast(hass, "weather.home")
    assert result.available
    assert result.maximum_temperatures_c == (25, 26)

    async def invalid(_: ServiceCall) -> dict[str, object]:
        return {"weather.home": {"forecast": [{"temperature": None}]}}

    hass.services.async_register(
        "weather",
        SERVICE_GET_FORECASTS,
        invalid,
        supports_response=SupportsResponse.ONLY,
    )
    assert not (await async_daily_forecast(hass, "weather.home")).available

    async def failed(_: ServiceCall) -> None:
        raise HomeAssistantError("forecast failed")

    hass.services.async_register(
        "weather",
        SERVICE_GET_FORECASTS,
        failed,
        supports_response=SupportsResponse.ONLY,
    )
    assert not (await async_daily_forecast(hass, "weather.home")).available
