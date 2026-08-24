"""Tests for the frozen informational entity surface."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.window_climate_advisor.const import (
    DOMAIN,
    SUBENTRY_TYPE_OPENING,
)
from custom_components.window_climate_advisor.domain.policy import Recommendation
from tests.integration.test_adapters import entry, set_ready_states
from tests.integration.test_config_flow import VALID_OPTIONS


def _entity_id(
    registry: er.EntityRegistry,
    domain: str,
    unique_id: str,
) -> str:
    """Return one required entity-registry ID."""
    entity_id = registry.async_get_entity_id(domain, DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


async def test_entities_publish_stable_advisor_results_and_devices(
    hass: HomeAssistant,
) -> None:
    """Publish five informational entities with stable subentry identities."""
    config_entry = entry()
    object.__setattr__(
        config_entry,
        "options",
        type(config_entry.options)(VALID_OPTIONS),
    )
    config_entry.add_to_hass(hass)
    set_ready_states(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    opening_id = next(
        subentry_id
        for subentry_id, subentry in config_entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    registry = er.async_get(hass)
    unique_prefix = f"{config_entry.entry_id}:{opening_id}"
    recommendation_id = _entity_id(
        registry, "sensor", f"{unique_prefix}:recommendation"
    )
    blind_id = _entity_id(
        registry, "sensor", f"{unique_prefix}:recommended_blind_position"
    )
    safety_id = _entity_id(registry, "binary_sensor", f"{unique_prefix}:safe_to_open")
    profile_id = _entity_id(
        registry, "sensor", f"{config_entry.entry_id}:active_profile"
    )
    evaluated_id = _entity_id(
        registry, "sensor", f"{config_entry.entry_id}:last_evaluation"
    )

    assert hass.states.get(recommendation_id).state in {
        item.value for item in Recommendation
    }
    assert 0 <= float(hass.states.get(blind_id).state) <= 100
    assert hass.states.get(safety_id).state == "on"
    assert hass.states.get(profile_id).state == "summer"
    assert hass.states.get(evaluated_id).state != "unavailable"

    opening_entries = [
        registry.async_get(entity_id)
        for entity_id in (recommendation_id, blind_id, safety_id)
    ]
    dwelling_entries = [
        registry.async_get(entity_id) for entity_id in (profile_id, evaluated_id)
    ]
    assert all(
        item is not None and item.config_subentry_id == opening_id
        for item in opening_entries
    )
    opening_device_ids = {item.device_id for item in opening_entries if item}
    dwelling_device_ids = {item.device_id for item in dwelling_entries if item}
    assert len(opening_device_ids) == len(dwelling_device_ids) == 1
    assert opening_device_ids != dwelling_device_ids
    opening_device = dr.async_get(hass).async_get(opening_device_ids.pop())
    assert opening_device is not None
    assert opening_device.via_device_id == dwelling_device_ids.pop()

    original_ids = set(registry.entities)
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    assert original_ids == set(registry.entities)


async def test_incomplete_options_degrade_and_optional_cover_omits_sensor(
    hass: HomeAssistant,
) -> None:
    """Keep repairable entities explicit and do not invent a blind target."""
    config_entry = entry(cover=False)
    config_entry.add_to_hass(hass)
    set_ready_states(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    opening_id = next(
        subentry_id
        for subentry_id, subentry in config_entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING
    )
    registry = er.async_get(hass)
    prefix = f"{config_entry.entry_id}:{opening_id}"
    recommendation_id = _entity_id(registry, "sensor", f"{prefix}:recommendation")
    safety_id = _entity_id(registry, "binary_sensor", f"{prefix}:safe_to_open")
    profile_id = _entity_id(
        registry, "sensor", f"{config_entry.entry_id}:active_profile"
    )

    assert hass.states.get(recommendation_id).state == "degraded"
    assert hass.states.get(safety_id).state == "unavailable"
    assert hass.states.get(profile_id).state == "unavailable"
    assert (
        registry.async_get_entity_id(
            "sensor",
            DOMAIN,
            f"{prefix}:recommended_blind_position",
        )
        is None
    )
