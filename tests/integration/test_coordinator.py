"""Tests for coordinator scheduling, degradation, and persistence."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.weather import SERVICE_GET_FORECASTS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_HOME, STATE_NOT_HOME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.window_climate_advisor.application.evaluator import InputIssue
from custom_components.window_climate_advisor.const import (
    CONF_PERSON_ENTITY_ID,
    CONF_WIND_GUST_ENTITY_ID,
    CONF_WIND_SPEED_ENTITY_ID,
    SUBENTRY_TYPE_RECIPIENT,
)
from custom_components.window_climate_advisor.coordinator import (
    WindowClimateAdvisorCoordinator,
)
from custom_components.window_climate_advisor.domain.optimizer import optimize_opening
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
    assert not coordinator.data.profile_forecast_available


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

    with (
        patch(
            "custom_components.window_climate_advisor.application.evaluator.optimize_opening",
            wraps=optimize_opening,
        ) as optimizer,
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_notification_candidate",
            new_callable=AsyncMock,
            return_value=0,
        ) as deliver,
    ):
        await coordinator.async_config_entry_first_refresh()

    assert coordinator.data.evaluation.season is Season.SUMMER
    assert coordinator.data.profile_forecast_available
    optimizer.assert_called_once()
    deliver.assert_awaited_once_with(
        hass,
        config_entry,
        coordinator.data.evaluation.notification_candidate,
        (),
    )
    assert optimizer.call_args.args[0].forecast_conditions is None
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


async def test_invalid_recipient_link_does_not_degrade_advisor(
    hass: HomeAssistant,
) -> None:
    """Keep notification configuration failures outside climate evaluation."""
    config_entry = entry(recipient=True)
    object.__setattr__(
        config_entry,
        "options",
        type(config_entry.options)(VALID_OPTIONS),
    )
    recipient = next(
        subentry
        for subentry in config_entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_RECIPIENT
    )
    object.__setattr__(
        recipient,
        "data",
        type(recipient.data)(
            {
                **recipient.data,
                CONF_PERSON_ENTITY_ID: config_entry.data[CONF_WIND_SPEED_ENTITY_ID],
            }
        ),
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data.source_quality["options"] == "ready"
    assert all(
        opening.recommendation is not Recommendation.DEGRADED
        for opening in coordinator.data.evaluation.openings.values()
    )


async def test_only_real_arrival_runs_fresh_targeted_delivery(
    hass: HomeAssistant,
) -> None:
    """Ignore startup/recovery and send once for a real away-to-home edge."""
    config_entry = entry(recipient=True)
    object.__setattr__(
        config_entry,
        "options",
        type(config_entry.options)(VALID_OPTIONS),
    )
    config_entry.add_to_hass(hass)
    config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    set_ready_states(hass)
    hass.states.async_set("person.resident", STATE_HOME)
    hass.states.async_set("notify.phone", "unknown")
    coordinator = WindowClimateAdvisorCoordinator(hass, config_entry)

    with (
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_notification_candidate",
            new_callable=AsyncMock,
            return_value=0,
        ) as ordinary,
        patch(
            "custom_components.window_climate_advisor.coordinator.async_deliver_arrival_candidate",
            new_callable=AsyncMock,
            return_value=0,
        ) as arrival,
    ):
        await coordinator.async_config_entry_first_refresh()
        arrival.assert_not_awaited()

        with patch.object(
            coordinator, "async_request_refresh", new_callable=AsyncMock
        ) as refresh:
            ordinary.reset_mock()
            hass.states.async_set("person.resident", STATE_NOT_HOME)
            await hass.async_block_till_done()
            refresh.assert_awaited_once()
            arrival.assert_not_awaited()

            refresh.reset_mock()
            ordinary.reset_mock()
            hass.states.async_set("person.resident", STATE_HOME)
            await hass.async_block_till_done()
            refresh.assert_awaited_once()
            await coordinator.async_refresh()

            arrival.assert_awaited_once()
            assert arrival.await_args.args[0:3] == (
                hass,
                config_entry,
                "person.resident",
            )
            assert ordinary.await_args.args[3] == ("person.resident",)

            arrival.reset_mock()
            hass.states.async_set("person.resident", STATE_HOME, {"source": "update"})
            await hass.async_block_till_done()
            await coordinator.async_refresh()
            arrival.assert_not_awaited()

            hass.states.async_set("person.resident", STATE_UNAVAILABLE)
            await hass.async_block_till_done()
            await coordinator.async_refresh()
            arrival.reset_mock()
            hass.states.async_set("person.resident", STATE_HOME)
            await hass.async_block_till_done()
            await coordinator.async_refresh()
            arrival.assert_not_awaited()
