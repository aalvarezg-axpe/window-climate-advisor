"""Translate Home Assistant daily weather forecasts."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from homeassistant.components.weather import ATTR_FORECAST_TEMP, SERVICE_GET_FORECASTS
from homeassistant.const import ATTR_ENTITY_ID, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.unit_conversion import TemperatureConverter


@dataclass(frozen=True, slots=True)
class DailyForecast:
    """Available daily maximum temperatures in domain units."""

    maximum_temperatures_c: tuple[float, ...]
    available: bool


async def async_daily_forecast(
    hass: HomeAssistant,
    weather_entity_id: str,
) -> DailyForecast:
    """Return validated daily maxima or explicit unavailability."""
    if not hass.services.has_service("weather", SERVICE_GET_FORECASTS):
        return DailyForecast((), False)
    try:
        response = await hass.services.async_call(
            "weather",
            SERVICE_GET_FORECASTS,
            {ATTR_ENTITY_ID: weather_entity_id, "type": "daily"},
            blocking=True,
            return_response=True,
        )
    except HomeAssistantError:
        return DailyForecast((), False)
    if not isinstance(response, Mapping):
        return DailyForecast((), False)
    payload: Any = response.get(weather_entity_id, response)
    if not isinstance(payload, Mapping):
        return DailyForecast((), False)
    values = payload.get("forecast")
    if not isinstance(values, Sequence) or isinstance(values, str | bytes):
        return DailyForecast((), False)

    maxima: list[float] = []
    from_unit = hass.config.units.temperature_unit
    for item in values:
        if not isinstance(item, Mapping):
            return DailyForecast((), False)
        value = item.get(ATTR_FORECAST_TEMP)
        if isinstance(value, bool) or not isinstance(value, int | float):
            return DailyForecast((), False)
        try:
            maxima.append(
                TemperatureConverter.convert(
                    float(value), from_unit, UnitOfTemperature.CELSIUS
                )
            )
        except ValueError:
            return DailyForecast((), False)
    return DailyForecast(tuple(maxima), bool(maxima))
