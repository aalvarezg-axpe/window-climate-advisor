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
from custom_components.window_climate_advisor.domain.profiles import (
    ComfortProfile,
    Season,
)

DIMENSIONS = OpeningDimensions(1.6, 1.2)
PROFILE = ComfortProfile(20, 25, 23, 0.5)
ZERO_PENALTIES = OptimizerSettings(10, 0, 0, 0)
DEFAULT_CURRENT_ACTION = CandidateAction(WindowState.CLOSED, BlindOpening(100))


def request(
    current: ThermalConditions,
    *,
    forecast: ThermalConditions | None = None,
    season: Season = Season.SHOULDER,
    current_action: CandidateAction = DEFAULT_CURRENT_ACTION,
    supports_tilt: bool = True,
    has_blind: bool = True,
) -> OptimizationRequest:
    """Build one concise typed request for tests."""
    return OptimizationRequest(
        dimensions=DIMENSIONS,
        profile=PROFILE,
        season=season,
        current_conditions=current,
        forecast_conditions=forecast,
        current_action=current_action,
        supports_tilt=supports_tilt,
        has_blind=has_blind,
    )


def test_candidate_space_is_exhaustive_and_tilt_is_constrained() -> None:
    """Enumerate all coherent candidates at the frozen 10% resolution."""
    with_tilt = enumerate_actions(ZERO_PENALTIES, supports_tilt=True)
    without_tilt = enumerate_actions(ZERO_PENALTIES, supports_tilt=False)

    assert len(with_tilt) == 31
    assert len(without_tilt) == 21
    assert {action.blind.percent for action in with_tilt} == set(range(0, 101, 10))
    assert all(
        action.window_state is WindowState.CLOSED or action.blind.percent > 0
        for action in with_tilt
    )
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
    assert cool.evaluated_candidates == solar.evaluated_candidates == 31
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


@pytest.mark.parametrize(
    ("season", "conditions", "expected_neutral", "expected_symmetric"),
    [
        (
            Season.SUMMER,
            ThermalConditions(18, 29, 500),
            CandidateAction(WindowState.CLOSED, BlindOpening(0)),
            CandidateAction(WindowState.OPEN, BlindOpening(100)),
        ),
        (
            Season.WINTER,
            ThermalConditions(26, 15, 0),
            CandidateAction(WindowState.CLOSED, BlindOpening(100)),
            CandidateAction(WindowState.OPEN, BlindOpening(100)),
        ),
    ],
)
def test_inactive_seasonal_direction_seeks_neutrality(
    season: Season,
    conditions: ThermalConditions,
    expected_neutral: CandidateAction,
    expected_symmetric: CandidateAction,
) -> None:
    """Stop unwanted seasonal gain or loss instead of reversing intent."""
    neutral = optimize_opening(
        request(conditions, season=season),
        ZERO_PENALTIES,
    )
    symmetric = optimize_opening(
        request(conditions, season=Season.SHOULDER),
        ZERO_PENALTIES,
    )

    assert neutral.best.action == expected_neutral
    assert symmetric.best.action == expected_symmetric
    assert neutral.best.thermal_cost_w == abs(neutral.best.current_load.total_w)
    assert abs(neutral.best.current_load.total_w) < abs(
        symmetric.best.current_load.total_w
    )


@pytest.mark.parametrize(
    ("season", "conditions"),
    [
        (Season.SUMMER, ThermalConditions(25, 20, 0)),
        (Season.WINTER, ThermalConditions(20, 25, 400)),
    ],
)
def test_active_seasonal_direction_still_uses_profile_boundaries(
    season: Season,
    conditions: ThermalConditions,
) -> None:
    """Keep Summer cooling and Winter heating active at exact outer bounds."""
    result = optimize_opening(
        request(conditions, season=season),
        ZERO_PENALTIES,
    )

    load = result.best.current_load.total_w
    assert result.best.action == CandidateAction(WindowState.OPEN, BlindOpening(100))
    assert result.best.thermal_cost_w == (load if season is Season.SUMMER else -load)


def test_summer_free_cools_until_lower_boundary_plus_hysteresis() -> None:
    """Use a cool low-sun interval before stopping at the Summer lower edge."""
    profile = ComfortProfile(24, 27, 25, 0.5)
    settings = OptimizerSettings(10, 20, 10, 30)
    current_action = CandidateAction(WindowState.TILT, BlindOpening(100))

    cooling = optimize_opening(
        OptimizationRequest(
            DIMENSIONS,
            profile,
            Season.SUMMER,
            ThermalConditions(24.7, 21.3, 30, 8, 12),
            None,
            current_action,
            True,
        ),
        settings,
    )
    stopped = optimize_opening(
        OptimizationRequest(
            DIMENSIONS,
            profile,
            Season.SUMMER,
            ThermalConditions(24.5, 21.3, 30, 8, 12),
            None,
            current_action,
            True,
        ),
        settings,
    )

    assert cooling.best.action == CandidateAction(WindowState.OPEN, BlindOpening(100))
    assert cooling.best.thermal_cost_w == cooling.best.current_load.total_w
    assert stopped.best.thermal_cost_w == abs(stopped.best.current_load.total_w)


@pytest.mark.parametrize(
    ("season", "current", "forecast"),
    [
        (
            Season.SUMMER,
            ThermalConditions(27, 20, 0),
            ThermalConditions(20.4, 29, 500),
        ),
        (
            Season.WINTER,
            ThermalConditions(19, 25, 400),
            ThermalConditions(26, 15, 0),
        ),
    ],
)
def test_forecast_uses_the_same_one_sided_seasonal_contract(
    season: Season,
    current: ThermalConditions,
    forecast: ThermalConditions,
) -> None:
    """Score an inactive forecast direction as neutral, not opposite intent."""
    result = optimize_opening(
        request(current, forecast=forecast, season=season),
        ZERO_PENALTIES,
    )

    assert result.best.forecast_load is not None
    current_cost = (
        result.best.current_load.total_w
        if season is Season.SUMMER
        else -result.best.current_load.total_w
    )
    assert result.best.thermal_cost_w == max(
        current_cost,
        abs(result.best.forecast_load.total_w),
    )


def test_tie_breaking_is_repeatable_and_prefers_the_current_combination() -> None:
    """Return the same current action when every thermal score is equal."""
    current_action = CandidateAction(WindowState.TILT, BlindOpening(50))
    tied_request = request(ThermalConditions(23, 23, 0), current_action=current_action)

    first = optimize_opening(tied_request, ZERO_PENALTIES)
    second = optimize_opening(tied_request, ZERO_PENALTIES)

    assert first == second
    assert first.best.action == current_action


def test_incoherent_current_action_is_compared_but_cannot_win() -> None:
    """Correct non-closed/0% observations without rejecting real current state."""
    current_action = CandidateAction(WindowState.TILT, BlindOpening(0))

    result = optimize_opening(
        request(ThermalConditions(23, 23, 0), current_action=current_action),
        ZERO_PENALTIES,
    )

    assert result.current.action == current_action
    assert result.best.action == CandidateAction(WindowState.TILT, BlindOpening(10))
    assert result.avoided_cost_w == 0


def test_opening_without_blind_only_evaluates_fully_open_blind_state() -> None:
    """Do not model solar protection that the configured opening lacks."""
    result = optimize_opening(
        request(ThermalConditions(27, 22, 1200), has_blind=False),
        ZERO_PENALTIES,
    )

    assert result.evaluated_candidates == 3
    assert result.best.action.blind == BlindOpening(100)


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
    with pytest.raises(ValueError):
        optimize_opening(
            request(
                ThermalConditions(23, 23, 0),
                current_action=CandidateAction(WindowState.CLOSED, BlindOpening(50)),
                has_blind=False,
            ),
            ZERO_PENALTIES,
        )
