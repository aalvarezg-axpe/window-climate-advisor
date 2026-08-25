"""Config flow for the Window Climate Advisor integration."""

from collections.abc import Mapping
from math import isfinite
from typing import Any, override

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BLIND_DEADBAND_PERCENT,
    CONF_BLIND_FULL_TRAVEL_PENALTY_W,
    CONF_BLIND_STEP_PERCENT,
    CONF_CO2_ENTITY_ID,
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_FACADE_AZIMUTH_DEG,
    CONF_HAS_BLIND,
    CONF_HEIGHT_M,
    CONF_HUMIDITY_ENTITY_ID,
    CONF_MINIMUM_BENEFIT_W,
    CONF_MISSING_FORECAST_CHANGE_PENALTY_W,
    CONF_NAME,
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
from .const import (
    VERSION as CONFIG_VERSION,
)
from .domain.optimizer import OptimizerSettings
from .domain.profiles import ComfortProfile, ComfortProfiles, SelectionMode
from .domain.state_machine import StabilitySettings


def _entity_selector(domain: str) -> selector.EntitySelector:
    """Return an entity selector constrained to one Home Assistant domain."""
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain))


def has_duplicate_entity_links(*mappings: Mapping[str, Any]) -> bool:
    """Reject one Home Assistant entity assigned to multiple semantic inputs."""
    entity_ids = [
        value
        for data in mappings
        for key, value in data.items()
        if key.endswith("_entity_id") and isinstance(value, str)
    ]
    return len(entity_ids) != len(set(entity_ids))


def _entry_mappings(
    entry: ConfigEntry,
    *,
    exclude_subentry_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Return every persisted structural mapping except one replacement target."""
    return (
        entry.data,
        *(
            subentry.data
            for subentry_id, subentry in entry.subentries.items()
            if subentry_id != exclude_subentry_id
        ),
    )


NAME_SELECTOR = vol.All(
    selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
    ),
    vol.Strip,
    vol.Length(min=1),
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
        vol.Required(CONF_RAIN_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["binary_sensor", "sensor"])
        ),
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
    minimum: float, maximum: float, *, unit: str, step: float = 0.01
) -> selector.NumberSelector:
    """Return a bounded numeric selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


PROFILE_TEMPERATURE_SELECTOR = _number_selector(5, 35, unit="°C", step=0.1)
PROFILE_HYSTERESIS_SELECTOR = _number_selector(0.1, 5, unit="°C", step=0.1)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_SELECTION_MODE, default=SelectionMode.AUTO.value
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[mode.value for mode in SelectionMode],
                translation_key="selection_mode",
            )
        ),
        vol.Required(CONF_SUMMER_LOWER_C): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(CONF_SUMMER_UPPER_C): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(
            CONF_SUMMER_PRECONDITIONING_TARGET_C
        ): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(CONF_SUMMER_HYSTERESIS_C): PROFILE_HYSTERESIS_SELECTOR,
        vol.Required(CONF_SHOULDER_LOWER_C): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(CONF_SHOULDER_UPPER_C): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(
            CONF_SHOULDER_PRECONDITIONING_TARGET_C
        ): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(CONF_SHOULDER_HYSTERESIS_C): PROFILE_HYSTERESIS_SELECTOR,
        vol.Required(CONF_WINTER_LOWER_C): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(CONF_WINTER_UPPER_C): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(
            CONF_WINTER_PRECONDITIONING_TARGET_C
        ): PROFILE_TEMPERATURE_SELECTOR,
        vol.Required(CONF_WINTER_HYSTERESIS_C): PROFILE_HYSTERESIS_SELECTOR,
        vol.Required(CONF_BLIND_STEP_PERCENT): _number_selector(
            1, 100, unit="%", step=1
        ),
        vol.Required(CONF_WINDOW_MOVEMENT_PENALTY_W): _number_selector(
            0, 10_000, unit="W", step=1
        ),
        vol.Required(CONF_BLIND_FULL_TRAVEL_PENALTY_W): _number_selector(
            0, 10_000, unit="W", step=1
        ),
        vol.Required(CONF_MISSING_FORECAST_CHANGE_PENALTY_W): _number_selector(
            0, 10_000, unit="W", step=1
        ),
        vol.Required(CONF_MINIMUM_BENEFIT_W): _number_selector(
            0, 10_000, unit="W", step=1
        ),
        vol.Required(CONF_BLIND_DEADBAND_PERCENT): _number_selector(
            0, 100, unit="%", step=1
        ),
        vol.Required(CONF_SOURCE_STALE_MINUTES): _number_selector(
            1, 1_440, unit="min", step=1
        ),
    }
)


def profiles_from_options(user_input: dict[str, Any]) -> ComfortProfiles:
    """Validate cross-field profile relationships through the domain model."""

    def profile(prefix: str) -> ComfortProfile:
        return ComfortProfile(
            lower_c=float(user_input[f"{prefix}_lower_c"]),
            upper_c=float(user_input[f"{prefix}_upper_c"]),
            preconditioning_target_c=float(
                user_input[f"{prefix}_preconditioning_target_c"]
            ),
            hysteresis_c=float(user_input[f"{prefix}_hysteresis_c"]),
        )

    return ComfortProfiles(
        summer=profile("summer"),
        shoulder=profile("shoulder"),
        winter=profile("winter"),
    )


def settings_from_options(
    user_input: dict[str, Any],
) -> tuple[OptimizerSettings, StabilitySettings, float]:
    """Validate runtime tuning through the existing typed settings."""
    blind_step = user_input[CONF_BLIND_STEP_PERCENT]
    if (
        isinstance(blind_step, bool)
        or not isinstance(blind_step, int | float)
        or not float(blind_step).is_integer()
    ):
        raise ValueError("blind step must be an integer")
    optimizer = OptimizerSettings(
        int(blind_step),
        float(user_input[CONF_WINDOW_MOVEMENT_PENALTY_W]),
        float(user_input[CONF_BLIND_FULL_TRAVEL_PENALTY_W]),
        float(user_input[CONF_MISSING_FORECAST_CHANGE_PENALTY_W]),
    )
    stability = StabilitySettings(
        float(user_input[CONF_MINIMUM_BENEFIT_W]),
        float(user_input[CONF_BLIND_DEADBAND_PERCENT]),
    )
    source_stale_minutes = float(user_input[CONF_SOURCE_STALE_MINUTES])
    if not isfinite(source_stale_minutes) or source_stale_minutes <= 0:
        raise ValueError("source stale minutes must be finite and positive")
    return optimizer, stability, source_stale_minutes


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
            vol.Required(CONF_FACADE_AZIMUTH_DEG): _number_selector(0, 359, unit="°"),
            vol.Required(CONF_WIDTH_M): _number_selector(0.01, 20, unit="m"),
            vol.Required(CONF_HEIGHT_M): _number_selector(0.01, 20, unit="m"),
            vol.Required(CONF_OVERHANG_DEPTH_M): _number_selector(0, 20, unit="m"),
            vol.Required(CONF_OVERHANG_GAP_M): _number_selector(0, 20, unit="m"),
            vol.Required(CONF_SUPPORTS_TILT): selector.BooleanSelector(),
            vol.Required(CONF_RAIN_PROTECTED): selector.BooleanSelector(),
            vol.Required(CONF_HAS_BLIND): selector.BooleanSelector(),
            vol.Optional(CONF_CONTACT_ENTITY_ID): _entity_selector("binary_sensor"),
            vol.Optional(CONF_COVER_ENTITY_ID): _entity_selector("cover"),
        }
    )


class WindowClimateAdvisorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle configuration of a dwelling's shared climate sources."""

    VERSION = CONFIG_VERSION

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the seasonal comfort options flow."""
        return WindowClimateAdvisorOptionsFlow()

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
            if not has_duplicate_entity_links(user_input):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            errors = {"base": "duplicate_entity_link"}
        else:
            errors = None

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CONFIG_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the shared climate sources for an existing dwelling."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            if not has_duplicate_entity_links(
                user_input,
                *(subentry.data for subentry in entry.subentries.values()),
            ):
                return self.async_update_reload_and_abort(
                    entry, title=user_input[CONF_NAME], data=user_input
                )
            errors = {"base": "duplicate_entity_link"}
        else:
            errors = None

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONFIG_SCHEMA, user_input or dict(entry.data)
            ),
            errors=errors,
        )


class WindowClimateAdvisorOptionsFlow(OptionsFlow):
    """Configure seasonal comfort profiles without Home Assistant helpers."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Store one complete, cross-field validated profile set."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                profiles_from_options(user_input)
                settings_from_options(user_input)
            except ValueError:
                errors["base"] = "invalid_options"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, dict(self.config_entry.options)
            ),
            errors=errors,
        )


class RoomSubentryFlow(ConfigSubentryFlow):
    """Create and reconfigure room subentries."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Create a room."""
        if user_input is not None:
            if not has_duplicate_entity_links(
                *_entry_mappings(self._get_entry()), user_input
            ):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            errors = {"base": "duplicate_entity_link"}
        else:
            errors = None
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(ROOM_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a room."""
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            entry = self._get_entry()
            if not has_duplicate_entity_links(
                *_entry_mappings(
                    entry,
                    exclude_subentry_id=subentry.subentry_id,
                ),
                user_input,
            ):
                return self.async_update_and_abort(
                    entry,
                    subentry,
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            errors = {"base": "duplicate_entity_link"}
        else:
            errors = None
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                ROOM_SCHEMA, user_input or dict(subentry.data)
            ),
            errors=errors,
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
            if CONF_COVER_ENTITY_ID in user_input and not user_input[CONF_HAS_BLIND]:
                errors = {"base": "cover_without_blind"}
            elif not has_duplicate_entity_links(*_entry_mappings(entry), user_input):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                errors = {"base": "duplicate_entity_link"}
        else:
            errors = None
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure an opening."""
        subentry = self._get_reconfigure_subentry()
        entry = self._get_entry()
        schema = _opening_schema(entry)
        if user_input is not None:
            if CONF_COVER_ENTITY_ID in user_input and not user_input[CONF_HAS_BLIND]:
                errors = {"base": "cover_without_blind"}
            elif not has_duplicate_entity_links(
                *_entry_mappings(
                    entry,
                    exclude_subentry_id=subentry.subentry_id,
                ),
                user_input,
            ):
                return self.async_update_and_abort(
                    entry,
                    subentry,
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            else:
                errors = {"base": "duplicate_entity_link"}
        else:
            errors = None
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or dict(subentry.data)
            ),
            errors=errors,
        )
