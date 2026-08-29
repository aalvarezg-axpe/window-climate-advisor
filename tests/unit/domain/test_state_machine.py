"""Tests for pure cost and time stability transitions."""

import math
from datetime import UTC, datetime, timedelta, timezone

import pytest

from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    WindowState,
)
from custom_components.window_climate_advisor.domain.optimizer import (
    CandidateAction,
    CandidateEvaluation,
    OptimizationResult,
)
from custom_components.window_climate_advisor.domain.policy import (
    PolicyResult,
    ReasonCode,
    Recommendation,
)
from custom_components.window_climate_advisor.domain.state_machine import (
    BlindDirection,
    OpeningStabilityState,
    PendingBlind,
    PendingWindow,
    StabilityInput,
    StabilitySettings,
    advance_opening,
    initial_stability_state,
)
from custom_components.window_climate_advisor.domain.thermal import ThermalLoad

NOW = datetime(2026, 8, 24, 10, tzinfo=UTC)
SETTINGS = StabilitySettings(50, 10)


def _evaluation(action: CandidateAction, total_cost_w: float) -> CandidateEvaluation:
    load = ThermalLoad(0, 0, 0)
    return CandidateEvaluation(action, load, None, 0, 0, 0, total_cost_w)


def sample(
    current: CandidateAction,
    target_state: WindowState,
    target_blind: float,
    *,
    benefit_w: float = 100,
    reason: ReasonCode = ReasonCode.OPTIMIZER,
    recommendation: Recommendation | None = None,
    gust_kmh: float | None = 0,
) -> StabilityInput:
    """Build an internally consistent stability sample."""
    target = CandidateAction(target_state, BlindOpening(target_blind))
    optimized = OptimizationResult(
        _evaluation(target, 0),
        _evaluation(current, benefit_w),
        33,
    )
    recommendation = (
        recommendation
        or {
            WindowState.CLOSED: Recommendation.CLOSE,
            WindowState.TILT: Recommendation.TILT,
            WindowState.OPEN: Recommendation.OPEN,
        }[target_state]
    )
    if reason in {ReasonCode.MISSING_SAFETY_DATA, ReasonCode.STALE_SAFETY_DATA}:
        recommendation = Recommendation.DEGRADED
    return StabilityInput(
        current,
        optimized,
        PolicyResult(
            recommendation,
            target_state,
            target.blind,
            reason
            not in {
                ReasonCode.WIND_CLOSE,
                ReasonCode.RAIN_CLOSE,
                ReasonCode.MISSING_SAFETY_DATA,
                ReasonCode.STALE_SAFETY_DATA,
            },
            reason,
        ),
        gust_kmh,
    )


def test_minimum_avoided_cost_blocks_small_joint_changes() -> None:
    """Use optimizer benefit rather than another disconnected solar threshold."""
    current = CandidateAction(WindowState.CLOSED, BlindOpening(100))
    state = initial_stability_state(current)

    low = advance_opening(
        state,
        sample(current, WindowState.OPEN, 80, benefit_w=49.99),
        NOW,
        SETTINGS,
    )
    boundary = advance_opening(
        state,
        sample(current, WindowState.OPEN, 80, benefit_w=50),
        NOW,
        SETTINGS,
    )

    assert low.state == state
    assert not low.changed
    assert boundary.state.pending_window == PendingWindow(WindowState.OPEN, NOW)
    assert boundary.state.pending_blind == PendingBlind(
        BlindDirection.LOWER,
        BlindOpening(80),
        NOW,
    )


def test_stable_target_immediately_corrects_zero_blind_for_non_closed_window() -> None:
    """Never retain an incoherent target while waiting for thermal benefit."""
    current = CandidateAction(WindowState.TILT, BlindOpening(0))
    proposal = sample(
        current,
        WindowState.TILT,
        20,
        benefit_w=0,
        recommendation=Recommendation.TILT,
    )

    result = advance_opening(initial_stability_state(current), proposal, NOW, SETTINGS)

    assert result.blind_changed
    assert result.state == OpeningStabilityState(
        WindowState.TILT,
        BlindOpening(20),
        blind_direction=BlindDirection.RAISE,
    )


def test_joint_opening_from_zero_blind_waits_and_changes_once() -> None:
    """Coordinate window and blind so no non-closed/0% state is published."""
    current = CandidateAction(WindowState.CLOSED, BlindOpening(0))
    proposal = sample(current, WindowState.OPEN, 20)

    started = advance_opening(initial_stability_state(current), proposal, NOW, SETTINGS)
    waiting = advance_opening(
        started.state, proposal, NOW + timedelta(minutes=10), SETTINGS
    )
    accepted = advance_opening(
        waiting.state, proposal, NOW + timedelta(minutes=15), SETTINGS
    )

    assert not started.changed and not waiting.changed
    assert started.state.pending_window == PendingWindow(WindowState.OPEN, NOW)
    assert started.state.pending_blind == PendingBlind(
        BlindDirection.RAISE,
        BlindOpening(20),
        NOW,
    )
    assert accepted.window_changed and accepted.blind_changed
    assert accepted.state.window is WindowState.OPEN
    assert accepted.state.blind == BlindOpening(20)


def test_low_benefit_close_can_resolve_non_closed_zero_blind() -> None:
    """Allow closing to restore coherence even below the movement threshold."""
    current = CandidateAction(WindowState.OPEN, BlindOpening(0))

    result = advance_opening(
        initial_stability_state(current),
        sample(current, WindowState.CLOSED, 0, benefit_w=0),
        NOW,
        SETTINGS,
    )

    assert result.window_changed
    assert result.state == OpeningStabilityState(WindowState.CLOSED, BlindOpening(0))


def test_opening_improvement_requires_ten_continuous_minutes() -> None:
    """Confirm opening improvements and avoid repeating an accepted state."""
    current = CandidateAction(WindowState.TILT, BlindOpening(100))
    state = initial_stability_state(current)
    proposal = sample(current, WindowState.OPEN, 100)

    started = advance_opening(state, proposal, NOW, SETTINGS)
    waiting = advance_opening(
        started.state, proposal, NOW + timedelta(minutes=9), SETTINGS
    )
    accepted = advance_opening(
        waiting.state, proposal, NOW + timedelta(minutes=10), SETTINGS
    )
    repeated = advance_opening(
        accepted.state, proposal, NOW + timedelta(minutes=20), SETTINGS
    )

    assert not started.changed
    assert not waiting.changed
    assert accepted.window_changed
    assert accepted.state.window is WindowState.OPEN
    assert not repeated.changed
    assert repeated.state.pending_window is None


def test_safety_close_and_rain_tilt_are_immediate() -> None:
    """Never delay absolute weather restrictions behind thermal hysteresis."""
    current = CandidateAction(WindowState.OPEN, BlindOpening(100))
    state = initial_stability_state(current)

    closed = advance_opening(
        state,
        sample(
            current,
            WindowState.CLOSED,
            100,
            benefit_w=0,
            reason=ReasonCode.WIND_CLOSE,
            gust_kmh=45,
        ),
        NOW,
        SETTINGS,
    )
    tilted = advance_opening(
        state,
        sample(
            current,
            WindowState.TILT,
            100,
            benefit_w=0,
            reason=ReasonCode.RAIN_TILT_ONLY,
        ),
        NOW,
        SETTINGS,
    )

    assert closed.window_changed and closed.state.window is WindowState.CLOSED
    assert tilted.window_changed and tilted.state.window is WindowState.TILT


def test_thermal_closing_uses_benefit_without_a_second_time_delay() -> None:
    """Accept a worthwhile thermal restriction after the optimizer penalty."""
    current = CandidateAction(WindowState.OPEN, BlindOpening(100))
    result = advance_opening(
        initial_stability_state(current),
        sample(current, WindowState.CLOSED, 100, benefit_w=50),
        NOW,
        SETTINGS,
    )

    assert result.window_changed
    assert result.state.window is WindowState.CLOSED
    assert result.state.pending_window is None


def test_marginal_wind_tilt_waits_five_minutes_but_20_kmh_is_immediate() -> None:
    """Retain the selective v4.17 open-to-tilt degradation timing."""
    current = CandidateAction(WindowState.OPEN, BlindOpening(100))
    state = initial_stability_state(current)
    marginal = sample(
        current,
        WindowState.TILT,
        100,
        reason=ReasonCode.WIND_TILT_ONLY,
        gust_kmh=19.9,
    )

    started = advance_opening(state, marginal, NOW, SETTINGS)
    waiting = advance_opening(
        started.state, marginal, NOW + timedelta(minutes=4), SETTINGS
    )
    accepted = advance_opening(
        waiting.state, marginal, NOW + timedelta(minutes=5), SETTINGS
    )
    immediate = advance_opening(
        state,
        sample(
            current,
            WindowState.TILT,
            100,
            reason=ReasonCode.WIND_TILT_ONLY,
            gust_kmh=20,
        ),
        NOW,
        SETTINGS,
    )

    assert not started.changed and not waiting.changed
    assert accepted.window_changed
    assert immediate.window_changed


def test_blind_direction_requires_fifteen_minutes_without_drift_rearming() -> None:
    """Confirm physical direction while treating exact percentage as diagnostic."""
    current = CandidateAction(WindowState.CLOSED, BlindOpening(100))
    state = initial_stability_state(current)

    started = advance_opening(
        state,
        sample(current, WindowState.CLOSED, 80),
        NOW,
        SETTINGS,
    )
    drifted = advance_opening(
        started.state,
        sample(current, WindowState.CLOSED, 70),
        NOW + timedelta(minutes=10),
        SETTINGS,
    )
    accepted = advance_opening(
        drifted.state,
        sample(current, WindowState.CLOSED, 60),
        NOW + timedelta(minutes=15),
        SETTINGS,
    )
    same_direction = advance_opening(
        accepted.state,
        sample(current, WindowState.CLOSED, 40),
        NOW + timedelta(minutes=20),
        SETTINGS,
    )

    assert not started.changed and not drifted.changed
    assert drifted.state.pending_blind is not None
    assert drifted.state.pending_blind.since == NOW
    assert accepted.blind_changed
    assert accepted.state.blind == BlindOpening(60)
    assert accepted.state.blind_direction is BlindDirection.LOWER
    assert not same_direction.changed
    assert same_direction.state.blind == BlindOpening(40)


def test_opposite_blind_direction_rearms_and_deadband_cancels_candidates() -> None:
    """Require stability again for an opposite physical instruction."""
    current = CandidateAction(WindowState.CLOSED, BlindOpening(60))
    state = OpeningStabilityState(
        WindowState.CLOSED,
        BlindOpening(60),
        blind_direction=BlindDirection.LOWER,
    )
    raising = sample(current, WindowState.CLOSED, 90)

    started = advance_opening(state, raising, NOW, SETTINGS)
    cancelled = advance_opening(
        started.state,
        sample(current, WindowState.CLOSED, 65),
        NOW + timedelta(minutes=5),
        SETTINGS,
    )
    restarted = advance_opening(
        cancelled.state,
        raising,
        NOW + timedelta(minutes=10),
        SETTINGS,
    )
    accepted = advance_opening(
        restarted.state,
        raising,
        NOW + timedelta(minutes=25),
        SETTINGS,
    )

    assert cancelled.state.pending_blind is None
    assert cancelled.state.blind == BlindOpening(65)
    assert restarted.state.pending_blind is not None
    assert accepted.blind_changed
    assert accepted.state.blind_direction is BlindDirection.RAISE


def test_state_inputs_enforce_units_ranges_and_utc_ordering() -> None:
    """Reject malformed tuning, weather, and restart timestamps."""
    for values in (
        (-1, 10),
        (math.inf, 10),
        (0, -1),
        (0, 101),
    ):
        with pytest.raises(ValueError):
            StabilitySettings(*values)
    with pytest.raises(ValueError):
        StabilitySettings(0, 10, marginal_wind_delay=timedelta(0))
    with pytest.raises(ValueError):
        StabilitySettings(0, 10, immediate_wind_gust_kmh=math.nan)
    with pytest.raises(ValueError):
        PendingWindow(WindowState.OPEN, datetime(2026, 8, 24, 10))
    with pytest.raises(ValueError):
        PendingBlind(
            BlindDirection.LOWER,
            BlindOpening(50),
            NOW.astimezone(timezone(timedelta(hours=2))),
        )

    current = CandidateAction(WindowState.OPEN, BlindOpening(100))
    with pytest.raises(ValueError):
        sample(current, WindowState.TILT, 100, gust_kmh=-1)
    with pytest.raises(ValueError):
        advance_opening(
            initial_stability_state(current),
            sample(current, WindowState.TILT, 100),
            datetime(2026, 8, 24, 10),
            SETTINGS,
        )

    pending_window = OpeningStabilityState(
        WindowState.TILT,
        BlindOpening(100),
        pending_window=PendingWindow(WindowState.OPEN, NOW),
    )
    with pytest.raises(ValueError):
        advance_opening(
            pending_window,
            sample(current, WindowState.OPEN, 100),
            NOW - timedelta(minutes=1),
            SETTINGS,
        )

    pending_blind = OpeningStabilityState(
        WindowState.CLOSED,
        BlindOpening(100),
        pending_blind=PendingBlind(
            BlindDirection.LOWER,
            BlindOpening(50),
            NOW,
        ),
    )
    with pytest.raises(ValueError):
        advance_opening(
            pending_blind,
            sample(
                CandidateAction(WindowState.CLOSED, BlindOpening(100)),
                WindowState.CLOSED,
                50,
            ),
            NOW - timedelta(minutes=1),
            SETTINGS,
        )
