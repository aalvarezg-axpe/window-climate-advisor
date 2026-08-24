"""Tests for recommendation-only weather safety policy."""

import math

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
    SafetyGeometry,
    SafetySettings,
    SafetySnapshot,
    apply_weather_policy,
)
from custom_components.window_climate_advisor.domain.thermal import ThermalLoad

CURRENT_CLOSED = CandidateAction(WindowState.CLOSED, BlindOpening(100))
GEOMETRY = SafetyGeometry(0, 0.5, 0.5, True)
DRY = SafetySnapshot(0, 5, 0, 20)


def optimized(state: WindowState, blind_percent: float = 60) -> OptimizationResult:
    """Return a minimal real optimization result for the policy boundary."""
    action = CandidateAction(state, BlindOpening(blind_percent))
    load = ThermalLoad(0, 0, 0)
    evaluation = CandidateEvaluation(action, load, None, 0, 0, 0, 0)
    return OptimizationResult(evaluation, evaluation, 33)


def test_stale_or_missing_safety_data_fails_closed_as_degraded() -> None:
    """Never turn unknown or stale observations into favourable weather."""
    stale = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(0, 5, 0, stale=True),
        GEOMETRY,
        supports_tilt=True,
    )
    assert stale == PolicyResult(
        Recommendation.DEGRADED,
        WindowState.CLOSED,
        BlindOpening(60),
        False,
        ReasonCode.STALE_SAFETY_DATA,
    )

    for snapshot in (
        SafetySnapshot(None, 5, 0),
        SafetySnapshot(0, None, 0),
        SafetySnapshot(0, 5, None, None),
    ):
        result = apply_weather_policy(
            optimized(WindowState.OPEN),
            CURRENT_CLOSED,
            snapshot,
            GEOMETRY,
            supports_tilt=True,
        )
        assert result.recommendation is Recommendation.DEGRADED
        assert result.reason is ReasonCode.MISSING_SAFETY_DATA
        assert not result.safe_to_open


def test_absolute_gust_limit_closes_before_any_thermal_result() -> None:
    """Close at 45 km/h even when the optimizer strongly prefers open."""
    result = apply_weather_policy(
        optimized(WindowState.OPEN, 80),
        CURRENT_CLOSED,
        SafetySnapshot(0, 45, 180),
        GEOMETRY,
        supports_tilt=True,
    )

    assert result.recommendation is Recommendation.CLOSE
    assert result.recommended_window_state is WindowState.CLOSED
    assert result.recommended_blind == BlindOpening(80)
    assert result.reason is ReasonCode.WIND_CLOSE


def test_worst_direction_and_continuous_limits_restrict_open_to_tilt_or_close() -> None:
    """Use the nearer direction and the continuous façade exposure limits."""
    open_safe = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(0, 9.9, 105),
        GEOMETRY,
        supports_tilt=True,
    )
    tilt_only = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(0, 15, 105, 0),
        GEOMETRY,
        supports_tilt=True,
    )
    frontal_close = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(0, 35, 0),
        GEOMETRY,
        supports_tilt=True,
    )
    leeward_tilt = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(0, 40, 105),
        GEOMETRY,
        supports_tilt=True,
    )

    assert open_safe.recommendation is Recommendation.OPEN
    assert tilt_only.reason is ReasonCode.WIND_TILT_ONLY
    assert tilt_only.recommended_window_state is WindowState.TILT
    assert frontal_close.reason is ReasonCode.WIND_CLOSE
    assert leeward_tilt.reason is ReasonCode.WIND_TILT_ONLY


def test_wind_restriction_closes_when_tilt_is_not_supported() -> None:
    """Do not invent a tilt capability for an opening that lacks it."""
    result = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(0, 15, 0),
        GEOMETRY,
        supports_tilt=False,
    )

    assert result.recommendation is Recommendation.CLOSE
    assert result.reason is ReasonCode.WIND_CLOSE


def test_light_rain_allows_only_a_geometrically_protected_tilt() -> None:
    """Apply the overhang projection before retaining thermal ventilation."""
    protected = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(1.2, 5, 0),
        GEOMETRY,
        supports_tilt=True,
    )
    leeward = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        SafetySnapshot(1, 5, 105),
        GEOMETRY,
        supports_tilt=True,
    )

    assert protected.recommendation is Recommendation.TILT
    assert protected.reason is ReasonCode.RAIN_TILT_ONLY
    assert protected.safe_to_open
    assert leeward.recommendation is Recommendation.TILT


@pytest.mark.parametrize(
    ("snapshot", "geometry", "supports_tilt"),
    [
        (SafetySnapshot(1.21, 5, 0), GEOMETRY, True),
        (SafetySnapshot(1, 18, 0), GEOMETRY, True),
        (SafetySnapshot(1, 5, 0), SafetyGeometry(0, 0.5, 0.5, False), True),
        (SafetySnapshot(1, 5, 0), GEOMETRY, False),
    ],
)
def test_heavy_unprotected_or_unsupported_rain_closes(
    snapshot: SafetySnapshot,
    geometry: SafetyGeometry,
    supports_tilt: bool,
) -> None:
    """Close when any accepted rain-tilt condition is absent."""
    result = apply_weather_policy(
        optimized(WindowState.OPEN),
        CURRENT_CLOSED,
        snapshot,
        geometry,
        supports_tilt=supports_tilt,
    )

    assert result.recommendation is Recommendation.CLOSE
    assert result.reason is ReasonCode.RAIN_CLOSE


def test_rain_does_not_make_a_closed_thermal_candidate_more_open() -> None:
    """Safety is a restriction and can never improve the optimizer action."""
    result = apply_weather_policy(
        optimized(WindowState.CLOSED),
        CURRENT_CLOSED,
        SafetySnapshot(1, 5, 0),
        GEOMETRY,
        supports_tilt=True,
    )

    assert result.recommendation is Recommendation.CLOSE
    assert result.recommended_window_state is WindowState.CLOSED


@pytest.mark.parametrize(
    ("optimized_state", "current_state", "expected"),
    [
        (WindowState.OPEN, WindowState.CLOSED, Recommendation.OPEN),
        (WindowState.TILT, WindowState.CLOSED, Recommendation.TILT),
        (WindowState.CLOSED, WindowState.OPEN, Recommendation.CLOSE),
        (WindowState.CLOSED, WindowState.CLOSED, Recommendation.HOLD),
    ],
)
def test_safe_weather_maps_optimizer_state_to_typed_recommendation(
    optimized_state: WindowState,
    current_state: WindowState,
    expected: Recommendation,
) -> None:
    """Map normal optimizer output without legacy letter codes."""
    result = apply_weather_policy(
        optimized(optimized_state),
        CandidateAction(current_state, BlindOpening(100)),
        DRY,
        GEOMETRY,
        supports_tilt=True,
    )

    assert result.recommendation is expected
    assert result.reason is ReasonCode.OPTIMIZER
    assert result.safe_to_open


def test_policy_inputs_and_settings_enforce_physical_bounds() -> None:
    """Reject malformed weather, geometry, and threshold relationships."""
    for snapshot in (
        (-1, 5, 0, None),
        (0, math.inf, 0, None),
        (0, 5, -1, None),
        (0, 5, 360, None),
        (0, 5, 0, math.nan),
    ):
        with pytest.raises(ValueError):
            SafetySnapshot(*snapshot)

    for geometry in (
        (360, 0.5, 0.5, True),
        (0, -1, 0.5, True),
        (0, 0.5, math.inf, True),
    ):
        with pytest.raises(ValueError):
            SafetyGeometry(*geometry)

    for kwargs in (
        {"absolute_close_gust_kmh": -1},
        {"full_open_frontal_kmh": 21},
        {"tilt_frontal_kmh": 46},
        {"direction_margin_deg": 91},
        {"light_rain_max_mm_h": 0},
        {"rain_vertical_speed_kmh": 0},
        {"tilt_opening_height_m": 0},
    ):
        with pytest.raises(ValueError):
            SafetySettings(**kwargs)
