"""Tests for coordinator scheduling, degradation, and persistence."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.components.weather import SERVICE_GET_FORECASTS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util import dt as dt_util

from custom_components.window_climate_advisor.application.evaluator import (
    InputIssue,
    evaluate_snapshot,
)
from custom_components.window_climate_advisor.application.state import (
    AdvisorState,
    NotificationCandidate,
    OpeningChange,
)
from custom_components.window_climate_advisor.const import (
    CONF_OCCUPANCY_PERSON_ENTITY_IDS,
    CONF_PERSON_ENTITY_ID,
    CONF_WIND_GUST_ENTITY_ID,
    CONF_WIND_SPEED_ENTITY_ID,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_RECIPIENT,
)
from custom_components.window_climate_advisor.coordinator import (
    WindowClimateAdvisorCoordinator,
    _dwelling_occupied,
)
from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    WindowState,
)
from custom_components.window_climate_advisor.domain.optimizer import optimize_opening
from custom_components.window_climate_advisor.domain.policy import (
    ReasonCode,
    Recommendation,
)
from custom_components.window_climate_advisor.domain.profiles import Season
from custom_components.window_climate_advisor.domain.state_machine import (
    BlindDirection,
    OpeningStabilityState,
    PendingBlind,
    PendingWindow,
)
from tests.integration.test_adapters import entry, set_ready_states
from tests.integration.test_config_flow import VALID_OPTIONS


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Allow native day-start listeners owned by config-entry unload."""
    return True


async def test_coordinator_tracks_the_configured_local_day_start(
    hass: HomeAssistant,
) -> None:
    """Request one refresh at the native local-time boundary."""
    config_entry = entry()
    object.__setattr__(
        config_entry, "options", type(config_entry.options)(VALID_OPTIONS)
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.window_climate_advisor.coordinator.async_track_time_change",
        return_value=Mock(),
    ) as track:
        coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    assert track.call_args.kwargs == {"hour": 8, "minute": 0, "second": 0}
    callback = track.call_args.args[1]
    with patch.object(
        coordinator, "async_request_refresh", new_callable=AsyncMock
    ) as refresh:
        callback(datetime(2026, 9, 2, 8, tzinfo=ZoneInfo("Europe/Madrid")))
        await hass.async_block_till_done()
    refresh.assert_awaited_once()


async def test_incomplete_options_load_as_explicit_degradation(
    hass: HomeAssistant,
) -> None:
    """Keep the UI-repairable entry loaded without hidden tuning defaults."""
    config_entry = entry()
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    opening = next(iter(coordinator.data.evaluation.openings.values()))
    assert opening.recommendation is Recommendation.DEGRADED
    assert opening.reason is InputIssue.CONFIGURATION_REQUIRED
    assert coordinator.data.source_quality["options"] == "configuration_required"
    assert not coordinator.data.daily_forecast_available


async def test_configured_coordinator_uses_forecast_persists_and_refreshes(
    hass: HomeAssistant,
) -> None:
    """Evaluate configured sources, persist state, and debounce state events."""
    config_entry = entry()
    object.__setattr__(
        config_entry,
        "data",
        type(config_entry.data)(
            {
                **config_entry.data,
                CONF_OCCUPANCY_PERSON_ENTITY_IDS: [
                    "person.antonio",
                    "person.elisa",
                ],
            }
        ),
    )
    object.__setattr__(
        config_entry, "options", type(config_entry.options)(VALID_OPTIONS)
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    hass.states.async_set("person.antonio", STATE_NOT_HOME)
    hass.states.async_set("person.elisa", STATE_NOT_HOME)
    hass.states.async_set("sun.sun", "above_horizon", {"azimuth": 0, "elevation": 30})

    async def forecast(_: ServiceCall) -> dict[str, object]:
        return {"weather.home": {"forecast": [{"temperature": 30}]}}

    hass.services.async_register(
        "weather",
        SERVICE_GET_FORECASTS,
        forecast,
        supports_response=SupportsResponse.ONLY,
    )
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with (
        patch(
            "custom_components.window_climate_advisor.application.evaluator.optimize_opening",
            wraps=optimize_opening,
        ) as optimizer,
        patch(
            "custom_components.window_climate_advisor.coordinator.evaluate_snapshot",
            wraps=evaluate_snapshot,
        ) as evaluator,
        patch.object(coordinator, "_queue_notification_candidate") as queue,
    ):
        await coordinator.async_config_entry_first_refresh()

    assert coordinator.data.evaluation.season is Season.SUMMER
    assert coordinator.data.daily_forecast_available
    optimizer.assert_called_once()
    snapshot = evaluator.call_args.args[0]
    assert snapshot.today_forecast_max_c == 30
    assert not snapshot.dwelling_occupied
    queue.assert_called_once_with(
        coordinator.data.evaluation.notification_candidate,
        (),
    )
    assert optimizer.call_args.args[0].forecast_conditions is None
    assert optimizer.call_args.args[0].allow_diffuse_blind_protection
    assert coordinator.data.source_quality["options"] == "ready"
    with patch.object(
        coordinator, "async_request_refresh", new_callable=AsyncMock
    ) as refresh:
        hass.states.async_set("sensor.outdoor", "21", {"unit_of_measurement": "°C"})
        await hass.async_block_till_done()
        refresh.assert_awaited_once()

    restored = WindowClimateAdvisorCoordinator(hass, config_entry)
    await restored.async_config_entry_first_refresh()
    assert restored.data.evaluation.state == coordinator.data.evaluation.state


async def test_first_refresh_after_day_start_resets_and_persists_assumptions(
    hass: HomeAssistant,
) -> None:
    """Catch up a missed boundary and discard the preceding ordinary batch."""
    config_entry = entry()
    object.__setattr__(
        config_entry, "options", type(config_entry.options)(VALID_OPTIONS)
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)
    opening_id = next(
        subentry_id
        for subentry_id, subentry in config_entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    old = datetime(2026, 9, 1, 6, tzinfo=UTC)
    coordinator._state = AdvisorState(
        {
            opening_id: OpeningStabilityState(
                WindowState.TILT,
                BlindOpening(50),
                blind_direction=BlindDirection.LOWER,
                pending_window=PendingWindow(WindowState.OPEN, old),
                pending_blind=PendingBlind(
                    BlindDirection.LOWER,
                    BlindOpening(20),
                    old,
                ),
            )
        },
        date(2026, 9, 1),
    )
    coordinator._pending_notification = NotificationCandidate(
        (
            OpeningChange(
                opening_id,
                coordinator._state.openings[opening_id],
                ReasonCode.OPTIMIZER,
                True,
                True,
            ),
        )
    )
    cancel = Mock()
    coordinator._cancel_notification_timer = cancel
    now = datetime(2026, 9, 2, 6, tzinfo=UTC)
    local_now = datetime(2026, 9, 2, 8, tzinfo=ZoneInfo("Europe/Madrid"))

    with (
        patch(
            "custom_components.window_climate_advisor.coordinator.dt_util.utcnow",
            return_value=now,
        ),
        patch(
            "custom_components.window_climate_advisor.coordinator.dt_util.as_local",
            return_value=local_now,
        ),
    ):
        await coordinator.async_config_entry_first_refresh()

    stable = coordinator._state.openings[opening_id]
    assert coordinator._state.day_started_on == date(2026, 9, 2)
    assert stable.window is WindowState.CLOSED
    assert stable.blind == BlindOpening(0)
    assert stable.pending_window is None or stable.pending_window.since == now
    assert stable.pending_blind is None or stable.pending_blind.since == now
    cancel.assert_called_once()
    assert coordinator._pending_notification is None
    stored = await coordinator._store.async_load()
    assert stored is not None
    assert stored["day_started_on"] == "2026-09-02"


def test_dwelling_occupancy_requires_every_selected_person_known_away(
    hass: HomeAssistant,
) -> None:
    """Fail conservatively for empty configuration and unusable person states."""
    config_entry = entry()
    assert _dwelling_occupied(hass, config_entry)
    object.__setattr__(
        config_entry,
        "data",
        type(config_entry.data)(
            {
                **config_entry.data,
                CONF_OCCUPANCY_PERSON_ENTITY_IDS: [
                    "person.antonio",
                    "person.elisa",
                ],
            }
        ),
    )

    hass.states.async_set("person.antonio", STATE_NOT_HOME)
    hass.states.async_set("person.elisa", "work")
    assert not _dwelling_occupied(hass, config_entry)
    for state in (STATE_HOME, STATE_UNKNOWN, STATE_UNAVAILABLE):
        hass.states.async_set("person.elisa", state)
        assert _dwelling_occupied(hass, config_entry)


async def test_invalid_structural_storage_fails_setup_explicitly(
    hass: HomeAssistant,
) -> None:
    """Do not silently invent required entity assignments from corrupt config."""
    config_entry = entry()
    object.__setattr__(config_entry, "data", type(config_entry.data)({}))
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


async def test_duplicate_stored_links_fail_setup_explicitly(
    hass: HomeAssistant,
) -> None:
    """Defend setup against duplicate links from older or corrupted storage."""
    config_entry = entry()
    object.__setattr__(
        config_entry,
        "data",
        type(config_entry.data)(
            {
                **config_entry.data,
                CONF_WIND_GUST_ENTITY_ID: config_entry.data[CONF_WIND_SPEED_ENTITY_ID],
            }
        ),
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


async def test_invalid_recipient_link_does_not_degrade_advisor(
    hass: HomeAssistant,
) -> None:
    """Keep notification configuration failures outside climate evaluation."""
    config_entry = entry(recipient=True)
    object.__setattr__(
        config_entry,
        "options",
        type(config_entry.options)(VALID_OPTIONS),
    )
    recipient = next(
        subentry
        for subentry in config_entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_RECIPIENT
    )
    object.__setattr__(
        recipient,
        "data",
        type(recipient.data)(
            {
                **recipient.data,
                CONF_PERSON_ENTITY_ID: config_entry.data[CONF_WIND_SPEED_ENTITY_ID],
            }
        ),
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data.source_quality["options"] == "ready"
    assert all(
        opening.recommendation is not Recommendation.DEGRADED
        for opening in coordinator.data.evaluation.openings.values()
    )


async def test_only_real_arrival_runs_fresh_targeted_delivery(
    hass: HomeAssistant,
) -> None:
    """Ignore startup/recovery and send once for a real away-to-home edge."""
    config_entry = entry(recipient=True)
    object.__setattr__(
        config_entry,
        "options",
        type(config_entry.options)(VALID_OPTIONS),
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    hass.states.async_set("person.resident", STATE_HOME)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with (
        patch.object(coordinator, "_queue_notification_candidate") as ordinary,
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_arrival_candidate",
            new_callable=AsyncMock,
            return_value=0,
        ) as arrival,
    ):
        await coordinator.async_config_entry_first_refresh()
        arrival.assert_not_awaited()

        with patch.object(
            coordinator, "async_request_refresh", new_callable=AsyncMock
        ) as refresh:
            ordinary.reset_mock()
            hass.states.async_set("person.resident", STATE_NOT_HOME)
            await hass.async_block_till_done()
            refresh.assert_awaited_once()
            arrival.assert_not_awaited()

            refresh.reset_mock()
            ordinary.reset_mock()
            hass.states.async_set("person.resident", STATE_HOME)
            await hass.async_block_till_done()
            refresh.assert_awaited_once()
            await coordinator.async_refresh()

            arrival.assert_awaited_once()
            assert arrival.await_args.args[0:3] == (
                hass,
                config_entry,
                "person.resident",
            )
            assert ordinary.call_args.args[1] == ("person.resident",)

            arrival.reset_mock()
            hass.states.async_set("person.resident", STATE_HOME, {"source": "update"})
            await hass.async_block_till_done()
            await coordinator.async_refresh()
            arrival.assert_not_awaited()

            hass.states.async_set("person.resident", STATE_UNAVAILABLE)
            await hass.async_block_till_done()
            await coordinator.async_refresh()
            arrival.reset_mock()
            hass.states.async_set("person.resident", STATE_HOME)
            await hass.async_block_till_done()
            await coordinator.async_refresh()
            arrival.assert_not_awaited()


async def test_ordinary_changes_use_one_fixed_batch_and_discard_on_unload(
    hass: HomeAssistant,
) -> None:
    """Merge staggered rows once without retaining away or arrival advice."""
    config_entry = entry(recipient=True)
    config_entry.add_to_hass(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)
    first = NotificationCandidate(
        (
            OpeningChange(
                "opening-b",
                OpeningStabilityState(WindowState.TILT, BlindOpening(100)),
                ReasonCode.OPTIMIZER,
                True,
                False,
            ),
        )
    )
    second = NotificationCandidate(
        (
            OpeningChange(
                "opening-a",
                OpeningStabilityState(WindowState.CLOSED, BlindOpening(0)),
                ReasonCode.WIND_CLOSE,
                True,
                True,
            ),
        )
    )
    scheduled: list[object] = []
    cancel = Mock()

    def schedule(_: object, delay: timedelta, action: object) -> Mock:
        assert delay == timedelta(minutes=10)
        scheduled.append(action)
        return cancel

    with (
        patch(
            "custom_components.window_climate_advisor.coordinator.home_notification_recipient_persons",
            side_effect=[
                (),
                ("person.resident",),
                ("person.resident",),
                ("person.resident",),
                ("person.resident",),
            ],
        ),
        patch(
            "custom_components.window_climate_advisor.coordinator.async_call_later",
            side_effect=schedule,
        ) as call_later,
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_notification_candidate",
            new_callable=AsyncMock,
            return_value=1,
        ) as deliver,
    ):
        coordinator._queue_notification_candidate(first, ())
        call_later.assert_not_called()

        coordinator._queue_notification_candidate(first, ())
        coordinator._queue_notification_candidate(second, ())
        call_later.assert_called_once()
        assert len(scheduled) == 1

        callback = scheduled[0]
        assert callable(callback)
        await callback(dt_util.utcnow())

        deliver.assert_awaited_once()
        delivered = deliver.await_args.args[2]
        assert isinstance(delivered, NotificationCandidate)
        assert [change.opening_id for change in delivered.changes] == [
            "opening-a",
            "opening-b",
        ]
        assert deliver.await_args.kwargs["included_person_entity_ids"] == {
            "person.resident"
        }

        deliver.reset_mock()
        coordinator._queue_notification_candidate(first, ())
        coordinator._queue_notification_candidate(None, ("person.resident",))
        await scheduled[1](dt_util.utcnow())
        assert deliver.await_args.kwargs["included_person_entity_ids"] == set()

        coordinator._queue_notification_candidate(first, ())
        coordinator._cancel_notification_batch()
        cancel.assert_called()
        assert coordinator._pending_notification is None


async def test_window_batch_waits_for_and_merges_same_opening_blind(
    hass: HomeAssistant,
) -> None:
    """Deliver one work round when blind confirmation follows the window."""
    config_entry = entry(recipient=True)
    config_entry.add_to_hass(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)
    now = dt_util.utcnow()
    window = NotificationCandidate(
        (
            OpeningChange(
                "opening-a",
                OpeningStabilityState(WindowState.CLOSED, BlindOpening(100)),
                ReasonCode.SOLAR_GAIN,
                True,
                False,
            ),
        )
    )
    coordinator._state = AdvisorState(
        {
            "opening-a": OpeningStabilityState(
                WindowState.CLOSED,
                BlindOpening(100),
                pending_blind=PendingBlind(
                    BlindDirection.LOWER,
                    BlindOpening(20),
                    now,
                ),
            )
        }
    )
    scheduled: list[tuple[timedelta, object]] = []

    def schedule(_: object, delay: timedelta, action: object) -> Mock:
        scheduled.append((delay, action))
        return Mock()

    with (
        patch(
            "custom_components.window_climate_advisor.coordinator.home_notification_recipient_persons",
            return_value=("person.resident",),
        ),
        patch(
            "custom_components.window_climate_advisor.coordinator.async_call_later",
            side_effect=schedule,
        ),
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_notification_candidate",
            new_callable=AsyncMock,
            return_value=1,
        ) as deliver,
    ):
        coordinator._queue_notification_candidate(window, ())
        assert scheduled[0][0] == timedelta(minutes=10)
        await scheduled[0][1](now)
        deliver.assert_not_awaited()
        assert scheduled[1][0] == timedelta(minutes=5)

        confirmed = NotificationCandidate(
            (
                OpeningChange(
                    "opening-a",
                    OpeningStabilityState(WindowState.CLOSED, BlindOpening(20)),
                    ReasonCode.SOLAR_GAIN,
                    False,
                    True,
                ),
            )
        )
        coordinator._state = AdvisorState(
            {
                "opening-a": OpeningStabilityState(
                    WindowState.CLOSED,
                    BlindOpening(20),
                )
            }
        )
        coordinator._queue_notification_candidate(confirmed, ())
        await scheduled[1][1](now + timedelta(minutes=5))

        deliver.assert_awaited_once()
        delivered = deliver.await_args.args[2]
        assert isinstance(delivered, NotificationCandidate)
        assert len(delivered.changes) == 1
        assert delivered.changes[0].window_changed
        assert delivered.changes[0].blind_changed
        assert delivered.changes[0].state.blind == BlindOpening(20)


async def test_window_batch_has_bounded_wait_for_unconfirmed_blind(
    hass: HomeAssistant,
) -> None:
    """Never starve a window message when its blind remains pending."""
    config_entry = entry(recipient=True)
    config_entry.add_to_hass(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)
    now = dt_util.utcnow()
    candidate = NotificationCandidate(
        (
            OpeningChange(
                "opening-a",
                OpeningStabilityState(WindowState.CLOSED, BlindOpening(100)),
                ReasonCode.SOLAR_GAIN,
                True,
                False,
            ),
        )
    )
    coordinator._state = AdvisorState(
        {
            "opening-a": OpeningStabilityState(
                WindowState.CLOSED,
                BlindOpening(100),
                pending_blind=PendingBlind(
                    BlindDirection.LOWER,
                    BlindOpening(20),
                    now,
                ),
            )
        }
    )
    scheduled: list[object] = []

    def schedule(_: object, __: timedelta, action: object) -> Mock:
        scheduled.append(action)
        return Mock()

    with (
        patch(
            "custom_components.window_climate_advisor.coordinator.home_notification_recipient_persons",
            return_value=("person.resident",),
        ),
        patch(
            "custom_components.window_climate_advisor.coordinator.async_call_later",
            side_effect=schedule,
        ),
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_notification_candidate",
            new_callable=AsyncMock,
            return_value=1,
        ) as deliver,
    ):
        coordinator._queue_notification_candidate(candidate, ())
        await scheduled[0](now + timedelta(minutes=10))
        await scheduled[1](now + timedelta(minutes=15))
        deliver.assert_not_awaited()
        await scheduled[2](now + timedelta(minutes=20))

        deliver.assert_awaited_once()
        assert coordinator._pending_notification is None
        assert coordinator._notification_pairing_retries == 0
