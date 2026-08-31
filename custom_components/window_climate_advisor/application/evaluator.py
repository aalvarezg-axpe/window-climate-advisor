"""Pure orchestration of one coherent advisor snapshot."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

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
from ..domain.thermal import candidate_thermal_load
from .state import AdvisorState, NotificationCandidate, advance_evaluation


class InputIssue(StrEnum):
    """Explicit reason why an opening cannot be evaluated."""

    CONFIGURATION_REQUIRED = "configuration_required"
    MISSING_INPUT = "missing_input"
    STALE_INPUT = "stale_input"
    MISSING_ROOM_TEMPERATURE = "missing_room_temperature"
    STALE_ROOM_TEMPERATURE = "stale_room_temperature"


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
    direct_sun_on_opening: bool = True


@dataclass(frozen=True, slots=True)
class EvaluationSnapshot:
    """One dwelling snapshot assembled at a single instant."""

    season: Season | None
    profile: ComfortProfile | None
    openings: tuple[OpeningSnapshot, ...]
    today_forecast_max_c: float | None = None
    dwelling_occupied: bool = True

    def __post_init__(self) -> None:
        opening_ids = [opening.opening_id for opening in self.openings]
        if any(not opening_id for opening_id in opening_ids):
            raise ValueError("opening IDs must not be empty")
        if len(opening_ids) != len(set(opening_ids)):
            raise ValueError("opening IDs must be unique")
        if (self.season is None) != (self.profile is None):
            raise ValueError("season and profile must be present together")
        if self.today_forecast_max_c is not None and not isfinite(
            self.today_forecast_max_c
        ):
            raise ValueError("today's forecast maximum must be finite")
        if not isinstance(self.dwelling_occupied, bool):
            raise ValueError("dwelling occupancy must be boolean")


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


def _optimizer_reason(
    opening: OpeningSnapshot,
    optimized: OptimizationResult,
    profile: ComfortProfile,
    season: Season,
    settings: OptimizerSettings,
    diffuse_blind_protection: bool,
) -> ReasonCode:
    """Return one concrete cause for a Summer target below full opening."""
    conditions = opening.current_conditions
    if diffuse_blind_protection and optimized.best.action.blind.percent < 100:
        return ReasonCode.DIFFUSE_HEAT_PROTECTION
    if (
        season is not Season.SUMMER
        or optimized.best.action.window_state is WindowState.OPEN
        or conditions is None
    ):
        return ReasonCode.OPTIMIZER
    if conditions.indoor_temperature_c <= profile.lower_c + profile.hysteresis_c:
        return ReasonCode.SUMMER_COMFORT_FLOOR
    if conditions.outdoor_temperature_c >= conditions.indoor_temperature_c:
        return ReasonCode.OUTDOOR_NOT_COOLER

    open_blind = BlindOpening(
        max(optimized.best.action.blind.percent, settings.blind_step_percent)
    )
    open_load = candidate_thermal_load(
        opening.dimensions,
        WindowState.OPEN,
        open_blind,
        conditions,
    )
    if open_load.solar_w >= abs(open_load.conduction_w + open_load.ventilation_w):
        return ReasonCode.SOLAR_GAIN
    return ReasonCode.STABILITY_MARGIN


def _allow_diffuse_blind_protection(
    snapshot: EvaluationSnapshot,
    opening: OpeningSnapshot,
) -> bool:
    """Unlock diffuse shading only for bounded Summer heat-risk scenarios."""
    profile = snapshot.profile
    conditions = opening.current_conditions
    if (
        snapshot.season is not Season.SUMMER
        or profile is None
        or conditions is None
        or opening.direct_sun_on_opening
    ):
        return False
    heat_risk = conditions.outdoor_temperature_c >= profile.upper_c or (
        snapshot.today_forecast_max_c is not None
        and snapshot.today_forecast_max_c >= profile.upper_c
    )
    protection_floor_c = (
        profile.upper_c if snapshot.dwelling_occupied else profile.lower_c
    )
    return heat_risk and conditions.indoor_temperature_c >= protection_floor_c


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
    season = snapshot.season

    for opening in snapshot.openings:
        if profile is None or season is None or settings is None:
            results[opening.opening_id] = _degraded(InputIssue.CONFIGURATION_REQUIRED)
            continue
        issue = opening.input_issue
        if issue is not None or opening.current_conditions is None:
            results[opening.opening_id] = _degraded(issue or InputIssue.MISSING_INPUT)
            continue

        diffuse_blind_protection = _allow_diffuse_blind_protection(snapshot, opening)
        optimized = optimize_opening(
            OptimizationRequest(
                opening.dimensions,
                profile,
                season,
                opening.current_conditions,
                opening.forecast_conditions,
                opening.current_action,
                opening.supports_tilt,
                opening.has_blind,
                opening.direct_sun_on_opening,
                diffuse_blind_protection,
            ),
            settings.optimizer,
        )
        policy = apply_weather_policy(
            optimized,
            opening.safety,
            opening.safety_geometry,
            supports_tilt=opening.supports_tilt,
        )
        if policy.reason is ReasonCode.OPTIMIZER:
            policy = replace(
                policy,
                reason=_optimizer_reason(
                    opening,
                    optimized,
                    profile,
                    season,
                    settings.optimizer,
                    diffuse_blind_protection,
                ),
            )
        samples[opening.opening_id] = StabilityInput(
            opening.current_action,
            optimized,
            policy,
            opening.safety.gust_kmh,
            blind_target_required=(
                season is Season.SUMMER
                and opening.has_blind
                and not opening.direct_sun_on_opening
                and not diffuse_blind_protection
            ),
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
        reason = policy.reason
        if (
            season is Season.SUMMER
            and stable.window is not WindowState.OPEN
            and policy.recommended_window_state is WindowState.OPEN
        ):
            reason = ReasonCode.STABILITY_CONFIRMATION
        results[opening_id] = OpeningEvaluation(
            recommendation,
            stable.window,
            stable.blind if opening.has_blind else None,
            policy.safe_to_open,
            reason,
            optimized,
        )

    return AdvisorEvaluation(
        now,
        snapshot.season,
        results,
        state,
        notification_candidate,
    )
