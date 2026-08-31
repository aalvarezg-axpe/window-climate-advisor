"""Tests for redacted Home Assistant diagnostics."""

import json

from homeassistant.core import HomeAssistant

from custom_components.window_climate_advisor.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.integration.test_adapters import entry, set_ready_states
from tests.integration.test_config_flow import VALID_OPTIONS


async def test_diagnostics_redact_household_identifiers_and_raw_state(
    hass: HomeAssistant,
) -> None:
    """Expose source quality and engine evidence without private identifiers."""
    config_entry = entry(recipient=True)
    object.__setattr__(
        config_entry,
        "options",
        type(config_entry.options)(VALID_OPTIONS),
    )
    config_entry.add_to_hass(hass)
    set_ready_states(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)

    report = await async_get_config_entry_diagnostics(hass, config_entry)
    serialized = json.dumps(report, sort_keys=True)
    private_values = {
        config_entry.entry_id,
        config_entry.title,
        *(config_entry.data.values()),
        *(subentry.subentry_id for subentry in config_entry.subentries.values()),
        *(subentry.title for subentry in config_entry.subentries.values()),
        *(
            value
            for subentry in config_entry.subentries.values()
            for key, value in subentry.data.items()
            if key.endswith("_entity_id")
        ),
    }
    assert all(str(value) not in serialized for value in private_values)
    assert report["config"]["opening_count"] == 1
    assert report["config"]["recipient_count"] == 1
    assert report["evaluation"]["openings"][0]["alias"] == "opening_1"
    assert report["evaluation"]["openings"][0]["has_blind"] is True
    assert report["evaluation"]["openings"][0]["evaluated_candidates"] == 31
    assert report["evaluation"]["daily_forecast_available"] is False
    assert "profile_forecast_available" not in report["evaluation"]
    assert report["source_quality"]["room_1:temperature"] == "ready"
    assert report["source_quality"]["opening_1:contact"] == "ready"
    assert report["source_quality_summary"] == {"ready": 11}
