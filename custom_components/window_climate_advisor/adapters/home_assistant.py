"""Translate Home Assistant entity state into typed advisor snapshots."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from homeassistant.components.cover import ATTR_CURRENT_POSITION
from homeassistant.components.sun.const import (
    DOMAIN as SUN_DOMAIN,
)
from homeassistant.components.sun.const import (
    STATE_ATTR_AZIMUTH,
    STATE_ATTR_ELEVATION,
)
from homeassistant.components.weather.const import (
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED_UNIT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfIrradiance,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.util.unit_conversion import SpeedConverter, TemperatureConverter

from ..application.evaluator import InputIssue, OpeningSnapshot
from ..application.state import AdvisorState
from ..const import (
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HEIGHT_M,
    CONF_OUTDOOR_TEMPERATURE_ENTITY_ID,
    CONF_OVERHANG_DEPTH_M,
    CONF_OVERHANG_GAP_M,
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
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_ROOM,
)
from ..domain.geometry import facade_irradiance_w_m2
from ..domain.models import (
    BlindOpening,
    OpeningDimensions,
    ThermalConditions,
    WindowState,
)
from ..domain.optimizer import CandidateAction
from ..domain.policy import (
    DEFAULT_SAFETY_SETTINGS,
    SafetyGeometry,
    SafetySnapshot,
)

_UNUSABLE_STATES = {STATE_UNKNOWN, STATE_UNAVAILABLE}
_SUN_ENTITY_ID = f"{SUN_DOMAIN}.{SUN_DOMAIN}"


@dataclass(frozen=True, slots=True)
class ObservedFloat:
    """One normalized numeric observation and explicit quality."""

    value: float | None
    issue: InputIssue | None


@dataclass(frozen=True, slots=True)
class SnapshotBuild:
    """Typed openings plus non-sensitive adapter diagnostics."""

    openings: tuple[OpeningSnapshot, ...]
    indoor_temperatures_c: tuple[float, ...]
    source_quality: dict[str, str]


def _quality(observed: ObservedFloat) -> str:
    return observed.issue.value if observed.issue is not None else "ready"


def _state_issue(
    state: State | None,
    now: datetime,
    max_age: timedelta | None,
) -> InputIssue | None:
    if state is None or state.state in _UNUSABLE_STATES:
        return InputIssue.MISSING_INPUT
    if max_age is None:
        return None
    if state.last_reported > now:
        return InputIssue.MISSING_INPUT
    if now - state.last_reported > max_age:
        return InputIssue.STALE_INPUT
    return None


def _numeric_state(
    hass: HomeAssistant,
    entity_id: str,
    now: datetime,
    max_age: timedelta | None,
    normalize: Callable[[float, State], float],
) -> ObservedFloat:
    state = hass.states.get(entity_id)
    if (issue := _state_issue(state, now, max_age)) is not None:
        return ObservedFloat(None, issue)
    assert state is not None
    try:
        return ObservedFloat(normalize(float(state.state), state), None)
    except TypeError, ValueError:
        return ObservedFloat(None, InputIssue.MISSING_INPUT)


def _temperature(value: float, state: State) -> float:
    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    if not isinstance(unit, str):
        raise ValueError("temperature unit is missing")
    return TemperatureConverter.convert(value, unit, UnitOfTemperature.CELSIUS)


def _speed(value: float, state: State) -> float:
    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    if not isinstance(unit, str):
        raise ValueError("speed unit is missing")
    return SpeedConverter.convert(value, unit, UnitOfSpeed.KILOMETERS_PER_HOUR)


def _irradiance(value: float, state: State) -> float:
    if state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) != (
        UnitOfIrradiance.WATTS_PER_SQUARE_METER
    ):
        raise ValueError("irradiance must use W/m²")
    if value < 0:
        raise ValueError("irradiance must not be negative")
    return value


def _direction(value: float, state: State) -> float:
    if not 0 <= value < 360:
        raise ValueError("wind direction must be within [0, 360)")
    return value


def _sun_position(
    hass: HomeAssistant,
    now: datetime,
    max_age: timedelta | None,
) -> tuple[ObservedFloat, ObservedFloat]:
    """Return validated current solar azimuth and elevation."""
    state = hass.states.get(_SUN_ENTITY_ID)
    if (issue := _state_issue(state, now, max_age)) is not None:
        missing = ObservedFloat(None, issue)
        return missing, missing
    assert state is not None
    azimuth = state.attributes.get(STATE_ATTR_AZIMUTH)
    elevation = state.attributes.get(STATE_ATTR_ELEVATION)
    if (
        isinstance(azimuth, bool)
        or not isinstance(azimuth, int | float)
        or not 0 <= azimuth < 360
        or isinstance(elevation, bool)
        or not isinstance(elevation, int | float)
        or not -90 <= elevation <= 90
    ):
        missing = ObservedFloat(None, InputIssue.MISSING_INPUT)
        return missing, missing
    return ObservedFloat(float(azimuth), None), ObservedFloat(float(elevation), None)


def _weather_gust(
    hass: HomeAssistant,
    weather_entity_id: str,
    now: datetime,
    max_age: timedelta | None,
) -> ObservedFloat:
    state = hass.states.get(weather_entity_id)
    if (issue := _state_issue(state, now, max_age)) is not None:
        return ObservedFloat(None, issue)
    assert state is not None
    value = state.attributes.get(ATTR_WEATHER_WIND_GUST_SPEED)
    unit = state.attributes.get(ATTR_WEATHER_WIND_SPEED_UNIT)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return ObservedFloat(None, InputIssue.MISSING_INPUT)
    if not isinstance(unit, str):
        return ObservedFloat(None, InputIssue.MISSING_INPUT)
    try:
        return ObservedFloat(
            SpeedConverter.convert(float(value), unit, UnitOfSpeed.KILOMETERS_PER_HOUR),
            None,
        )
    except ValueError:
        return ObservedFloat(None, InputIssue.MISSING_INPUT)


def _rain(
    hass: HomeAssistant,
    entity_id: str,
    now: datetime,
    max_age: timedelta | None,
) -> ObservedFloat:
    state = hass.states.get(entity_id)
    if entity_id.startswith("binary_sensor."):
        if (issue := _state_issue(state, now, None)) is not None:
            return ObservedFloat(None, issue)
        assert state is not None
        if state.state == STATE_OFF:
            return ObservedFloat(0, None)
        if state.state == STATE_ON:
            return ObservedFloat(
                DEFAULT_SAFETY_SETTINGS.light_rain_max_mm_h + 0.1,
                None,
            )
        return ObservedFloat(None, InputIssue.MISSING_INPUT)

    def normalize(value: float, numeric_state: State) -> float:
        if numeric_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) != (
            UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR
        ):
            raise ValueError("rain rate must use mm/h")
        if value < 0:
            raise ValueError("rain rate must not be negative")
        return value

    return _numeric_state(hass, entity_id, now, max_age, normalize)


def _merge_issue(*observations: ObservedFloat) -> InputIssue | None:
    if any(item.issue is InputIssue.STALE_INPUT for item in observations):
        return InputIssue.STALE_INPUT
    if any(item.value is None for item in observations):
        return InputIssue.MISSING_INPUT
    return None


def _contact_window(
    hass: HomeAssistant,
    entity_id: str | None,
    previous: WindowState,
) -> tuple[WindowState, InputIssue | None]:
    if entity_id is None:
        return previous, None
    state = hass.states.get(entity_id)
    if state is None or state.state in _UNUSABLE_STATES:
        return WindowState.CLOSED, InputIssue.MISSING_INPUT
    if state.state == STATE_ON:
        return WindowState.OPEN, None
    if state.state == STATE_OFF:
        return WindowState.CLOSED, None
    return WindowState.CLOSED, InputIssue.MISSING_INPUT


def _cover_blind(
    hass: HomeAssistant,
    entity_id: str | None,
) -> tuple[BlindOpening, InputIssue | None]:
    if entity_id is None:
        return BlindOpening(100), None
    state = hass.states.get(entity_id)
    if state is None or state.state in _UNUSABLE_STATES:
        return BlindOpening(100), InputIssue.MISSING_INPUT
    value: Any = state.attributes.get(ATTR_CURRENT_POSITION)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return BlindOpening(100), InputIssue.MISSING_INPUT
    try:
        return BlindOpening(float(value)), None
    except ValueError:
        return BlindOpening(100), InputIssue.MISSING_INPUT


def configured_entity_ids(entry: ConfigEntry) -> set[str]:
    """Return every entity whose state can affect this entry."""
    entity_ids = {
        value
        for key, value in entry.data.items()
        if key.endswith("_entity_id") and isinstance(value, str)
    }
    for subentry in entry.subentries.values():
        entity_ids.update(
            value
            for key, value in subentry.data.items()
            if key.endswith("_entity_id") and isinstance(value, str)
        )
    entity_ids.add(_SUN_ENTITY_ID)
    return entity_ids


def build_snapshot(
    hass: HomeAssistant,
    entry: ConfigEntry,
    previous_state: AdvisorState,
    now: datetime,
    max_age: timedelta | None,
) -> SnapshotBuild:
    """Build one coherent typed dwelling snapshot without retaining HA state."""
    outdoor = _numeric_state(
        hass,
        entry.data[CONF_OUTDOOR_TEMPERATURE_ENTITY_ID],
        now,
        max_age,
        _temperature,
    )
    irradiance = _numeric_state(
        hass,
        entry.data[CONF_SOLAR_RADIATION_ENTITY_ID],
        now,
        max_age,
        _irradiance,
    )
    sun_azimuth, sun_elevation = _sun_position(hass, now, max_age)
    sun_issue = _merge_issue(sun_azimuth, sun_elevation)
    wind = _numeric_state(
        hass,
        entry.data[CONF_WIND_SPEED_ENTITY_ID],
        now,
        max_age,
        _speed,
    )
    direction = _numeric_state(
        hass,
        entry.data[CONF_WIND_DIRECTION_ENTITY_ID],
        now,
        max_age,
        _direction,
    )
    gust_entity_id = entry.data.get(CONF_WIND_GUST_ENTITY_ID)
    gust = (
        _numeric_state(hass, gust_entity_id, now, max_age, _speed)
        if isinstance(gust_entity_id, str)
        else _weather_gust(
            hass,
            entry.data[CONF_WEATHER_ENTITY_ID],
            now,
            max_age,
        )
    )
    rain = _rain(hass, entry.data[CONF_RAIN_ENTITY_ID], now, max_age)

    quality = {
        "outdoor_temperature": _quality(outdoor),
        "solar_radiation": _quality(irradiance),
        "sun_position": sun_issue.value if sun_issue is not None else "ready",
        "wind_speed": _quality(wind),
        "wind_direction": _quality(direction),
        "wind_gust": _quality(gust),
        "rain": _quality(rain),
    }
    safety = SafetySnapshot(
        rain.value,
        gust.value,
        direction.value,
        stale=any(
            item.issue is InputIssue.STALE_INPUT for item in (rain, gust, direction)
        ),
    )
    rooms = {
        subentry_id: subentry
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    }
    room_temperatures: dict[str, ObservedFloat] = {}
    for room_id, room in rooms.items():
        room_temperatures[room_id] = _numeric_state(
            hass,
            room.data[CONF_TEMPERATURE_ENTITY_ID],
            now,
            max_age,
            _temperature,
        )
        quality[f"room:{room_id}:temperature"] = _quality(room_temperatures[room_id])

    openings: list[OpeningSnapshot] = []
    for opening_id, opening in entry.subentries.items():
        if opening.subentry_type != SUBENTRY_TYPE_OPENING:
            continue
        data = opening.data
        room_id = data[CONF_ROOM_SUBENTRY_ID]
        indoor = room_temperatures.get(room_id)
        previous = previous_state.openings.get(opening_id)
        previous_window = (
            previous.window if previous is not None else WindowState.CLOSED
        )
        contact_id = data.get(CONF_CONTACT_ENTITY_ID)
        cover_id = data.get(CONF_COVER_ENTITY_ID)
        window, contact_issue = _contact_window(
            hass,
            contact_id if isinstance(contact_id, str) else None,
            previous_window,
        )
        blind, cover_issue = _cover_blind(
            hass,
            cover_id if isinstance(cover_id, str) else None,
        )
        if isinstance(contact_id, str):
            quality[f"opening:{opening_id}:contact"] = (
                contact_issue.value if contact_issue is not None else "ready"
            )
        if isinstance(cover_id, str):
            quality[f"opening:{opening_id}:cover"] = (
                cover_issue.value if cover_issue is not None else "ready"
            )

        input_issue = (
            InputIssue.CONFIGURATION_REQUIRED
            if indoor is None
            else _merge_issue(
                indoor,
                outdoor,
                irradiance,
                sun_azimuth,
                sun_elevation,
                wind,
                gust,
            )
        )
        if contact_issue is not None or cover_issue is not None:
            input_issue = InputIssue.MISSING_INPUT
        current_conditions = None
        if input_issue is None:
            assert indoor is not None
            current_conditions = ThermalConditions(
                cast(float, indoor.value),
                cast(float, outdoor.value),
                facade_irradiance_w_m2(
                    cast(float, irradiance.value),
                    cast(float, sun_azimuth.value),
                    cast(float, sun_elevation.value),
                    float(data[CONF_FACADE_AZIMUTH_DEG]),
                    float(data[CONF_HEIGHT_M]),
                    float(data[CONF_OVERHANG_DEPTH_M]),
                    float(data[CONF_OVERHANG_GAP_M]),
                ),
                cast(float, wind.value),
                cast(float, gust.value),
            )
        openings.append(
            OpeningSnapshot(
                opening_id,
                OpeningDimensions(
                    float(data[CONF_WIDTH_M]),
                    float(data[CONF_HEIGHT_M]),
                ),
                SafetyGeometry(
                    float(data[CONF_FACADE_AZIMUTH_DEG]),
                    float(data[CONF_OVERHANG_DEPTH_M]),
                    float(data[CONF_OVERHANG_GAP_M]),
                    bool(data[CONF_RAIN_PROTECTED]),
                ),
                bool(data[CONF_SUPPORTS_TILT]),
                isinstance(cover_id, str),
                CandidateAction(window, blind),
                current_conditions,
                None,
                safety,
                input_issue,
            )
        )

    indoor_temperatures = tuple(
        observation.value
        for observation in room_temperatures.values()
        if observation.issue is None and observation.value is not None
    )
    return SnapshotBuild(tuple(openings), indoor_temperatures, quality)
