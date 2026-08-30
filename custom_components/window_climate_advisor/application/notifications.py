"""Typed notification recipient configuration."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from ..const import CONF_PERSON_ENTITY_ID
from ..domain.models import BlindOpening, WindowState
from ..domain.optimizer import CandidateAction
from ..domain.policy import Recommendation
from .evaluator import AdvisorEvaluation


@dataclass(frozen=True, slots=True)
class OpeningFeedback:
    """Current physical feedback available for one opening."""

    current_action: CandidateAction
    window_observed: bool
    blind_observed: bool


@dataclass(frozen=True, slots=True)
class ArrivalOpeningAdvice:
    """Still-actionable part of one opening recommendation on arrival."""

    opening_id: str
    window: WindowState | None
    blind: BlindOpening | None
    manual_blind_unobserved: bool


@dataclass(frozen=True, slots=True)
class ArrivalNotificationCandidate:
    """Fresh actionable summary for a recipient arriving home."""

    openings: tuple[ArrivalOpeningAdvice, ...]


def recipient_person_from_mapping(
    value: Mapping[str, object],
) -> str:
    """Decode one persisted recipient without importing Home Assistant."""
    person_entity_id = value.get(CONF_PERSON_ENTITY_ID)
    if not isinstance(person_entity_id, str):
        raise ValueError("recipient person entity ID must be a string")
    if not person_entity_id.startswith("person."):
        raise ValueError("recipient person must be a person entity")
    return person_entity_id


def recipient_persons_from_mappings(
    values: Iterable[Mapping[str, object]],
) -> tuple[str, ...]:
    """Decode recipients and reject duplicate people."""
    recipients = tuple(recipient_person_from_mapping(value) for value in values)
    if len(set(recipients)) != len(recipients):
        raise ValueError("recipient persons must be unique")
    return recipients


def arrival_notification_candidate(
    evaluation: AdvisorEvaluation,
    feedback_by_opening: Mapping[str, OpeningFeedback],
) -> ArrivalNotificationCandidate | None:
    """Build fresh advice, retaining only targets not proven already satisfied."""
    openings: list[ArrivalOpeningAdvice] = []
    for opening_id, result in sorted(evaluation.openings.items()):
        if result.recommendation is Recommendation.DEGRADED:
            continue
        feedback = feedback_by_opening.get(opening_id)
        window: WindowState | None = result.recommended_window_state
        if (
            feedback is not None
            and feedback.window_observed
            and feedback.current_action.window_state is window
        ):
            window = None
        blind = result.recommended_blind
        if (
            blind is not None
            and feedback is not None
            and feedback.blind_observed
            and feedback.current_action.blind == blind
        ):
            blind = None
        if window is None and blind is None:
            continue
        openings.append(
            ArrivalOpeningAdvice(
                opening_id,
                window,
                blind,
                blind is not None and (feedback is None or not feedback.blind_observed),
            )
        )
    return ArrivalNotificationCandidate(tuple(openings)) if openings else None
