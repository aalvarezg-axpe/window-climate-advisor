"""Constants for the Window Climate Advisor integration."""

from typing import Final

DOMAIN: Final = "window_climate_advisor"
VERSION: Final = 1

SUBENTRY_TYPE_ROOM: Final = "room"
SUBENTRY_TYPE_OPENING: Final = "opening"

CONF_NAME: Final = "name"
CONF_OUTDOOR_TEMPERATURE_ENTITY_ID: Final = "outdoor_temperature_entity_id"
CONF_WEATHER_ENTITY_ID: Final = "weather_entity_id"
CONF_SOLAR_RADIATION_ENTITY_ID: Final = "solar_radiation_entity_id"
CONF_WIND_SPEED_ENTITY_ID: Final = "wind_speed_entity_id"
CONF_WIND_DIRECTION_ENTITY_ID: Final = "wind_direction_entity_id"
CONF_WIND_GUST_ENTITY_ID: Final = "wind_gust_entity_id"
CONF_RAIN_ENTITY_ID: Final = "rain_entity_id"

CONF_TEMPERATURE_ENTITY_ID: Final = "temperature_entity_id"
CONF_HUMIDITY_ENTITY_ID: Final = "humidity_entity_id"
CONF_CO2_ENTITY_ID: Final = "co2_entity_id"

CONF_ROOM_SUBENTRY_ID: Final = "room_subentry_id"
CONF_FACADE_AZIMUTH: Final = "facade_azimuth"
CONF_WIDTH: Final = "width"
CONF_HEIGHT: Final = "height"
CONF_OVERHANG_DEPTH: Final = "overhang_depth"
CONF_OVERHANG_GAP: Final = "overhang_gap"
CONF_SUPPORTS_TILT: Final = "supports_tilt"
CONF_RAIN_PROTECTED: Final = "rain_protected"
CONF_CONTACT_ENTITY_ID: Final = "contact_entity_id"
CONF_COVER_ENTITY_ID: Final = "cover_entity_id"
