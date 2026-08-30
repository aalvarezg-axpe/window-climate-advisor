"""Versioned advisor state and grouped transition candidates."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..domain.models import BlindOpening, WindowState
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

STATE_VERSION = 1


@dataclass(frozen=True, slots=True)
class AdvisorState:
    """Restart-safe state for all known openings."""

    openings: dict[str, OpeningStabilityState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if any(
            not isinstance(opening_id, str) or not opening_id
            for opening_id in self.openings
        ):
            raise ValueError("opening IDs must be non-empty strings")


@dataclass(frozen=True, slots=True)
class OpeningChange:
    """One accepted physical recommendation change."""

    opening_id: str
    state: OpeningStabilityState
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


def advance_evaluation(
    previous: AdvisorState,
    samples: Mapping[str, StabilityInput],
    now: datetime,
    settings: StabilitySettings,
) -> EvaluationTransition:
    """Advance all available openings and group their stable changes once."""
    openings = dict(previous.openings)
    changes: list[OpeningChange] = []
    for opening_id in sorted(samples):
        if not opening_id:
            raise ValueError("opening IDs must not be empty")
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
                    transition.window_changed,
                    transition.blind_changed,
                )
            )
    candidate = NotificationCandidate(tuple(changes)) if changes else None
    return EvaluationTransition(AdvisorState(openings), candidate)


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
    if payload.get("version") != STATE_VERSION:
        raise ValueError("unsupported state version")
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
    return AdvisorState(openings)
