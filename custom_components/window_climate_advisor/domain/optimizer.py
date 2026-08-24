"""Deterministic exhaustive optimizer for one opening and blind."""

from dataclasses import dataclass
from math import isfinite

from .models import BlindOpening, OpeningDimensions, ThermalConditions, WindowState
from .profiles import ComfortProfile
from .thermal import (
    DEFAULT_THERMAL_CALIBRATION,
    ThermalCalibration,
    ThermalLoad,
    candidate_thermal_load,
)

_STATE_RANK = {
    WindowState.CLOSED: 0,
    WindowState.TILT: 1,
    WindowState.OPEN: 2,
}


@dataclass(frozen=True, slots=True)
class CandidateAction:
    """One recommendation-only window and blind combination."""

    window_state: WindowState
    blind: BlindOpening


@dataclass(frozen=True, slots=True)
class OptimizerSettings:
    """Explicit candidate resolution and uncalibrated penalty inputs."""

    blind_step_percent: int
    window_movement_penalty_w: float
    blind_full_travel_penalty_w: float
    missing_forecast_change_penalty_w: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.blind_step_percent, bool)
            or not isinstance(self.blind_step_percent, int)
            or not 0 < self.blind_step_percent <= 100
            or 100 % self.blind_step_percent
        ):
            raise ValueError("blind step must be a positive integer divisor of 100")
        for name, value in (
            ("window_movement_penalty_w", self.window_movement_penalty_w),
            ("blind_full_travel_penalty_w", self.blind_full_travel_penalty_w),
            (
                "missing_forecast_change_penalty_w",
                self.missing_forecast_change_penalty_w,
            ),
        ):
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class OptimizationRequest:
    """Complete typed input for one coherent optimization."""

    dimensions: OpeningDimensions
    profile: ComfortProfile
    current_conditions: ThermalConditions
    forecast_conditions: ThermalConditions | None
    current_action: CandidateAction
    supports_tilt: bool


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    """Auditable score components for one candidate."""

    action: CandidateAction
    current_load: ThermalLoad
    forecast_load: ThermalLoad | None
    thermal_cost_w: float
    movement_cost_w: float
    uncertainty_cost_w: float
    total_cost_w: float


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """Winning candidate and exhaustive search size."""

    best: CandidateEvaluation
    current: CandidateEvaluation
    evaluated_candidates: int

    @property
    def avoided_cost_w(self) -> float:
        """Return cost avoided by the optimum relative to the current action."""
        return self.current.total_cost_w - self.best.total_cost_w


def enumerate_actions(
    settings: OptimizerSettings, *, supports_tilt: bool
) -> tuple[CandidateAction, ...]:
    """Return every candidate in a fixed deterministic order."""
    states = (
        (WindowState.CLOSED, WindowState.TILT, WindowState.OPEN)
        if supports_tilt
        else (WindowState.CLOSED, WindowState.OPEN)
    )
    return tuple(
        CandidateAction(state, BlindOpening(percent))
        for state in states
        for percent in range(0, 101, settings.blind_step_percent)
        if state is WindowState.CLOSED or percent > 0
    )


def _thermal_cost_w(
    load: ThermalLoad, temperature_c: float, profile: ComfortProfile
) -> float:
    """Return lower-is-better thermal cost for the horizon's comfort intent."""
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


def _evaluate(
    request: OptimizationRequest,
    action: CandidateAction,
    settings: OptimizerSettings,
    calibration: ThermalCalibration,
) -> CandidateEvaluation:
    """Evaluate one candidate without state or I/O."""
    current_load = candidate_thermal_load(
        request.dimensions,
        action.window_state,
        action.blind,
        request.current_conditions,
        calibration,
    )
    current_cost = _thermal_cost_w(
        current_load,
        request.current_conditions.indoor_temperature_c,
        request.profile,
    )

    forecast_load: ThermalLoad | None = None
    thermal_cost = current_cost
    if request.forecast_conditions is not None:
        forecast_load = candidate_thermal_load(
            request.dimensions,
            action.window_state,
            action.blind,
            request.forecast_conditions,
            calibration,
        )
        thermal_cost = max(
            current_cost,
            _thermal_cost_w(
                forecast_load,
                request.forecast_conditions.indoor_temperature_c,
                request.profile,
            ),
        )

    window_distance = abs(
        _STATE_RANK[action.window_state]
        - _STATE_RANK[request.current_action.window_state]
    )
    blind_travel = (
        abs(action.blind.percent - request.current_action.blind.percent) / 100
    )
    movement_cost = (
        window_distance * settings.window_movement_penalty_w
        + blind_travel * settings.blind_full_travel_penalty_w
    )
    uncertainty_cost = (
        settings.missing_forecast_change_penalty_w
        if request.forecast_conditions is None and action != request.current_action
        else 0.0
    )
    return CandidateEvaluation(
        action=action,
        current_load=current_load,
        forecast_load=forecast_load,
        thermal_cost_w=thermal_cost,
        movement_cost_w=movement_cost,
        uncertainty_cost_w=uncertainty_cost,
        total_cost_w=thermal_cost + movement_cost + uncertainty_cost,
    )


def optimize_opening(
    request: OptimizationRequest,
    settings: OptimizerSettings,
    calibration: ThermalCalibration = DEFAULT_THERMAL_CALIBRATION,
) -> OptimizationResult:
    """Exhaustively select the minimum deterministic recommendation score."""
    if (
        not request.supports_tilt
        and request.current_action.window_state is WindowState.TILT
    ):
        raise ValueError("current tilt state requires supports_tilt")

    evaluations = tuple(
        _evaluate(request, action, settings, calibration)
        for action in enumerate_actions(settings, supports_tilt=request.supports_tilt)
    )
    best = min(
        evaluations,
        key=lambda item: (
            item.total_cost_w,
            item.action != request.current_action,
            abs(
                _STATE_RANK[item.action.window_state]
                - _STATE_RANK[request.current_action.window_state]
            ),
            abs(item.action.blind.percent - request.current_action.blind.percent),
            _STATE_RANK[item.action.window_state],
            item.action.blind.percent,
        ),
    )
    current = _evaluate(request, request.current_action, settings, calibration)
    return OptimizationResult(
        best=best,
        current=current,
        evaluated_candidates=len(evaluations),
    )
