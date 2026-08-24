"""Informational binary sensors for Window Climate Advisor."""

from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SUBENTRY_TYPE_OPENING
from .coordinator import (
    WindowClimateAdvisorConfigEntry,
    WindowClimateAdvisorCoordinator,
)
from .domain.policy import Recommendation
from .entity import WindowClimateAdvisorOpeningEntity

SAFE_TO_OPEN_DESCRIPTION = BinarySensorEntityDescription(
    key="safe_to_open",
    translation_key="safe_to_open",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WindowClimateAdvisorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one safety sensor per opening."""
    coordinator = entry.runtime_data
    for opening_id, subentry in entry.subentries.items():
        if subentry.subentry_type == SUBENTRY_TYPE_OPENING:
            async_add_entities(
                [SafeToOpenBinarySensor(coordinator, opening_id)],
                config_subentry_id=opening_id,
            )


class SafeToOpenBinarySensor(WindowClimateAdvisorOpeningEntity, BinarySensorEntity):
    """Publish whether current weather policy permits opening."""

    entity_description = SAFE_TO_OPEN_DESCRIPTION

    def __init__(
        self, coordinator: WindowClimateAdvisorCoordinator, opening_id: str
    ) -> None:
        """Initialize the safety sensor."""
        super().__init__(coordinator, opening_id, self.entity_description.key)

    @property
    @override
    def available(self) -> bool:
        """Expose degradation as unavailable rather than a favourable state."""
        return (
            super().available
            and self.opening.recommendation is not Recommendation.DEGRADED
        )

    @property
    @override
    def is_on(self) -> bool:
        """Return the evaluated safety result."""
        return self.opening.safe_to_open
