"""Tests for coordinator scheduling, degradation, and persistence."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.weather import SERVICE_GET_FORECASTS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.window_climate_advisor.application.evaluator import InputIssue
from custom_components.window_climate_advisor.const import (
    CONF_WIND_GUST_ENTITY_ID,
    CONF_WIND_SPEED_ENTITY_ID,
)
from custom_components.window_climate_advisor.coordinator import (
    WindowClimateAdvisorCoordinator,
)
from custom_components.window_climate_advisor.domain.policy import Recommendation
from custom_components.window_climate_advisor.domain.profiles import Season
from tests.integration.test_adapters import entry, set_ready_states
from tests.integration.test_config_flow import VALID_OPTIONS


async def test_incomplete_options_load_as_explicit_degradation(
    hass: HomeAssistant,
) -> None:
    """Keep the UI-repairable entry loaded without hidden tuning defaults."""
    config_entry = entry()
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    opening = next(iter(coordinator.data.evaluation.openings.values()))
    assert opening.recommendation is Recommendation.DEGRADED
    assert opening.reason is InputIssue.CONFIGURATION_REQUIRED
    assert coordinator.data.source_quality["options"] == "configuration_required"
    assert not coordinator.data.forecast_available


async def test_configured_coordinator_uses_forecast_persists_and_refreshes(
    hass: HomeAssistant,
) -> None:
    """Evaluate configured sources, persist state, and debounce state events."""
    config_entry = entry()
    object.__setattr__(
        config_entry, "options", type(config_entry.options)(VALID_OPTIONS)
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)

    async def forecast(_: ServiceCall) -> dict[str, object]:
        return {"weather.home": {"forecast": [{"temperature": 30}]}}

    hass.services.async_register(
        "weather",
        SERVICE_GET_FORECASTS,
        forecast,
        supports_response=SupportsResponse.ONLY,
    )
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data.evaluation.season is Season.SUMMER
    assert coordinator.data.forecast_available
    assert coordinator.data.source_quality["options"] == "ready"
    with patch.object(
        coordinator, "async_request_refresh", new_callable=AsyncMock
    ) as refresh:
        hass.states.async_set("sensor.outdoor", "21", {"unit_of_measurement": "°C"})
        await hass.async_block_till_done()
        refresh.assert_awaited_once()

    restored = WindowClimateAdvisorCoordinator(hass, config_entry)
    await restored.async_config_entry_first_refresh()
    assert restored.data.evaluation.state == coordinator.data.evaluation.state


async def test_invalid_structural_storage_fails_setup_explicitly(
    hass: HomeAssistant,
) -> None:
    """Do not silently invent required entity assignments from corrupt config."""
    config_entry = entry()
    object.__setattr__(config_entry, "data", type(config_entry.data)({}))
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


async def test_duplicate_stored_links_fail_setup_explicitly(
    hass: HomeAssistant,
) -> None:
    """Defend setup against duplicate links from older or corrupted storage."""
    config_entry = entry()
    object.__setattr__(
        config_entry,
        "data",
        type(config_entry.data)(
            {
                **config_entry.data,
                CONF_WIND_GUST_ENTITY_ID: config_entry.data[CONF_WIND_SPEED_ENTITY_ID],
            }
        ),
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()
