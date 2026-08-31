"""Pure hysteresis and stability for recommendation changes."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from .models import BlindOpening, WindowState
from .optimizer import CandidateAction, OptimizationResult
from .policy import PolicyResult, ReasonCode

_WINDOW_RANK = {
    WindowState.CLOSED: 0,
    WindowState.TILT: 1,
    WindowState.OPEN: 2,
}
_IMMEDIATE_REASONS = {
    ReasonCode.WIND_CLOSE,
    ReasonCode.RAIN_CLOSE,
    ReasonCode.RAIN_TILT_ONLY,
    ReasonCode.MISSING_SAFETY_DATA,
    ReasonCode.STALE_SAFETY_DATA,
    ReasonCode.OUTDOOR_NOT_COOLER,
}
_OPTIMIZER_REASONS = {
    ReasonCode.OPTIMIZER,
    ReasonCode.SUMMER_COMFORT_FLOOR,
    ReasonCode.SOLAR_GAIN,
    ReasonCode.STABILITY_MARGIN,
}


class BlindDirection(StrEnum):
    """Physical blind movement category, independent of exact percentage."""

    LOWER = "lower"
    RAISE = "raise"


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamps must be timezone-aware UTC")


@dataclass(frozen=True, slots=True)
class PendingWindow:
    """Window candidate awaiting continuous confirmation."""

    target: WindowState
    since: datetime

    def __post_init__(self) -> None:
        _require_utc(self.since)


@dataclass(frozen=True, slots=True)
class PendingBlind:
    """Blind movement candidate awaiting continuous confirmation."""

    direction: BlindDirection
    target: BlindOpening
    since: datetime

    def __post_init__(self) -> None:
        _require_utc(self.since)


@dataclass(frozen=True, slots=True)
class OpeningStabilityState:
    """Restart-safe physical-category memory for one opening."""

    window: WindowState
    blind: BlindOpening
    blind_direction: BlindDirection | None = None
    pending_window: PendingWindow | None = None
    pending_blind: PendingBlind | None = None


@dataclass(frozen=True, slots=True)
class StabilitySettings:
    """Explicit benefit/deadband settings plus inherited stability periods."""

    minimum_benefit_w: float
    blind_deadband_percent: float
    marginal_wind_delay: timedelta = timedelta(minutes=5)
    opening_improvement_delay: timedelta = timedelta(minutes=10)
    blind_delay: timedelta = timedelta(minutes=15)
    immediate_wind_gust_kmh: float = 20

    def __post_init__(self) -> None:
        if not isfinite(self.minimum_benefit_w) or self.minimum_benefit_w < 0:
            raise ValueError("minimum_benefit_w must be finite and non-negative")
        if (
            not isfinite(self.blind_deadband_percent)
            or not 0 <= self.blind_deadband_percent <= 100
        ):
            raise ValueError("blind_deadband_percent must be within [0, 100]")
        if any(
            delay <= timedelta(0)
            for delay in (
                self.marginal_wind_delay,
                self.opening_improvement_delay,
                self.blind_delay,
            )
        ):
            raise ValueError("stability delays must be positive")
        if (
            not isfinite(self.immediate_wind_gust_kmh)
            or self.immediate_wind_gust_kmh < 0
        ):
            raise ValueError("immediate_wind_gust_kmh must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class StabilityInput:
    """One evaluated recommendation and the observations needed for stability."""

    current_action: CandidateAction
    optimized: OptimizationResult
    policy: PolicyResult
    gust_kmh: float | None
    blind_target_required: bool = False

    def __post_init__(self) -> None:
        if self.gust_kmh is not None and (
            not isfinite(self.gust_kmh) or self.gust_kmh < 0
        ):
            raise ValueError("gust_kmh must be finite and non-negative when present")


@dataclass(frozen=True, slots=True)
class OpeningTransition:
    """Updated memory and stable changes eligible for grouping."""

    state: OpeningStabilityState
    window_changed: bool
    blind_changed: bool

    @property
    def changed(self) -> bool:
        """Return whether a stable physical recommendation changed."""
        return self.window_changed or self.blind_changed


def initial_stability_state(current: CandidateAction) -> OpeningStabilityState:
    """Initialize memory from the observed action without emitting a change."""
    return OpeningStabilityState(current.window_state, current.blind)


def _window_delay(
    state: OpeningStabilityState,
    sample: StabilityInput,
    settings: StabilitySettings,
) -> timedelta:
    reason = sample.policy.reason
    if reason in _IMMEDIATE_REASONS:
        delay = timedelta(0)
    elif reason is ReasonCode.WIND_TILT_ONLY:
        delay = (
            timedelta(0)
            if sample.gust_kmh is not None
            and sample.gust_kmh >= settings.immediate_wind_gust_kmh
            else settings.marginal_wind_delay
        )
    elif (
        _WINDOW_RANK[sample.policy.recommended_window_state]
        > _WINDOW_RANK[state.window]
    ):
        delay = settings.opening_improvement_delay
    else:
        delay = timedelta(0)

    blind_target = sample.policy.recommended_blind
    if (
        reason in _OPTIMIZER_REASONS
        and sample.policy.recommended_window_state is not state.window
        and abs(blind_target.percent - state.blind.percent)
        > settings.blind_deadband_percent
        and _blind_direction(state.blind, blind_target) is not state.blind_direction
    ):
        delay = max(delay, settings.blind_delay)
    return delay


def _advance_window(
    state: OpeningStabilityState,
    sample: StabilityInput,
    now: datetime,
    settings: StabilitySettings,
) -> tuple[OpeningStabilityState, bool]:
    target = sample.policy.recommended_window_state
    if (
        sample.policy.reason in _OPTIMIZER_REASONS
        and sample.optimized.avoided_cost_w < settings.minimum_benefit_w
        and not (
            state.window is not WindowState.CLOSED
            and state.blind.percent == 0
            and target is WindowState.CLOSED
        )
    ):
        target = state.window
    if target is state.window:
        return replace(state, pending_window=None), False

    delay = _window_delay(state, sample, settings)
    if (
        state.window is WindowState.CLOSED
        and state.blind.percent == 0
        and target is not WindowState.CLOSED
    ):
        delay = max(delay, settings.blind_delay)
    if delay == timedelta(0):
        return replace(state, window=target, pending_window=None), True
    pending = state.pending_window
    if pending is None or pending.target is not target:
        return replace(state, pending_window=PendingWindow(target, now)), False
    if now < pending.since:
        raise ValueError("now cannot precede a pending window timestamp")
    if now - pending.since < delay:
        return state, False
    return replace(state, window=target, pending_window=None), True


def _blind_direction(current: BlindOpening, target: BlindOpening) -> BlindDirection:
    return (
        BlindDirection.RAISE
        if target.percent > current.percent
        else BlindDirection.LOWER
    )


def _advance_blind(
    state: OpeningStabilityState,
    sample: StabilityInput,
    now: datetime,
    settings: StabilitySettings,
) -> tuple[OpeningStabilityState, bool]:
    target = sample.policy.recommended_blind
    if (
        sample.optimized.avoided_cost_w < settings.minimum_benefit_w
        and not sample.blind_target_required
        and not (state.window is not WindowState.CLOSED and state.blind.percent == 0)
    ):
        target = state.blind
    direction = _blind_direction(state.blind, target)
    if state.window is not WindowState.CLOSED and state.blind.percent == 0:
        return replace(
            state,
            blind=target,
            blind_direction=direction,
            pending_blind=None,
        ), True
    if abs(target.percent - state.blind.percent) <= settings.blind_deadband_percent:
        return replace(state, pending_blind=None), False
    if direction is state.blind_direction:
        return replace(state, blind=target, pending_blind=None), True

    pending = state.pending_blind
    if pending is None or pending.direction is not direction:
        return replace(
            state,
            pending_blind=PendingBlind(direction, target, now),
        ), False
    if now < pending.since:
        raise ValueError("now cannot precede a pending blind timestamp")
    if now - pending.since < settings.blind_delay:
        return replace(
            state,
            pending_blind=replace(pending, target=target),
        ), False
    return replace(
        state,
        blind=target,
        blind_direction=direction,
        pending_blind=None,
    ), True


def advance_opening(
    state: OpeningStabilityState,
    sample: StabilityInput,
    now: datetime,
    settings: StabilitySettings,
) -> OpeningTransition:
    """Advance one opening without I/O or notification delivery."""
    _require_utc(now)
    after_window, window_changed = _advance_window(state, sample, now, settings)
    after_blind, blind_changed = _advance_blind(after_window, sample, now, settings)
    return OpeningTransition(after_blind, window_changed, blind_changed)
