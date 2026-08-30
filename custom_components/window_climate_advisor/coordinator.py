"""Home Assistant scheduling and restart-safe advisor state."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .adapters.forecast import async_daily_forecast
from .adapters.home_assistant import build_snapshot, configured_entity_ids
from .adapters.notifications import async_deliver_notification_candidate
from .application.evaluator import (
    AdvisorEvaluation,
    EvaluationSettings,
    EvaluationSnapshot,
    evaluate_snapshot,
)
from .application.state import AdvisorState, state_from_dict, state_to_dict
from .config_flow import (
    has_duplicate_entity_links,
    profiles_from_options,
    settings_from_options,
)
from .const import (
    CONF_SELECTION_MODE,
    CONF_WEATHER_ENTITY_ID,
    DOMAIN,
    SUBENTRY_TYPE_RECIPIENT,
)
from .domain.profiles import SelectionMode, select_season

_LOGGER = logging.getLogger(__name__)
_UPDATE_INTERVAL = timedelta(minutes=5)
_STORE_VERSION = 1


@dataclass(frozen=True, slots=True)
class CoordinatorData:
    """Published evaluation plus redacted source quality."""

    evaluation: AdvisorEvaluation
    source_quality: dict[str, str]
    profile_forecast_available: bool


class WindowClimateAdvisorCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinate one dwelling without controlling Home Assistant entities."""

    config_entry: ConfigEntry[WindowClimateAdvisorCoordinator]

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry[WindowClimateAdvisorCoordinator],
    ) -> None:
        """Initialize scheduling, persistence, and source subscriptions."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}:{entry.entry_id}",
            update_interval=_UPDATE_INTERVAL,
            always_update=False,
        )
        self._state = AdvisorState()
        self._store = Store[dict[str, object]](
            hass,
            _STORE_VERSION,
            f"{DOMAIN}.{entry.entry_id}",
        )

        @callback
        def request_refresh(_: Event[Any]) -> None:
            hass.async_create_task(self.async_request_refresh())

        entry.async_on_unload(
            async_track_state_change_event(
                hass,
                configured_entity_ids(entry),
                request_refresh,
            )
        )

    @override
    async def _async_setup(self) -> None:
        """Load independently versioned state before the first evaluation."""
        if (stored := await self._store.async_load()) is not None:
            self._state = state_from_dict(stored)

    @override
    async def _async_update_data(self) -> CoordinatorData:
        """Assemble, evaluate, persist, and publish one coherent snapshot."""
        now = dt_util.utcnow()
        if has_duplicate_entity_links(
            self.config_entry.data,
            *(
                subentry.data
                for subentry in self.config_entry.subentries.values()
                if subentry.subentry_type != SUBENTRY_TYPE_RECIPIENT
            ),
        ):
            raise UpdateFailed("Duplicate entity links in advisor configuration")
        settings: EvaluationSettings | None = None
        profiles = None
        source_max_age: timedelta | None = None
        room_temperature_max_age: timedelta | None = None
        try:
            profiles = profiles_from_options(dict(self.config_entry.options))
            (
                optimizer,
                stability,
                source_age_minutes,
                room_age_minutes,
            ) = settings_from_options(dict(self.config_entry.options))
            settings = EvaluationSettings(optimizer, stability)
            source_max_age = timedelta(minutes=source_age_minutes)
            room_temperature_max_age = timedelta(minutes=room_age_minutes)
        except KeyError, ValueError:
            pass

        try:
            built = build_snapshot(
                self.hass,
                self.config_entry,
                self._state,
                now,
                source_max_age,
                room_temperature_max_age,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise UpdateFailed("Invalid stored advisor configuration") from error

        season = None
        profile = None
        profile_forecast_available = False
        if profiles is not None and settings is not None:
            forecast = await async_daily_forecast(
                self.hass,
                self.config_entry.data[CONF_WEATHER_ENTITY_ID],
            )
            profile_forecast_available = forecast.available
            temperatures = built.indoor_temperatures_c
            season = select_season(
                SelectionMode(self.config_entry.options[CONF_SELECTION_MODE]),
                profiles,
                month=dt_util.as_local(now).month,
                indoor_min_c=min(temperatures) if temperatures else None,
                indoor_max_c=max(temperatures) if temperatures else None,
                forecast_daily_max_c=forecast.maximum_temperatures_c,
            )
            profile = profiles.for_season(season)

        evaluation = evaluate_snapshot(
            EvaluationSnapshot(season, profile, built.openings),
            self._state,
            now,
            settings,
        )
        state_changed = evaluation.state != self._state
        self._state = evaluation.state
        if state_changed:
            await self._store.async_save(state_to_dict(self._state))
        await async_deliver_notification_candidate(
            self.hass,
            self.config_entry,
            evaluation.notification_candidate,
        )
        quality = dict(built.source_quality)
        quality["options"] = (
            "ready" if settings is not None else "configuration_required"
        )
        return CoordinatorData(evaluation, quality, profile_forecast_available)


type WindowClimateAdvisorConfigEntry = ConfigEntry[WindowClimateAdvisorCoordinator]
