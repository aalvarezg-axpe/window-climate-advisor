"""Tests for grouped and restart-safe application state."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.window_climate_advisor.application.state import (
    AdvisorState,
    NotificationCandidate,
    OpeningChange,
    advance_evaluation,
    logical_day_started_on,
    merge_notification_candidates,
    start_day,
    state_from_dict,
    state_to_dict,
)
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
)
from custom_components.window_climate_advisor.domain.state_machine import (
    BlindDirection,
    OpeningStabilityState,
    PendingBlind,
    PendingWindow,
    StabilityInput,
    StabilitySettings,
)
from custom_components.window_climate_advisor.domain.thermal import ThermalLoad

NOW = datetime(2026, 8, 24, 10, tzinfo=UTC)
SETTINGS = StabilitySettings(50, 10)


def sample(
    current_state: WindowState,
    target_state: WindowState,
    blind: float = 100,
    *,
    reason: ReasonCode = ReasonCode.OPTIMIZER,
    benefit_w: float = 100,
) -> StabilityInput:
    """Create a concise application input."""
    current = CandidateAction(current_state, BlindOpening(100))
    target = CandidateAction(target_state, BlindOpening(blind))
    load = ThermalLoad(0, 0, 0)
    best = CandidateEvaluation(target, load, None, 0, 0, 0, 0)
    current_evaluation = CandidateEvaluation(current, load, None, 0, 0, 0, benefit_w)
    recommendation = {
        WindowState.CLOSED: Recommendation.CLOSE,
        WindowState.TILT: Recommendation.TILT,
        WindowState.OPEN: Recommendation.OPEN,
    }[target_state]
    return StabilityInput(
        current,
        OptimizationResult(best, current_evaluation, 33),
        PolicyResult(
            recommendation,
            target_state,
            target.blind,
            reason not in {ReasonCode.WIND_CLOSE, ReasonCode.RAIN_CLOSE},
            reason,
        ),
        45 if reason is ReasonCode.WIND_CLOSE else 0,
    )


def test_evaluation_returns_at_most_one_sorted_grouped_candidate() -> None:
    """Aggregate every accepted opening change without a delivery surface."""
    previous = AdvisorState(
        {
            "room-b": OpeningStabilityState(WindowState.TILT, BlindOpening(100)),
            "room-a": OpeningStabilityState(WindowState.OPEN, BlindOpening(100)),
        },
        date(2026, 8, 24),
    )
    samples = {
        "room-b": sample(
            WindowState.TILT,
            WindowState.CLOSED,
            reason=ReasonCode.WIND_CLOSE,
            benefit_w=0,
        ),
        "room-a": sample(
            WindowState.OPEN,
            WindowState.CLOSED,
            reason=ReasonCode.WIND_CLOSE,
            benefit_w=0,
        ),
    }

    result = advance_evaluation(previous, samples, NOW, SETTINGS)

    assert result.state.day_started_on == date(2026, 8, 24)

    assert isinstance(result.notification_candidate, NotificationCandidate)
    assert [change.opening_id for change in result.notification_candidate.changes] == [
        "room-a",
        "room-b",
    ]
    assert all(
        change.window_changed and not change.blind_changed
        for change in result.notification_candidate.changes
    )
    assert all(
        change.reason is ReasonCode.WIND_CLOSE
        for change in result.notification_candidate.changes
    )
    assert not hasattr(result.notification_candidate, "send")

    repeated = advance_evaluation(result.state, samples, NOW, SETTINGS)
    assert repeated.notification_candidate is None


def test_notification_batch_keeps_latest_target_and_combines_components() -> None:
    """Merge staggered changes once without losing an earlier component."""
    first_state = OpeningStabilityState(WindowState.TILT, BlindOpening(100))
    latest_state = OpeningStabilityState(WindowState.OPEN, BlindOpening(70))
    current = NotificationCandidate(
        (
            OpeningChange(
                "room-b",
                first_state,
                ReasonCode.OPTIMIZER,
                True,
                False,
            ),
        )
    )
    incoming = NotificationCandidate(
        (
            OpeningChange(
                "room-a",
                first_state,
                ReasonCode.WIND_TILT_ONLY,
                True,
                False,
            ),
            OpeningChange(
                "room-b",
                latest_state,
                ReasonCode.RAIN_TILT_ONLY,
                False,
                True,
            ),
        )
    )

    merged = merge_notification_candidates(current, incoming)

    assert [change.opening_id for change in merged.changes] == ["room-a", "room-b"]
    latest = merged.changes[1]
    assert latest.state == latest_state
    assert latest.reason is ReasonCode.RAIN_TILT_ONLY
    assert latest.window_changed
    assert latest.blind_changed


def test_missing_openings_are_preserved_and_new_ones_start_from_observation() -> None:
    """Do not erase memory on source loss, recovery, or first evaluation."""
    retained = OpeningStabilityState(WindowState.TILT, BlindOpening(40))
    previous = AdvisorState({"missing": retained})

    empty = advance_evaluation(previous, {}, NOW, SETTINGS)
    recovered = advance_evaluation(
        empty.state,
        {
            "new": sample(
                WindowState.OPEN,
                WindowState.CLOSED,
                reason=ReasonCode.WIND_CLOSE,
                benefit_w=0,
            )
        },
        NOW,
        SETTINGS,
    )

    assert empty.state.openings["missing"] == retained
    assert recovered.state.openings["missing"] == retained
    assert recovered.state.openings["new"].window is WindowState.CLOSED
    assert recovered.notification_candidate is not None


def test_state_round_trip_preserves_utc_pending_memory() -> None:
    """Persist candidates and physical memory without Home Assistant helpers."""
    state = AdvisorState(
        {
            "opening": OpeningStabilityState(
                WindowState.TILT,
                BlindOpening(40),
                blind_direction=BlindDirection.LOWER,
                pending_window=PendingWindow(WindowState.OPEN, NOW),
                pending_blind=PendingBlind(
                    BlindDirection.RAISE,
                    BlindOpening(80),
                    NOW + timedelta(minutes=1),
                ),
            )
        },
        date(2026, 8, 24),
    )

    encoded = state_to_dict(state)

    assert encoded["version"] == 2
    assert encoded["day_started_on"] == "2026-08-24"
    assert state_from_dict(encoded) == state
    assert state_from_dict(state_to_dict(AdvisorState())) == AdvisorState()
    without_pending = AdvisorState(
        {
            "opening": OpeningStabilityState(
                WindowState.CLOSED,
                BlindOpening(100),
            )
        }
    )
    assert state_from_dict(state_to_dict(without_pending)) == without_pending


def test_thirty_day_percentage_drift_does_not_create_candidates() -> None:
    """Keep 30 days of small percentage drift diagnostic-only."""
    state = AdvisorState(
        {
            "opening": OpeningStabilityState(
                WindowState.CLOSED,
                BlindOpening(50),
                blind_direction=BlindDirection.LOWER,
            )
        }
    )
    for index in range(30 * 48):
        target = 40 if index % 2 else 50
        result = advance_evaluation(
            state,
            {"opening": sample(WindowState.CLOSED, WindowState.CLOSED, target)},
            NOW + timedelta(minutes=30 * index),
            SETTINGS,
        )
        assert result.notification_candidate is None
        state = result.state


def test_v1_state_migrates_without_a_logical_day_marker() -> None:
    """Load the previous schema and initialize its marker as unknown."""
    state = AdvisorState(
        {"opening": OpeningStabilityState(WindowState.CLOSED, BlindOpening(100))}
    )
    payload = state_to_dict(state)
    payload["version"] = 1
    payload.pop("day_started_on")

    assert state_from_dict(payload) == state
    assert state_from_dict(payload).day_started_on is None


@pytest.mark.parametrize(
    ("local_now", "expected"),
    [
        (
            datetime(2026, 9, 2, 7, 59, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 9, 1),
        ),
        (
            datetime(2026, 9, 2, 8, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 9, 2),
        ),
        (
            datetime(2026, 9, 3, 10, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 9, 3),
        ),
    ],
)
def test_logical_day_uses_the_local_start_boundary(
    local_now: datetime, expected: date
) -> None:
    """Map before, at, and after the configured local start."""
    assert logical_day_started_on(local_now, time(8)) == expected


@pytest.mark.parametrize(
    "local_now, day_start",
    [
        (datetime(2026, 9, 2, 8), time(8)),
        (
            datetime(2026, 9, 2, 8, tzinfo=ZoneInfo("Europe/Madrid")),
            time(8, tzinfo=UTC),
        ),
    ],
)
def test_logical_day_rejects_naive_datetime_or_aware_start(
    local_now: datetime, day_start: time
) -> None:
    """Require a local aware instant and a naive configured wall time."""
    with pytest.raises(ValueError):
        logical_day_started_on(local_now, day_start)


@pytest.mark.parametrize(
    ("local_now", "expected"),
    [
        (
            datetime(2026, 3, 29, 7, 59, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 3, 28),
        ),
        (
            datetime(2026, 3, 29, 8, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 3, 29),
        ),
        (
            datetime(2026, 10, 25, 7, 59, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 10, 24),
        ),
        (
            datetime(2026, 10, 25, 8, tzinfo=ZoneInfo("Europe/Madrid")),
            date(2026, 10, 25),
        ),
    ],
)
def test_logical_day_handles_europe_madrid_dst_dates(
    local_now: datetime, expected: date
) -> None:
    """Use local wall time across both Europe/Madrid DST transitions."""
    assert logical_day_started_on(local_now, time(8)) == expected


def test_start_day_resets_configured_openings_and_is_idempotent() -> None:
    """Reset assumptions and clear all pending movement memory once daily."""
    state = AdvisorState(
        {
            "with-blind": OpeningStabilityState(
                WindowState.OPEN,
                BlindOpening(40),
                blind_direction=BlindDirection.LOWER,
                pending_window=PendingWindow(WindowState.CLOSED, NOW),
                pending_blind=PendingBlind(
                    BlindDirection.RAISE,
                    BlindOpening(80),
                    NOW,
                ),
            ),
            "without-blind": OpeningStabilityState(
                WindowState.TILT,
                BlindOpening(20),
            ),
        },
        date(2026, 9, 1),
    )

    reset, changed = start_day(
        state,
        date(2026, 9, 2),
        {"with-blind": True, "without-blind": False},
    )

    assert changed
    assert reset.day_started_on == date(2026, 9, 2)
    assert reset.openings == {
        "with-blind": OpeningStabilityState(WindowState.CLOSED, BlindOpening(0)),
        "without-blind": OpeningStabilityState(
            WindowState.CLOSED,
            BlindOpening(100),
        ),
    }
    same, changed_again = start_day(
        reset,
        date(2026, 9, 2),
        {"with-blind": True, "without-blind": False},
    )
    assert same is reset
    assert not changed_again


@pytest.mark.parametrize(
    "capabilities",
    [
        {"": True},
        {1: True},
        {"opening": 1},
    ],
)
def test_start_day_rejects_invalid_opening_ids_and_blind_flags(
    capabilities: object,
) -> None:
    """Do not coerce untrusted opening identities or capability flags."""
    with pytest.raises(ValueError):
        start_day(AdvisorState(), date(2026, 9, 2), capabilities)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"version": 2, "openings": {}},
        {"version": 2, "day_started_on": "not-a-date", "openings": {}},
        {"version": 2, "day_started_on": "2026-02-30", "openings": {}},
        {"version": 2, "day_started_on": date(2026, 9, 2), "openings": {}},
        {"version": 1, "openings": []},
        {"version": 1, "openings": {"": {}}},
        {"version": 1, "openings": {1: {}}},
        {"version": 1, "openings": {"opening": []}},
        {
            "version": 1,
            "openings": {
                "opening": {
                    "window": "closed",
                    "blind": True,
                    "blind_direction": None,
                    "pending_window": None,
                    "pending_blind": None,
                }
            },
        },
        {
            "version": 1,
            "openings": {
                "opening": {
                    "window": "closed",
                    "blind": 50,
                    "blind_direction": None,
                    "pending_window": {
                        "target": "open",
                        "since": "not-a-time",
                    },
                    "pending_blind": None,
                }
            },
        },
        {
            "version": 1,
            "openings": {
                "opening": {
                    "window": "closed",
                    "blind": 50,
                    "blind_direction": None,
                    "pending_window": {
                        "target": "open",
                        "since": 123,
                    },
                    "pending_blind": None,
                }
            },
        },
        {
            "version": 1,
            "openings": {
                "opening": {
                    "window": "closed",
                    "blind": 50,
                    "blind_direction": None,
                    "pending_window": None,
                    "pending_blind": {
                        "direction": "sideways",
                        "target": 80,
                        "since": NOW.isoformat(),
                    },
                }
            },
        },
    ],
)
def test_invalid_persisted_state_fails_explicitly(payload: object) -> None:
    """Reject corrupt or unsupported state instead of silently resetting it."""
    with pytest.raises(ValueError):
        state_from_dict(payload)


def test_empty_opening_ids_are_rejected_at_both_boundaries() -> None:
    """Require stable non-empty identity for state and evaluations."""
    for opening_id in ("", 1):
        with pytest.raises(ValueError):
            AdvisorState(  # type: ignore[dict-item]
                {opening_id: OpeningStabilityState(WindowState.CLOSED, BlindOpening(0))}
            )
    with pytest.raises(ValueError):
        advance_evaluation(
            AdvisorState(),
            {"": sample(WindowState.CLOSED, WindowState.CLOSED)},
            NOW,
            SETTINGS,
        )
