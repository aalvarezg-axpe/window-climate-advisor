"""Versioned multi-day replay comparison against characterized v4.17 actions."""

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import isfinite
from pathlib import Path
from typing import Any

import pytest

from custom_components.window_climate_advisor.application.state import (
    AdvisorState,
    advance_evaluation,
)
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
    optimize_opening,
)
from custom_components.window_climate_advisor.domain.policy import (
    ReasonCode,
    SafetyGeometry,
    SafetySnapshot,
    apply_weather_policy,
)
from custom_components.window_climate_advisor.domain.profiles import (
    ComfortProfile,
    Season,
)
from custom_components.window_climate_advisor.domain.state_machine import (
    OpeningStabilityState,
    StabilityInput,
    StabilitySettings,
)
from custom_components.window_climate_advisor.domain.thermal import (
    DEFAULT_THERMAL_CALIBRATION,
    ThermalCalibration,
    ThermalLoad,
    candidate_thermal_load,
)
from custom_components.window_climate_advisor.domain.ventilation import (
    AirflowCalibration,
)

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "replay" / "seasonal_v1.json"
CATALOG_PATH = (
    Path(__file__).parents[1] / "fixtures" / "migration" / "case_catalog.json"
)
OPENING_ID = "representative-opening"
HARD_SAFETY_REASONS = {
    ReasonCode.WIND_CLOSE,
    ReasonCode.RAIN_CLOSE,
    ReasonCode.RAIN_TILT_ONLY,
    ReasonCode.MISSING_SAFETY_DATA,
    ReasonCode.STALE_SAFETY_DATA,
}
STATE_RANK = {
    WindowState.CLOSED: 0,
    WindowState.TILT: 1,
    WindowState.OPEN: 2,
}


@dataclass(frozen=True, slots=True)
class ReplayMetrics:
    """Comparable deterministic metrics for one replay."""

    new_comfort_cost_wh: float
    legacy_comfort_cost_wh: float
    new_net_energy_wh: float
    legacy_net_energy_wh: float
    new_transitions: int
    legacy_transitions: int
    notification_candidates: int
    unstable_transitions: int
    safety_violations: int
    legacy_safety_violations: int
    recommendation_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Metrics plus observed stable actions by tagged segment."""

    metrics: ReplayMetrics
    tagged_actions: dict[str, set[CandidateAction]]


def fixture() -> dict[str, Any]:
    """Load the small, reviewable replay contract."""
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _action(value: dict[str, Any]) -> CandidateAction:
    return CandidateAction(WindowState(value["window"]), BlindOpening(value["blind"]))


def _conditions(value: dict[str, Any]) -> ThermalConditions:
    return ThermalConditions(
        value["indoor_c"],
        value["outdoor_c"],
        value["irradiance_w_m2"],
        value["wind_kmh"],
        value["gust_kmh"],
    )


def _comfort_cost(
    load: ThermalLoad, temperature_c: float, profile: ComfortProfile
) -> float:
    if (
        temperature_c <= profile.lower_c
        or temperature_c < profile.preconditioning_target_c - profile.hysteresis_c
    ):
        return -load.total_w
    if (
        temperature_c >= profile.upper_c
        or temperature_c > profile.preconditioning_target_c + profile.hysteresis_c
    ):
        return load.total_w
    return abs(load.total_w)


def _horizon_cost(
    action: CandidateAction,
    current: ThermalConditions,
    forecast: ThermalConditions | None,
    dimensions: OpeningDimensions,
    profile: ComfortProfile,
    calibration: ThermalCalibration,
) -> float:
    current_load = candidate_thermal_load(
        dimensions, action.window_state, action.blind, current, calibration
    )
    cost = _comfort_cost(current_load, current.indoor_temperature_c, profile)
    if forecast is None:
        return cost
    forecast_load = candidate_thermal_load(
        dimensions, action.window_state, action.blind, forecast, calibration
    )
    return max(
        cost,
        _comfort_cost(forecast_load, forecast.indoor_temperature_c, profile),
    )


def _violates_hard_safety(
    action: CandidateAction, reason: ReasonCode, allowed: WindowState
) -> bool:
    return (
        reason in HARD_SAFETY_REASONS
        and STATE_RANK[action.window_state] > STATE_RANK[allowed]
    )


def run_replay(
    data: dict[str, Any],
    scenario: dict[str, Any],
    calibration: ThermalCalibration = DEFAULT_THERMAL_CALIBRATION,
) -> ReplayResult:
    """Run one deterministic multi-day scenario through the accepted engine."""
    opening = data["opening"]
    dimensions = OpeningDimensions(opening["width_m"], opening["height_m"])
    geometry = SafetyGeometry(
        opening["facade_azimuth_deg"],
        opening["overhang_depth_m"],
        opening["overhang_gap_m"],
        opening["rain_protected"],
    )
    profile = ComfortProfile(**data["profiles"][scenario["season"]])
    optimizer_settings = OptimizerSettings(**data["optimizer"])
    stability_settings = StabilitySettings(**data["stability"])
    sample_duration_h = data["sample_minutes"] / 60
    initial = _action(scenario["initial"])
    state = AdvisorState(
        {
            OPENING_ID: OpeningStabilityState(
                initial.window_state,
                initial.blind,
            )
        }
    )
    previous_new = initial
    previous_legacy = initial
    now = datetime(2026, 1, 1, tzinfo=UTC)
    values = {
        "new_comfort": 0.0,
        "legacy_comfort": 0.0,
        "new_energy": 0.0,
        "legacy_energy": 0.0,
    }
    new_transitions = 0
    legacy_transitions = 0
    notification_candidates = 0
    unstable_transitions = 0
    safety_violations = 0
    legacy_safety_violations = 0
    recommendation_counts: Counter[str] = Counter()
    tagged_actions: dict[str, set[CandidateAction]] = {
        segment["id"]: set() for segment in scenario["segments"]
    }

    for _day in range(data["days"]):
        for segment in scenario["segments"]:
            current = _conditions(segment["current"])
            forecast = (
                _conditions(segment["forecast"])
                if segment["forecast"] is not None
                else None
            )
            legacy = _action(segment["legacy"])
            safety = segment["safety"]
            snapshot = SafetySnapshot(
                safety["rain_mm_h"],
                safety["gust_kmh"],
                safety["direction_deg"],
                safety["mean_direction_deg"],
            )
            for _sample in range(segment["samples"]):
                current_action = CandidateAction(
                    state.openings[OPENING_ID].window,
                    state.openings[OPENING_ID].blind,
                )
                optimized = optimize_opening(
                    OptimizationRequest(
                        dimensions,
                        profile,
                        current,
                        forecast,
                        current_action,
                        opening["supports_tilt"],
                    ),
                    optimizer_settings,
                    calibration,
                )
                policy = apply_weather_policy(
                    optimized,
                    snapshot,
                    geometry,
                    supports_tilt=opening["supports_tilt"],
                )
                transition = advance_evaluation(
                    state,
                    {
                        OPENING_ID: StabilityInput(
                            current_action,
                            optimized,
                            policy,
                            safety["gust_kmh"],
                        )
                    },
                    now,
                    stability_settings,
                )
                state = transition.state
                stable = state.openings[OPENING_ID]
                new = CandidateAction(stable.window, stable.blind)
                tagged_actions[segment["id"]].add(new)
                recommendation_counts[new.window_state.value] += 1
                changed = new != previous_new
                new_transitions += changed
                unstable_transitions += changed and _sample > 1
                legacy_transitions += legacy != previous_legacy
                notification_candidates += transition.notification_candidate is not None
                safety_violations += _violates_hard_safety(
                    new, policy.reason, policy.recommended_window_state
                )
                legacy_safety_violations += _violates_hard_safety(
                    legacy, policy.reason, policy.recommended_window_state
                )
                new_load = candidate_thermal_load(
                    dimensions,
                    new.window_state,
                    new.blind,
                    current,
                    calibration,
                )
                legacy_load = candidate_thermal_load(
                    dimensions,
                    legacy.window_state,
                    legacy.blind,
                    current,
                    calibration,
                )
                values["new_comfort"] += (
                    _horizon_cost(
                        new, current, forecast, dimensions, profile, calibration
                    )
                    * sample_duration_h
                )
                values["legacy_comfort"] += (
                    _horizon_cost(
                        legacy, current, forecast, dimensions, profile, calibration
                    )
                    * sample_duration_h
                )
                values["new_energy"] += new_load.total_w * sample_duration_h
                values["legacy_energy"] += legacy_load.total_w * sample_duration_h
                previous_new = new
                previous_legacy = legacy
                now += timedelta(minutes=data["sample_minutes"])

    metrics = ReplayMetrics(
        values["new_comfort"],
        values["legacy_comfort"],
        values["new_energy"],
        values["legacy_energy"],
        new_transitions,
        legacy_transitions,
        notification_candidates,
        unstable_transitions,
        safety_violations,
        legacy_safety_violations,
        tuple(sorted(recommendation_counts.items())),
    )
    return ReplayResult(metrics, tagged_actions)


def test_fixture_is_versioned_synthetic_and_covers_every_f04_08_case() -> None:
    """Keep provenance explicit and prevent silent scenario loss."""
    data = fixture()
    requirements = {
        requirement
        for scenario in data["scenarios"]
        for requirement in scenario["requirements"]
    }

    assert data["schema_version"] == 1
    assert "Synthetic" in data["provenance"]
    assert "not measured" in data["provenance"]
    assert data["days"] >= 2
    assert {scenario["season"] for scenario in data["scenarios"]} == {
        season.value for season in Season
    }
    assert requirements == {
        "summer_outdoor_25_c",
        "night_pre_cooling",
        "winter_solar_gain_above_24_c",
        "no_wind",
        "partial_solar_exposure",
        "adverse_forecast",
    }
    assert all(
        sum(segment["samples"] for segment in scenario["segments"]) == 48
        for scenario in data["scenarios"]
    )
    assert all(
        source.startswith("C") and len(source) == 4
        for scenario in data["scenarios"]
        for segment in scenario["segments"]
        for source in segment["legacy_source"]
    )
    catalog_ids = {
        case["id"]
        for case in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["cases"]
    }
    assert all(
        source in catalog_ids
        for scenario in data["scenarios"]
        for segment in scenario["segments"]
        for source in segment["legacy_source"]
    )


def test_replays_improve_aggregate_comfort_without_safety_or_alert_regression() -> None:
    """Compare both strategies through one physical metric implementation."""
    data = fixture()
    results = [run_replay(data, scenario) for scenario in data["scenarios"]]
    metrics = [result.metrics for result in results]

    assert sum(item.new_comfort_cost_wh for item in metrics) <= sum(
        item.legacy_comfort_cost_wh for item in metrics
    )
    assert all(item.safety_violations == 0 for item in metrics)
    assert all(item.legacy_safety_violations == 0 for item in metrics)
    assert all(item.unstable_transitions == 0 for item in metrics)
    assert all(item.notification_candidates == item.new_transitions for item in metrics)
    assert all(
        action.window_state is WindowState.CLOSED or action.blind.percent > 0
        for result in results
        for actions in result.tagged_actions.values()
        for action in actions
    )
    assert all(
        isfinite(value)
        for item in metrics
        for value in (
            item.new_comfort_cost_wh,
            item.legacy_comfort_cost_wh,
            item.new_net_energy_wh,
            item.legacy_net_energy_wh,
        )
    )
    assert all(
        sum(dict(item.recommendation_counts).values()) == 3 * 48 for item in metrics
    )


def test_required_boundaries_have_the_expected_stable_recommendations() -> None:
    """Exercise the six named F04-08 cases through production call paths."""
    data = fixture()
    results = {
        scenario["id"]: run_replay(data, scenario) for scenario in data["scenarios"]
    }

    summer = results["summer_preconditioning"].tagged_actions
    shoulder = results["shoulder_partial_exposure"].tagged_actions
    winter = results["winter_solar_gain"].tagged_actions
    assert any(
        action.window_state is WindowState.OPEN
        for action in summer["night_pre_cooling"]
    )
    assert any(
        action.window_state is WindowState.OPEN
        for action in summer["summer_outdoor_25_c"]
    )
    assert all(
        action.window_state is not WindowState.OPEN
        for action in summer["adverse_forecast"]
    )
    assert any(
        action.window_state is WindowState.OPEN for action in shoulder["no_wind"]
    )
    assert shoulder["partial_solar_exposure"] == {
        CandidateAction(WindowState.OPEN, BlindOpening(100))
    }
    assert (
        CandidateAction(WindowState.CLOSED, BlindOpening(100))
        in winter["winter_solar_gain_above_24_c"]
    )


@pytest.mark.parametrize(
    "calibration",
    [
        ThermalCalibration(
            closed_blind_solar_residual=0.05,
            airflow=AirflowCalibration(tilt_opening_fraction=0.08),
        ),
        ThermalCalibration(
            closed_blind_solar_residual=0.25,
            airflow=AirflowCalibration(tilt_opening_fraction=0.18),
        ),
    ],
)
def test_provisional_solar_and_tilt_assumptions_have_bounded_sensitivity(
    calibration: ThermalCalibration,
) -> None:
    """Vary the two provisional coefficients without weakening safety."""
    data = fixture()
    nominal = [run_replay(data, scenario) for scenario in data["scenarios"]]
    varied = [run_replay(data, scenario, calibration) for scenario in data["scenarios"]]

    assert all(item.metrics.safety_violations == 0 for item in varied)
    assert all(item.metrics.unstable_transitions == 0 for item in varied)
    assert all(
        item.metrics.notification_candidates == item.metrics.new_transitions
        for item in varied
    )
    nominal_transitions = sum(item.metrics.new_transitions for item in nominal)
    varied_transitions = sum(item.metrics.new_transitions for item in varied)
    assert abs(varied_transitions - nominal_transitions) <= 6
    assert all(
        isfinite(item.metrics.new_comfort_cost_wh)
        and isfinite(item.metrics.new_net_energy_wh)
        for item in varied
    )
