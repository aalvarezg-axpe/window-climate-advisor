"""Redacted diagnostics for Window Climate Advisor."""

from collections import Counter
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_CONTACT_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_HAS_BLIND,
    SUBENTRY_TYPE_OPENING,
    SUBENTRY_TYPE_ROOM,
)
from .coordinator import WindowClimateAdvisorConfigEntry


def _source_quality(
    quality: dict[str, str],
    room_aliases: dict[str, str],
    opening_aliases: dict[str, str],
) -> dict[str, str]:
    """Replace stored subentry IDs in source-quality keys."""
    redacted: dict[str, str] = {}
    for key, value in quality.items():
        parts = key.split(":")
        if len(parts) == 3 and parts[0] == "room":
            key = f"{room_aliases.get(parts[1], 'removed_room')}:{parts[2]}"
        elif len(parts) == 3 and parts[0] == "opening":
            key = f"{opening_aliases.get(parts[1], 'removed_opening')}:{parts[2]}"
        redacted[key] = value
    return redacted


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: WindowClimateAdvisorConfigEntry,
) -> dict[str, Any]:
    """Return useful engine evidence without names, entity IDs, or raw states."""
    coordinator = entry.runtime_data
    data = coordinator.data
    room_ids = sorted(
        subentry_id
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_ROOM
    )
    opening_ids = sorted(
        subentry_id
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    room_aliases = {
        subentry_id: f"room_{index}"
        for index, subentry_id in enumerate(room_ids, start=1)
    }
    opening_aliases = {
        subentry_id: f"opening_{index}"
        for index, subentry_id in enumerate(opening_ids, start=1)
    }
    openings = []
    for opening_id in opening_ids:
        subentry = entry.subentries[opening_id]
        evaluation = data.evaluation.openings[opening_id]
        optimization = evaluation.optimization
        openings.append(
            {
                "alias": opening_aliases[opening_id],
                "has_contact": CONF_CONTACT_ENTITY_ID in subentry.data,
                "has_blind": bool(subentry.data[CONF_HAS_BLIND]),
                "has_cover": CONF_COVER_ENTITY_ID in subentry.data,
                "recommendation": evaluation.recommendation.value,
                "recommended_window_state": evaluation.recommended_window_state.value,
                "recommended_blind_position": (
                    evaluation.recommended_blind.percent
                    if evaluation.recommended_blind is not None
                    else None
                ),
                "safe_to_open": evaluation.safe_to_open,
                "reason": evaluation.reason.value,
                "evaluated_candidates": (
                    optimization.evaluated_candidates
                    if optimization is not None
                    else None
                ),
                "avoided_cost_w": (
                    optimization.avoided_cost_w if optimization is not None else None
                ),
            }
        )

    quality = _source_quality(
        data.source_quality,
        room_aliases,
        opening_aliases,
    )
    return {
        "config": {
            "version": entry.version,
            "options_configured": bool(entry.options),
            "configured_option_keys": sorted(entry.options),
            "room_count": len(room_ids),
            "opening_count": len(opening_ids),
        },
        "evaluation": {
            "evaluated_at": data.evaluation.evaluated_at.isoformat(),
            "active_profile": (
                data.evaluation.season.value
                if data.evaluation.season is not None
                else None
            ),
            "profile_forecast_available": data.profile_forecast_available,
            "openings": openings,
        },
        "source_quality": quality,
        "source_quality_summary": dict(Counter(quality.values())),
    }
