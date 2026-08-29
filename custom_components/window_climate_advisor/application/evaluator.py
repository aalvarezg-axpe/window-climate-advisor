"""Pure orchestration of one coherent advisor snapshot."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from ..domain.models import (
    BlindOpening,
    OpeningDimensions,
    ThermalConditions,
    WindowState,
)
from ..domain.optimizer import (
    CandidateAction,
    OptimizationRequest,
    OptimizationResult,
    OptimizerSettings,
    optimize_opening,
)
from ..domain.policy import (
    PolicyResult,
    ReasonCode,
    Recommendation,
    SafetyGeometry,
    SafetySnapshot,
    apply_weather_policy,
    recommendation_for_state,
)
from ..domain.profiles import ComfortProfile, Season
from ..domain.state_machine import StabilityInput, StabilitySettings
from .state import AdvisorState, NotificationCandidate, advance_evaluation


class InputIssue(StrEnum):
    """Explicit reason why an opening cannot be evaluated."""

    CONFIGURATION_REQUIRED = "configuration_required"
    MISSING_INPUT = "missing_input"
    STALE_INPUT = "stale_input"


@dataclass(frozen=True, slots=True)
class OpeningSnapshot:
    """Typed adapter output for one opening."""

    opening_id: str
    dimensions: OpeningDimensions
    safety_geometry: SafetyGeometry
    supports_tilt: bool
    has_blind: bool
    current_action: CandidateAction
    current_conditions: ThermalConditions | None
    forecast_conditions: ThermalConditions | None
    safety: SafetySnapshot
    input_issue: InputIssue | None = None


@dataclass(frozen=True, slots=True)
class EvaluationSnapshot:
    """One dwelling snapshot assembled at a single instant."""

    season: Season | None
    profile: ComfortProfile | None
    openings: tuple[OpeningSnapshot, ...]

    def __post_init__(self) -> None:
        opening_ids = [opening.opening_id for opening in self.openings]
        if any(not opening_id for opening_id in opening_ids):
            raise ValueError("opening IDs must not be empty")
        if len(opening_ids) != len(set(opening_ids)):
            raise ValueError("opening IDs must be unique")
        if (self.season is None) != (self.profile is None):
            raise ValueError("season and profile must be present together")


@dataclass(frozen=True, slots=True)
class EvaluationSettings:
    """Accepted optimizer and stability settings."""

    optimizer: OptimizerSettings
    stability: StabilitySettings


@dataclass(frozen=True, slots=True)
class OpeningEvaluation:
    """Stable informational output for one opening."""

    recommendation: Recommendation
    recommended_window_state: WindowState
    recommended_blind: BlindOpening | None
    safe_to_open: bool
    reason: ReasonCode | InputIssue
    optimization: OptimizationResult | None


@dataclass(frozen=True, slots=True)
class AdvisorEvaluation:
    """Complete evaluation and restart-safe state."""

    evaluated_at: datetime
    season: Season | None
    openings: dict[str, OpeningEvaluation]
    state: AdvisorState
    notification_candidate: NotificationCandidate | None


def _degraded(issue: InputIssue) -> OpeningEvaluation:
    return OpeningEvaluation(
        Recommendation.DEGRADED,
        WindowState.CLOSED,
        None,
        False,
        issue,
        None,
    )


def evaluate_snapshot(
    snapshot: EvaluationSnapshot,
    previous_state: AdvisorState,
    now: datetime,
    settings: EvaluationSettings | None,
) -> AdvisorEvaluation:
    """Evaluate every ready opening and preserve explicit degradation."""
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("evaluation timestamp must be timezone-aware UTC")
    samples: dict[str, StabilityInput] = {}
    evaluated: dict[str, tuple[OpeningSnapshot, OptimizationResult, PolicyResult]] = {}
    results: dict[str, OpeningEvaluation] = {}
    profile = snapshot.profile

    for opening in snapshot.openings:
        if profile is None or settings is None:
            results[opening.opening_id] = _degraded(InputIssue.CONFIGURATION_REQUIRED)
            continue
        issue = opening.input_issue
        if issue is not None or opening.current_conditions is None:
            results[opening.opening_id] = _degraded(issue or InputIssue.MISSING_INPUT)
            continue

        optimized = optimize_opening(
            OptimizationRequest(
                opening.dimensions,
                profile,
                opening.current_conditions,
                opening.forecast_conditions,
                opening.current_action,
                opening.supports_tilt,
                opening.has_blind,
            ),
            settings.optimizer,
        )
        policy = apply_weather_policy(
            optimized,
            opening.safety,
            opening.safety_geometry,
            supports_tilt=opening.supports_tilt,
        )
        samples[opening.opening_id] = StabilityInput(
            opening.current_action,
            optimized,
            policy,
            opening.safety.gust_kmh,
        )
        evaluated[opening.opening_id] = opening, optimized, policy

    configured_ids = {opening.opening_id for opening in snapshot.openings}
    retained_state = AdvisorState(
        {
            opening_id: state
            for opening_id, state in previous_state.openings.items()
            if opening_id in configured_ids
        }
    )
    if settings is None:
        state = retained_state
        notification_candidate = None
    else:
        transition = advance_evaluation(
            retained_state, samples, now, settings.stability
        )
        state = transition.state
        notification_candidate = transition.notification_candidate
    for opening_id, (opening, optimized, policy) in evaluated.items():
        stable = state.openings[opening_id]
        recommendation = (
            Recommendation.DEGRADED
            if policy.recommendation is Recommendation.DEGRADED
            else recommendation_for_state(stable.window)
        )
        results[opening_id] = OpeningEvaluation(
            recommendation,
            stable.window,
            stable.blind if opening.has_blind else None,
            policy.safe_to_open,
            policy.reason,
            optimized,
        )

    return AdvisorEvaluation(
        now,
        snapshot.season,
        results,
        state,
        notification_candidate,
    )
