"""Tests for deterministic exhaustive opening optimization."""

import math

import pytest

from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    OpeningDimensions,
    ThermalConditions,
    WindowState,
)
from custom_components.window_climate_advisor.domain.optimizer import (
    CandidateAction,
    OptimizationRequest,
    OptimizerSettings,
    enumerate_actions,
    optimize_opening,
)
from custom_components.window_climate_advisor.domain.profiles import ComfortProfile

DIMENSIONS = OpeningDimensions(1.6, 1.2)
PROFILE = ComfortProfile(20, 25, 23, 0.5)
ZERO_PENALTIES = OptimizerSettings(10, 0, 0, 0)
DEFAULT_CURRENT_ACTION = CandidateAction(WindowState.CLOSED, BlindOpening(100))


def request(
    current: ThermalConditions,
    *,
    forecast: ThermalConditions | None = None,
    current_action: CandidateAction = DEFAULT_CURRENT_ACTION,
    supports_tilt: bool = True,
) -> OptimizationRequest:
    """Build one concise typed request for tests."""
    return OptimizationRequest(
        dimensions=DIMENSIONS,
        profile=PROFILE,
        current_conditions=current,
        forecast_conditions=forecast,
        current_action=current_action,
        supports_tilt=supports_tilt,
    )


def test_candidate_space_is_exhaustive_and_tilt_is_constrained() -> None:
    """Enumerate 33 or 22 candidates at the frozen 10% resolution."""
    with_tilt = enumerate_actions(ZERO_PENALTIES, supports_tilt=True)
    without_tilt = enumerate_actions(ZERO_PENALTIES, supports_tilt=False)

    assert len(with_tilt) == 33
    assert len(without_tilt) == 22
    assert {action.blind.percent for action in with_tilt} == set(range(0, 101, 10))
    assert {action.window_state for action in without_tilt} == {
        WindowState.CLOSED,
        WindowState.OPEN,
    }


def test_optimizer_couples_cooling_and_solar_protection() -> None:
    """Open to cool without sun but close/lower against strong solar load."""
    cool = optimize_opening(
        request(ThermalConditions(27, 22, 0, wind_speed_kmh=8, gust_speed_kmh=12)),
        ZERO_PENALTIES,
    )
    solar = optimize_opening(
        request(ThermalConditions(27, 22, 1200, wind_speed_kmh=8, gust_speed_kmh=12)),
        ZERO_PENALTIES,
    )

    assert cool.best.action == CandidateAction(WindowState.OPEN, BlindOpening(100))
    assert solar.best.action == CandidateAction(WindowState.CLOSED, BlindOpening(0))
    assert cool.evaluated_candidates == solar.evaluated_candidates == 33
    assert cool.avoided_cost_w > 0
    assert solar.avoided_cost_w > 0


def test_optimizer_uses_the_worse_current_or_forecast_horizon() -> None:
    """Do not accept a current benefit that the valid forecast reverses."""
    current = ThermalConditions(27, 22, 0, wind_speed_kmh=8, gust_speed_kmh=12)
    forecast = ThermalConditions(27, 22, 1200, wind_speed_kmh=8, gust_speed_kmh=12)
    current_only = optimize_opening(request(current), ZERO_PENALTIES)
    with_forecast = optimize_opening(
        request(current, forecast=forecast), ZERO_PENALTIES
    )

    assert current_only.best.action.window_state is WindowState.OPEN
    assert with_forecast.best.action == CandidateAction(
        WindowState.CLOSED, BlindOpening(0)
    )
    assert with_forecast.best.forecast_load is not None
    assert with_forecast.best.thermal_cost_w == max(
        with_forecast.best.current_load.total_w,
        with_forecast.best.forecast_load.total_w,
    )


def test_movement_and_missing_forecast_penalties_are_explicitly_sensitive() -> None:
    """Allow caller-supplied penalties to retain a near-equivalent state."""
    current_action = CandidateAction(WindowState.CLOSED, BlindOpening(100))
    current = ThermalConditions(26, 25, 0)
    no_penalty = optimize_opening(
        request(current, current_action=current_action), ZERO_PENALTIES
    )
    penalized = optimize_opening(
        request(current, current_action=current_action),
        OptimizerSettings(
            blind_step_percent=10,
            window_movement_penalty_w=100,
            blind_full_travel_penalty_w=20,
            missing_forecast_change_penalty_w=100,
        ),
    )

    assert no_penalty.best.action != current_action
    assert penalized.best.action == current_action
    assert penalized.best.movement_cost_w == 0
    assert penalized.best.uncertainty_cost_w == 0


def test_heating_and_hold_objectives_cover_all_profile_intents() -> None:
    """Maximize heating below target and minimize absolute load inside hold band."""
    heating = optimize_opening(request(ThermalConditions(18, 25, 600)), ZERO_PENALTIES)
    hold_action = CandidateAction(WindowState.TILT, BlindOpening(50))
    hold = optimize_opening(
        request(
            ThermalConditions(23, 23, 0),
            current_action=hold_action,
        ),
        ZERO_PENALTIES,
    )

    assert heating.best.current_load.total_w > 0
    assert heating.best.thermal_cost_w == -heating.best.current_load.total_w
    assert hold.best.action == hold_action
    assert hold.best.total_cost_w == 0


def test_tie_breaking_is_repeatable_and_prefers_the_current_combination() -> None:
    """Return the same current action when every thermal score is equal."""
    current_action = CandidateAction(WindowState.TILT, BlindOpening(50))
    tied_request = request(ThermalConditions(23, 23, 0), current_action=current_action)

    first = optimize_opening(tied_request, ZERO_PENALTIES)
    second = optimize_opening(tied_request, ZERO_PENALTIES)

    assert first == second
    assert first.best.action == current_action


def test_optimizer_settings_and_current_state_are_validated() -> None:
    """Reject invalid resolution, penalties, and unsupported current tilt."""
    for values in (
        (0, 0, 0, 0),
        (30, 0, 0, 0),
        (True, 0, 0, 0),
        (10, -1, 0, 0),
        (10, 0, math.inf, 0),
        (10, 0, 0, math.nan),
    ):
        with pytest.raises(ValueError):
            OptimizerSettings(*values)

    with pytest.raises(ValueError):
        optimize_opening(
            request(
                ThermalConditions(23, 23, 0),
                current_action=CandidateAction(WindowState.TILT, BlindOpening(50)),
                supports_tilt=False,
            ),
            ZERO_PENALTIES,
        )
