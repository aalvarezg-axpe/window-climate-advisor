"""Home Assistant scheduling and restart-safe advisor state."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .adapters.forecast import async_daily_forecast
from .adapters.home_assistant import build_snapshot, configured_entity_ids
from .adapters.notifications import (
    async_deliver_arrival_candidate,
    async_deliver_notification_candidate,
    home_notification_recipient_persons,
)
from .application.evaluator import (
    AdvisorEvaluation,
    EvaluationSettings,
    EvaluationSnapshot,
    evaluate_snapshot,
)
from .application.notifications import OpeningFeedback, arrival_notification_candidate
from .application.state import (
    AdvisorState,
    NotificationCandidate,
    merge_notification_candidates,
    state_from_dict,
    state_to_dict,
)
from .config_flow import (
    has_duplicate_entity_links,
    occupancy_person_entity_ids,
    profiles_from_options,
    settings_from_options,
)
from .const import (
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_PERSON_ENTITY_ID,
    CONF_SELECTION_MODE,
    CONF_WEATHER_ENTITY_ID,
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
)
from .domain.profiles import SelectionMode, select_season

_LOGGER = logging.getLogger(__name__)
_UPDATE_INTERVAL = timedelta(minutes=5)
_NOTIFICATION_BATCH_WINDOW = timedelta(minutes=10)
_NOTIFICATION_PAIRING_RETRIES = 2
_STORE_VERSION = 1


def _arrival_person_entity_id(entry: ConfigEntry, event: Event[Any]) -> str | None:
    """Return a configured person only for a real non-home to home edge."""
    old_state = event.data.get("old_state")
    new_state = event.data.get("new_state")
    if old_state is None or new_state is None or new_state.state != STATE_HOME:
        return None
    if old_state.state in {STATE_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN}:
        return None
    entity_id = new_state.entity_id
    if not isinstance(entity_id, str):
        return None
    if any(
        subentry.subentry_type == SUBENTRY_TYPE_RECIPIENT
        and subentry.data.get(CONF_PERSON_ENTITY_ID) == entity_id
        for subentry in entry.subentries.values()
    ):
        return entity_id
    return None


def _dwelling_occupied(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Treat only an entirely known-away selected group as unoccupied."""
    try:
        entity_ids = occupancy_person_entity_ids(entry.data)
    except ValueError:
        return True
    if not entity_ids:
        return True
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None or state.state in {
            STATE_HOME,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        }:
            return True
    return False


@dataclass(frozen=True, slots=True)
class CoordinatorData:
    """Published evaluation plus redacted source quality."""

    evaluation: AdvisorEvaluation
    source_quality: dict[str, str]
    daily_forecast_available: bool


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
        self._pending_arrivals: set[str] = set()
        self._pending_notification: NotificationCandidate | None = None
        self._pending_notification_people: set[str] = set()
        self._cancel_notification_timer: Callable[[], None] | None = None
        self._notification_pairing_retries = 0

        @callback
        def request_refresh(event: Event[Any]) -> None:
            if person_entity_id := _arrival_person_entity_id(entry, event):
                self._pending_arrivals.add(person_entity_id)
            hass.async_create_task(self.async_request_refresh())

        entry.async_on_unload(
            async_track_state_change_event(
                hass,
                configured_entity_ids(entry),
                request_refresh,
            )
        )
        entry.async_on_unload(self._cancel_notification_batch)

    @callback
    def _cancel_notification_batch(self) -> None:
        """Discard the deliberately non-persistent ordinary delivery batch."""
        if self._cancel_notification_timer is not None:
            self._cancel_notification_timer()
        self._cancel_notification_timer = None
        self._pending_notification = None
        self._pending_notification_people.clear()
        self._notification_pairing_retries = 0

    @callback
    def _queue_notification_candidate(
        self,
        candidate: NotificationCandidate | None,
        arriving_person_ids: tuple[str, ...],
    ) -> None:
        """Retain one bounded batch without creating an away-time queue."""
        self._pending_notification_people.difference_update(arriving_person_ids)
        if candidate is None:
            return
        eligible_people = set(
            home_notification_recipient_persons(self.hass, self.config_entry)
        )
        eligible_people.difference_update(arriving_person_ids)
        if not eligible_people:
            return
        self._pending_notification = merge_notification_candidates(
            self._pending_notification,
            candidate,
        )
        self._pending_notification_people.update(eligible_people)
        if self._cancel_notification_timer is None:
            self._notification_pairing_retries = _NOTIFICATION_PAIRING_RETRIES
            self._cancel_notification_timer = async_call_later(
                self.hass,
                _NOTIFICATION_BATCH_WINDOW,
                self._async_flush_notification_batch,
            )

    async def _async_flush_notification_batch(self, _: datetime) -> None:
        """Deliver one batch, briefly waiting for its paired blind change."""
        candidate = self._pending_notification
        if (
            candidate is not None
            and self._notification_pairing_retries > 0
            and any(
                change.window_changed
                and not change.blind_changed
                and (opening := self._state.openings.get(change.opening_id)) is not None
                and opening.pending_blind is not None
                for change in candidate.changes
            )
        ):
            self._notification_pairing_retries -= 1
            self._cancel_notification_timer = async_call_later(
                self.hass,
                _UPDATE_INTERVAL,
                self._async_flush_notification_batch,
            )
            return
        included_people = set(self._pending_notification_people)
        self._cancel_notification_timer = None
        self._pending_notification = None
        self._pending_notification_people.clear()
        self._notification_pairing_retries = 0
        await async_deliver_notification_candidate(
            self.hass,
            self.config_entry,
            candidate,
            included_person_entity_ids=included_people,
        )

    @override
    async def _async_setup(self) -> None:
        """Load independently versioned state before the first evaluation."""
        if (stored := await self._store.async_load()) is not None:
            self._state = state_from_dict(stored)

    @override
    async def _async_update_data(self) -> CoordinatorData:
        """Assemble, evaluate, persist, and publish one coherent snapshot."""
        arriving_person_ids = tuple(sorted(self._pending_arrivals))
        self._pending_arrivals.difference_update(arriving_person_ids)
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
        daily_forecast_available = False
        today_forecast_max_c = None
        if profiles is not None and settings is not None:
            forecast = await async_daily_forecast(
                self.hass,
                self.config_entry.data[CONF_WEATHER_ENTITY_ID],
            )
            daily_forecast_available = forecast.available
            today_forecast_max_c = (
                forecast.maximum_temperatures_c[0]
                if forecast.maximum_temperatures_c
                else None
            )
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
            EvaluationSnapshot(
                season,
                profile,
                built.openings,
                today_forecast_max_c,
                _dwelling_occupied(self.hass, self.config_entry),
            ),
            self._state,
            now,
            settings,
        )
        state_changed = evaluation.state != self._state
        self._state = evaluation.state
        if state_changed:
            await self._store.async_save(state_to_dict(self._state))
        self._queue_notification_candidate(
            evaluation.notification_candidate,
            arriving_person_ids,
        )
        if arriving_person_ids:
            feedback_by_opening: dict[str, OpeningFeedback] = {}
            for opening in built.openings:
                subentry = self.config_entry.subentries.get(opening.opening_id)
                data = (
                    subentry.data
                    if subentry is not None
                    and subentry.subentry_type == SUBENTRY_TYPE_OPENING
                    else {}
                )
                feedback_by_opening[opening.opening_id] = OpeningFeedback(
                    opening.current_action,
                    isinstance(data.get(CONF_CONTACT_ENTITY_ID), str),
                    isinstance(data.get(CONF_COVER_ENTITY_ID), str),
                )
            arrival_candidate = arrival_notification_candidate(
                evaluation, feedback_by_opening
            )
            for person_entity_id in arriving_person_ids:
                await async_deliver_arrival_candidate(
                    self.hass,
                    self.config_entry,
                    person_entity_id,
                    arrival_candidate,
                )
        quality = dict(built.source_quality)
        quality["options"] = (
            "ready" if settings is not None else "configuration_required"
        )
        return CoordinatorData(evaluation, quality, daily_forecast_available)


type WindowClimateAdvisorConfigEntry = ConfigEntry[WindowClimateAdvisorCoordinator]
