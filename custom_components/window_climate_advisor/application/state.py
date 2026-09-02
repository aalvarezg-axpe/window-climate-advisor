"""Versioned advisor state and grouped transition candidates."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from ..domain.models import BlindOpening, WindowState
from ..domain.policy import ReasonCode
from ..domain.state_machine import (
    BlindDirection,
    OpeningStabilityState,
    PendingBlind,
    PendingWindow,
    StabilityInput,
    StabilitySettings,
    advance_opening,
    initial_stability_state,
)

STATE_VERSION = 2


@dataclass(frozen=True, slots=True)
class AdvisorState:
    """Restart-safe state for all known openings."""

    openings: dict[str, OpeningStabilityState] = field(default_factory=dict)
    day_started_on: date | None = None

    def __post_init__(self) -> None:
        if any(
            not isinstance(opening_id, str) or not opening_id
            for opening_id in self.openings
        ):
            raise ValueError("opening IDs must be non-empty strings")
        if self.day_started_on is not None and (
            isinstance(self.day_started_on, datetime)
            or not isinstance(self.day_started_on, date)
        ):
            raise ValueError("day_started_on must be a date")


@dataclass(frozen=True, slots=True)
class OpeningChange:
    """One accepted physical recommendation change."""

    opening_id: str
    state: OpeningStabilityState
    reason: ReasonCode
    window_changed: bool
    blind_changed: bool


@dataclass(frozen=True, slots=True)
class NotificationCandidate:
    """Single grouped candidate; delivery intentionally does not exist."""

    changes: tuple[OpeningChange, ...]


@dataclass(frozen=True, slots=True)
class EvaluationTransition:
    """Application state plus zero or one grouped notification candidate."""

    state: AdvisorState
    notification_candidate: NotificationCandidate | None


def merge_notification_candidates(
    current: NotificationCandidate | None,
    incoming: NotificationCandidate,
) -> NotificationCandidate:
    """Merge a bounded delivery batch using each opening's latest target."""
    changes = (
        {}
        if current is None
        else {change.opening_id: change for change in current.changes}
    )
    for change in incoming.changes:
        previous = changes.get(change.opening_id)
        changes[change.opening_id] = OpeningChange(
            change.opening_id,
            change.state,
            change.reason,
            change.window_changed or (previous is not None and previous.window_changed),
            change.blind_changed or (previous is not None and previous.blind_changed),
        )
    return NotificationCandidate(tuple(changes[key] for key in sorted(changes)))


def advance_evaluation(
    previous: AdvisorState,
    samples: Mapping[str, StabilityInput],
    now: datetime,
    settings: StabilitySettings,
) -> EvaluationTransition:
    """Advance all available openings and group their stable changes once."""
    if any(not isinstance(opening_id, str) or not opening_id for opening_id in samples):
        raise ValueError("opening IDs must be non-empty strings")
    openings = dict(previous.openings)
    changes: list[OpeningChange] = []
    for opening_id in sorted(samples):
        sample = samples[opening_id]
        before = openings.get(
            opening_id,
            initial_stability_state(sample.current_action),
        )
        transition = advance_opening(before, sample, now, settings)
        openings[opening_id] = transition.state
        if transition.changed:
            changes.append(
                OpeningChange(
                    opening_id,
                    transition.state,
                    sample.policy.reason,
                    transition.window_changed,
                    transition.blind_changed,
                )
            )
    candidate = NotificationCandidate(tuple(changes)) if changes else None
    return EvaluationTransition(
        AdvisorState(openings, previous.day_started_on), candidate
    )


def logical_day_started_on(local_now: datetime, day_start: time) -> date:
    """Return the logical local date for an aware local timestamp."""
    if (
        not isinstance(local_now, datetime)
        or local_now.tzinfo is None
        or local_now.utcoffset() is None
    ):
        raise ValueError("local_now must be timezone-aware")
    if not isinstance(day_start, time) or day_start.tzinfo is not None:
        raise ValueError("day_start must be a naive time")
    if local_now.timetz().replace(tzinfo=None) < day_start:
        return local_now.date() - timedelta(days=1)
    return local_now.date()


def _day(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("day_started_on must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("day_started_on must be an ISO date") from error
    if parsed.isoformat() != value:
        raise ValueError("day_started_on must be an ISO date")
    return parsed


def start_day(
    state: AdvisorState,
    started_on: date,
    opening_has_blind: Mapping[str, bool],
) -> tuple[AdvisorState, bool]:
    """Reset assumed opening state once for each logical local day."""
    if isinstance(started_on, datetime) or not isinstance(started_on, date):
        raise ValueError("started_on must be a date")
    if not isinstance(opening_has_blind, Mapping):
        raise ValueError("opening_has_blind must be a mapping")
    if any(
        not isinstance(opening_id, str)
        or not opening_id
        or not isinstance(has_blind, bool)
        for opening_id, has_blind in opening_has_blind.items()
    ):
        raise ValueError("opening capabilities must use valid IDs and booleans")
    if state.day_started_on == started_on:
        return state, False
    openings = {
        opening_id: OpeningStabilityState(
            WindowState.CLOSED,
            BlindOpening(0 if has_blind else 100),
        )
        for opening_id, has_blind in opening_has_blind.items()
    }
    return AdvisorState(openings, started_on), True


def _pending_window_to_dict(pending: PendingWindow | None) -> object:
    if pending is None:
        return None
    return {"target": pending.target.value, "since": pending.since.isoformat()}


def _pending_blind_to_dict(pending: PendingBlind | None) -> object:
    if pending is None:
        return None
    return {
        "direction": pending.direction.value,
        "target": pending.target.percent,
        "since": pending.since.isoformat(),
    }


def state_to_dict(state: AdvisorState) -> dict[str, object]:
    """Encode state using JSON-safe versioned primitives."""
    return {
        "version": STATE_VERSION,
        "day_started_on": (
            state.day_started_on.isoformat()
            if state.day_started_on is not None
            else None
        ),
        "openings": {
            opening_id: {
                "window": opening.window.value,
                "blind": opening.blind.percent,
                "blind_direction": (
                    opening.blind_direction.value
                    if opening.blind_direction is not None
                    else None
                ),
                "pending_window": _pending_window_to_dict(opening.pending_window),
                "pending_blind": _pending_blind_to_dict(opening.pending_blind),
            }
            for opening_id, opening in sorted(state.openings.items())
        },
    }


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("pending timestamp must be a string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("pending timestamp must be ISO 8601") from error


def _blind(value: object) -> BlindOpening:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("blind target must be numeric")
    return BlindOpening(float(value))


def _pending_window(value: object) -> PendingWindow | None:
    if value is None:
        return None
    payload = _mapping(value, "pending_window")
    try:
        return PendingWindow(
            WindowState(payload["target"]),
            _timestamp(payload["since"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid pending_window") from error


def _pending_blind(value: object) -> PendingBlind | None:
    if value is None:
        return None
    payload = _mapping(value, "pending_blind")
    try:
        return PendingBlind(
            BlindDirection(payload["direction"]),
            _blind(payload["target"]),
            _timestamp(payload["since"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid pending_blind") from error


def state_from_dict(value: object) -> AdvisorState:
    """Decode and validate versioned persisted state without silent fallback."""
    payload = _mapping(value, "state")
    version = payload.get("version")
    if (
        isinstance(version, bool)
        or not isinstance(version, int)
        or version not in (1, STATE_VERSION)
    ):
        raise ValueError("unsupported state version")
    if version == 1:
        day_started_on = None
    elif "day_started_on" not in payload:
        raise ValueError("day_started_on is required for state version 2")
    else:
        raw_day = payload["day_started_on"]
        day_started_on = None if raw_day is None else _day(raw_day)
    opening_payloads = _mapping(payload.get("openings"), "openings")
    openings: dict[str, OpeningStabilityState] = {}
    for opening_id, value in opening_payloads.items():
        if not isinstance(opening_id, str) or not opening_id:
            raise ValueError("opening IDs must be non-empty strings")
        opening = _mapping(value, f"opening {opening_id}")
        try:
            direction = opening["blind_direction"]
            openings[opening_id] = OpeningStabilityState(
                window=WindowState(opening["window"]),
                blind=_blind(opening["blind"]),
                blind_direction=(
                    BlindDirection(direction) if direction is not None else None
                ),
                pending_window=_pending_window(opening["pending_window"]),
                pending_blind=_pending_blind(opening["pending_blind"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid state for opening {opening_id}") from error
    return AdvisorState(openings, day_started_on)
