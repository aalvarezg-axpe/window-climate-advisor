"""Tests for typed notification recipient configuration."""

from datetime import UTC, datetime

import pytest

from custom_components.window_climate_advisor.application.evaluator import (
    AdvisorEvaluation,
    OpeningEvaluation,
)
from custom_components.window_climate_advisor.application.notifications import (
    ArrivalNotificationCandidate,
    ArrivalOpeningAdvice,
    OpeningFeedback,
    arrival_notification_candidate,
    recipient_person_from_mapping,
    recipient_persons_from_mappings,
)
from custom_components.window_climate_advisor.application.state import AdvisorState
from custom_components.window_climate_advisor.const import CONF_PERSON_ENTITY_ID
from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    WindowState,
)
from custom_components.window_climate_advisor.domain.optimizer import CandidateAction
from custom_components.window_climate_advisor.domain.policy import (
    ReasonCode,
    Recommendation,
)
from custom_components.window_climate_advisor.domain.profiles import Season


def _mapping(person: str) -> dict[str, object]:
    return {CONF_PERSON_ENTITY_ID: person}


def test_recipient_mapping_is_typed_and_ordered() -> None:
    """Decode persisted mappings without Home Assistant objects."""
    assert recipient_person_from_mapping(_mapping("person.one")) == "person.one"
    assert recipient_persons_from_mappings(
        [_mapping("person.two"), _mapping("person.one")]
    ) == ("person.two", "person.one")


def test_recipient_mapping_rejects_missing_and_duplicate_people() -> None:
    """Reject malformed and repeated-person mappings."""
    for value in ({}, {CONF_PERSON_ENTITY_ID: 1}):
        with pytest.raises(ValueError):
            recipient_person_from_mapping(value)
    for value in (_mapping("sensor.one"),):
        with pytest.raises(ValueError):
            recipient_person_from_mapping(value)
    with pytest.raises(ValueError, match="persons must be unique"):
        recipient_persons_from_mappings(
            [_mapping("person.one"), _mapping("person.one")]
        )


def _evaluation(
    *openings: tuple[str, Recommendation, WindowState, float | None],
) -> AdvisorEvaluation:
    """Build the minimum stable evaluation needed by arrival advice tests."""
    return AdvisorEvaluation(
        datetime(2026, 8, 30, tzinfo=UTC),
        Season.SUMMER,
        {
            opening_id: OpeningEvaluation(
                recommendation,
                window,
                BlindOpening(blind) if blind is not None else None,
                True,
                ReasonCode.OPTIMIZER,
                None,
            )
            for opening_id, recommendation, window, blind in openings
        },
        AdvisorState(),
        None,
    )


def test_arrival_advice_omits_targets_proven_satisfied() -> None:
    """Do not notify when contact and cover feedback already match targets."""
    evaluation = _evaluation(
        ("south", Recommendation.OPEN, WindowState.OPEN, 60),
    )

    assert (
        arrival_notification_candidate(
            evaluation,
            {
                "south": OpeningFeedback(
                    CandidateAction(WindowState.OPEN, BlindOpening(60)),
                    window_observed=True,
                    blind_observed=True,
                )
            },
        )
        is None
    )


def test_arrival_advice_keeps_only_actionable_and_unobserved_targets() -> None:
    """Retain mismatches and mark a manual blind whose position is unknowable."""
    evaluation = _evaluation(
        ("manual", Recommendation.TILT, WindowState.TILT, 40),
        ("observed", Recommendation.CLOSE, WindowState.CLOSED, 100),
        ("degraded", Recommendation.DEGRADED, WindowState.CLOSED, None),
    )

    assert arrival_notification_candidate(
        evaluation,
        {
            "manual": OpeningFeedback(
                CandidateAction(WindowState.CLOSED, BlindOpening(80)),
                window_observed=True,
                blind_observed=False,
            ),
            "observed": OpeningFeedback(
                CandidateAction(WindowState.OPEN, BlindOpening(100)),
                window_observed=True,
                blind_observed=True,
            ),
        },
    ) == ArrivalNotificationCandidate(
        (
            # Window and manual blind both remain actionable.
            ArrivalOpeningAdvice("manual", WindowState.TILT, BlindOpening(40), True),
            # Only the observed window differs; the blind target is already met.
            ArrivalOpeningAdvice("observed", WindowState.CLOSED, None, False),
        )
    )
