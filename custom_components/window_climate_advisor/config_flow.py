"""Config flow for the Window Climate Advisor integration."""

from typing import Any, override

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CO2_ENTITY_ID,
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_FACADE_AZIMUTH,
    CONF_HEIGHT,
    CONF_HUMIDITY_ENTITY_ID,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY_ID,
    CONF_OVERHANG_DEPTH,
    CONF_OVERHANG_GAP,
    CONF_RAIN_ENTITY_ID,
    CONF_RAIN_PROTECTED,
    CONF_ROOM_SUBENTRY_ID,
    CONF_SOLAR_RADIATION_ENTITY_ID,
    CONF_SUPPORTS_TILT,
    CONF_TEMPERATURE_ENTITY_ID,
    CONF_WEATHER_ENTITY_ID,
    CONF_WIDTH,
    CONF_WIND_DIRECTION_ENTITY_ID,
    CONF_WIND_GUST_ENTITY_ID,
    CONF_WIND_SPEED_ENTITY_ID,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_ROOM,
)
from .const import (
    VERSION as CONFIG_VERSION,
)


def _entity_selector(domain: str) -> selector.EntitySelector:
    """Return an entity selector constrained to one Home Assistant domain."""
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain))


def _non_empty_name(value: str) -> str:
    """Reject names that contain no visible text."""
    name = value.strip()
    if not name:
        raise vol.Invalid("Name must not be empty")
    return name


NAME_SELECTOR = vol.All(
    selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
    ),
    _non_empty_name,
)


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): NAME_SELECTOR,
        vol.Required(CONF_OUTDOOR_TEMPERATURE_ENTITY_ID): _entity_selector("sensor"),
        vol.Required(CONF_WEATHER_ENTITY_ID): _entity_selector("weather"),
        vol.Required(CONF_SOLAR_RADIATION_ENTITY_ID): _entity_selector("sensor"),
        vol.Required(CONF_WIND_SPEED_ENTITY_ID): _entity_selector("sensor"),
        vol.Required(CONF_WIND_DIRECTION_ENTITY_ID): _entity_selector("sensor"),
        vol.Optional(CONF_WIND_GUST_ENTITY_ID): _entity_selector("sensor"),
        vol.Required(CONF_RAIN_ENTITY_ID): _entity_selector("binary_sensor"),
    }
)

ROOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): NAME_SELECTOR,
        vol.Required(CONF_TEMPERATURE_ENTITY_ID): _entity_selector("sensor"),
        vol.Optional(CONF_HUMIDITY_ENTITY_ID): _entity_selector("sensor"),
        vol.Optional(CONF_CO2_ENTITY_ID): _entity_selector("sensor"),
    }
)


def _number_selector(
    minimum: float, maximum: float, *, unit: str
) -> selector.NumberSelector:
    """Return a bounded numeric selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=0.01,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


def _opening_schema(entry: ConfigEntry) -> vol.Schema:
    """Build the opening schema from the entry's current room subentries."""
    rooms = [
        selector.SelectOptionDict(value=subentry_id, label=subentry.title)
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    ]
    return vol.Schema(
        {
            vol.Required(CONF_NAME): NAME_SELECTOR,
            vol.Required(CONF_ROOM_SUBENTRY_ID): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=rooms,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    sort=True,
                )
            ),
            vol.Required(CONF_FACADE_AZIMUTH): _number_selector(0, 359, unit="°"),
            vol.Required(CONF_WIDTH): _number_selector(0.01, 20, unit="m"),
            vol.Required(CONF_HEIGHT): _number_selector(0.01, 20, unit="m"),
            vol.Required(CONF_OVERHANG_DEPTH): _number_selector(0, 20, unit="m"),
            vol.Required(CONF_OVERHANG_GAP): _number_selector(0, 20, unit="m"),
            vol.Required(CONF_SUPPORTS_TILT): selector.BooleanSelector(),
            vol.Required(CONF_RAIN_PROTECTED): selector.BooleanSelector(),
            vol.Optional(CONF_CONTACT_ENTITY_ID): _entity_selector("binary_sensor"),
            vol.Optional(CONF_COVER_ENTITY_ID): _entity_selector("cover"),
        }
    )


class WindowClimateAdvisorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle configuration of a dwelling's shared climate sources."""

    VERSION = CONFIG_VERSION

    @classmethod
    @callback
    @override
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return the room and opening subentry flow handlers."""
        return {
            SUBENTRY_TYPE_ROOM: RoomSubentryFlow,
            SUBENTRY_TYPE_OPENING: OpeningSubentryFlow,
        }

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a user-started configuration flow."""
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the shared climate sources for an existing dwelling."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry, title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONFIG_SCHEMA, dict(entry.data)
            ),
        )


class RoomSubentryFlow(ConfigSubentryFlow):
    """Create and reconfigure room subentries."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Create a room."""
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=ROOM_SCHEMA)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a room."""
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            return self.async_update_and_abort(
                self._get_entry(),
                subentry,
                title=user_input[CONF_NAME],
                data=user_input,
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                ROOM_SCHEMA, dict(subentry.data)
            ),
        )


class OpeningSubentryFlow(ConfigSubentryFlow):
    """Create and reconfigure opening subentries."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Create an opening linked to a room."""
        entry = self._get_entry()
        if not any(
            subentry.subentry_type == SUBENTRY_TYPE_ROOM
            for subentry in entry.subentries.values()
        ):
            return self.async_abort(reason="no_rooms")
        schema = _opening_schema(entry)
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure an opening."""
        subentry = self._get_reconfigure_subentry()
        schema = _opening_schema(self._get_entry())
        if user_input is not None:
            return self.async_update_and_abort(
                self._get_entry(),
                subentry,
                title=user_input[CONF_NAME],
                data=user_input,
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema, dict(subentry.data)
            ),
        )
