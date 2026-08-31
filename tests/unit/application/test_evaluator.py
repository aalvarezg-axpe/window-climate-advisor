"""Tests for pure dwelling snapshot orchestration."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.window_climate_advisor.application.evaluator import (
    EvaluationSettings,
    EvaluationSnapshot,
    InputIssue,
    OpeningSnapshot,
    evaluate_snapshot,
)
from custom_components.window_climate_advisor.application.state import AdvisorState
from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    OpeningDimensions,
    ThermalConditions,
    WindowState,
)
from custom_components.window_climate_advisor.domain.optimizer import (
    CandidateAction,
    OptimizerSettings,
)
from custom_components.window_climate_advisor.domain.policy import (
    ReasonCode,
    Recommendation,
    SafetyGeometry,
    SafetySnapshot,
)
from custom_components.window_climate_advisor.domain.profiles import (
    ComfortProfile,
    Season,
)
from custom_components.window_climate_advisor.domain.state_machine import (
    OpeningStabilityState,
    StabilitySettings,
)

NOW = datetime(2026, 8, 25, 10, tzinfo=UTC)
PROFILE = ComfortProfile(22, 25, 23, 0.5)
SETTINGS = EvaluationSettings(
    OptimizerSettings(10, 0, 0, 0),
    StabilitySettings(0, 0),
)
DEFAULT_SAFETY = SafetySnapshot(0, 0, 0)
DEFAULT_CONDITIONS = ThermalConditions(27, 20, 0)


def opening(
    current: WindowState = WindowState.CLOSED,
    *,
    safety: SafetySnapshot = DEFAULT_SAFETY,
    has_blind: bool = False,
    conditions: ThermalConditions | None = DEFAULT_CONDITIONS,
    issue: InputIssue | None = None,
) -> OpeningSnapshot:
    """Build one ready opening snapshot."""
    return OpeningSnapshot(
        "opening",
        OpeningDimensions(1.6, 1.2),
        SafetyGeometry(0, 0.5, 0.5, True),
        True,
        has_blind,
        CandidateAction(current, BlindOpening(100)),
        conditions,
        None,
        safety,
        issue,
    )


def snapshot(
    item: OpeningSnapshot,
    *,
    configured: bool = True,
    season: Season = Season.SUMMER,
) -> EvaluationSnapshot:
    """Build one seasonal snapshot or an explicitly incomplete configuration."""
    return EvaluationSnapshot(
        season if configured else None,
        PROFILE if configured else None,
        (item,),
    )


def test_stability_publishes_resolved_target_then_accepted_change() -> None:
    """Keep the stable target visible while gating an improvement."""
    item = opening()

    started = evaluate_snapshot(snapshot(item), AdvisorState(), NOW, SETTINGS)
    accepted = evaluate_snapshot(
        snapshot(item),
        started.state,
        NOW + timedelta(minutes=10),
        SETTINGS,
    )

    assert started.openings["opening"].recommendation is Recommendation.CLOSE
    assert started.notification_candidate is None
    assert accepted.openings["opening"].recommendation is Recommendation.OPEN
    assert accepted.openings["opening"].recommended_blind is None
    assert accepted.notification_candidate is not None


@pytest.mark.parametrize(
    ("safety", "expected", "state"),
    [
        (SafetySnapshot(0, 45, 0), Recommendation.CLOSE, WindowState.CLOSED),
        (SafetySnapshot(0, 20, 0), Recommendation.TILT, WindowState.TILT),
    ],
)
def test_weather_restrictions_publish_stable_close_or_tilt(
    safety: SafetySnapshot,
    expected: Recommendation,
    state: WindowState,
) -> None:
    """Preserve absolute weather policy through application orchestration."""
    result = evaluate_snapshot(
        snapshot(opening(WindowState.OPEN, safety=safety)),
        AdvisorState(
            {"opening": OpeningStabilityState(WindowState.OPEN, BlindOpening(100))}
        ),
        NOW,
        SETTINGS,
    )

    assert result.openings["opening"].recommendation is expected
    assert result.openings["opening"].recommended_window_state is state


def test_evaluator_delivers_explicit_season_to_optimizer() -> None:
    """Keep Summer neutral where the same profile lets Winter seek heat."""
    item = opening(conditions=ThermalConditions(18, 25, 600))

    summer = evaluate_snapshot(snapshot(item), AdvisorState(), NOW, SETTINGS)
    winter = evaluate_snapshot(
        snapshot(item, season=Season.WINTER),
        AdvisorState(),
        NOW,
        SETTINGS,
    )

    summer_result = summer.openings["opening"].optimization
    winter_result = winter.openings["opening"].optimization
    assert summer_result is not None
    assert winter_result is not None
    assert summer_result.best.thermal_cost_w == abs(
        summer_result.best.current_load.total_w
    )
    assert winter_result.best.thermal_cost_w == -winter_result.best.current_load.total_w


def test_summer_non_open_targets_publish_concrete_thermal_causes() -> None:
    """Explain the winning Summer constraint instead of saying optimizer."""
    cases = (
        (
            replace(
                opening(has_blind=True, conditions=ThermalConditions(27, 25, 500)),
                current_action=CandidateAction(
                    WindowState.CLOSED,
                    BlindOpening(0),
                ),
            ),
            SETTINGS,
            ReasonCode.SOLAR_GAIN,
        ),
        (
            opening(conditions=ThermalConditions(27, 30, 0)),
            SETTINGS,
            ReasonCode.OUTDOOR_NOT_COOLER,
        ),
        (
            opening(conditions=ThermalConditions(23, 22.9, 0)),
            EvaluationSettings(
                OptimizerSettings(10, 1_000, 1_000, 1_000),
                StabilitySettings(0, 0),
            ),
            ReasonCode.STABILITY_MARGIN,
        ),
        (
            opening(conditions=ThermalConditions(22.5, 15, 0)),
            SETTINGS,
            ReasonCode.SUMMER_COMFORT_FLOOR,
        ),
    )

    for item, settings, expected in cases:
        profile = (
            ComfortProfile(22, 25, 23, 0.5)
            if expected is ReasonCode.SUMMER_COMFORT_FLOOR
            else PROFILE
        )
        result = evaluate_snapshot(
            EvaluationSnapshot(Season.SUMMER, profile, (item,)),
            AdvisorState(),
            NOW,
            settings,
        )

        assert result.openings["opening"].reason is expected


def test_pending_summer_opening_has_an_explicit_confirmation_reason() -> None:
    """Explain a retained non-open state while a better opening awaits stability."""
    result = evaluate_snapshot(snapshot(opening()), AdvisorState(), NOW, SETTINGS)

    assert result.openings["opening"].recommendation is Recommendation.CLOSE
    assert result.openings["opening"].reason is ReasonCode.STABILITY_CONFIRMATION


def test_missing_safety_and_thermal_inputs_degrade_without_favourable_defaults() -> (
    None
):
    """Expose both policy and adapter degradation while retaining valid state."""
    missing_safety = evaluate_snapshot(
        snapshot(opening(safety=SafetySnapshot(0, None, 0))),
        AdvisorState(),
        NOW,
        SETTINGS,
    )
    stale_thermal = evaluate_snapshot(
        snapshot(opening(conditions=None, issue=InputIssue.STALE_INPUT)),
        missing_safety.state,
        NOW,
        SETTINGS,
    )

    assert missing_safety.openings["opening"].recommendation is Recommendation.DEGRADED
    assert missing_safety.openings["opening"].reason is ReasonCode.MISSING_SAFETY_DATA
    assert not missing_safety.openings["opening"].safe_to_open
    assert stale_thermal.openings["opening"].reason is InputIssue.STALE_INPUT
    assert stale_thermal.openings["opening"].optimization is None


def test_incomplete_options_degrade_and_removed_openings_are_pruned() -> None:
    """Keep the entry loaded for UI repair without retaining removed state."""
    previous = AdvisorState(
        {
            "opening": OpeningStabilityState(WindowState.OPEN, BlindOpening(100)),
            "removed": OpeningStabilityState(WindowState.TILT, BlindOpening(50)),
        }
    )

    result = evaluate_snapshot(
        snapshot(opening(), configured=False), previous, NOW, None
    )

    assert result.season is None
    assert result.openings["opening"].reason is InputIssue.CONFIGURATION_REQUIRED
    assert set(result.state.openings) == {"opening"}


def test_snapshot_identity_and_utc_contract_are_strict() -> None:
    """Reject inconsistent identity, profile, and time boundaries."""
    item = opening()
    with pytest.raises(ValueError, match="empty"):
        EvaluationSnapshot(
            Season.SUMMER,
            PROFILE,
            (replace(item, opening_id=""),),
        )
    with pytest.raises(ValueError, match="unique"):
        EvaluationSnapshot(Season.SUMMER, PROFILE, (item, item))
    with pytest.raises(ValueError, match="together"):
        EvaluationSnapshot(Season.SUMMER, None, (item,))
    with pytest.raises(ValueError, match="UTC"):
        evaluate_snapshot(
            snapshot(item),
            AdvisorState(),
            datetime(2026, 8, 25, 10),
            SETTINGS,
        )
