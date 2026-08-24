"""Shared entities for the Window Climate Advisor integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .application.evaluator import OpeningEvaluation
from .const import DOMAIN
from .coordinator import WindowClimateAdvisorCoordinator


class WindowClimateAdvisorDwellingEntity(
    CoordinatorEntity[WindowClimateAdvisorCoordinator]
):
    """Base for one dwelling-level informational entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WindowClimateAdvisorCoordinator,
        kind: str,
    ) -> None:
        """Bind identity to the immutable config-entry ID."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}:{kind}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )


class WindowClimateAdvisorOpeningEntity(
    CoordinatorEntity[WindowClimateAdvisorCoordinator]
):
    """Base for one opening-level informational entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WindowClimateAdvisorCoordinator,
        opening_id: str,
        kind: str,
    ) -> None:
        """Bind identity to immutable config-entry and subentry IDs."""
        super().__init__(coordinator, context=opening_id)
        entry = coordinator.config_entry
        self._opening_id = opening_id
        self._attr_unique_id = f"{entry.entry_id}:{opening_id}:{kind}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}:{opening_id}")},
            name=entry.subentries[opening_id].title,
            via_device=(DOMAIN, entry.entry_id),
        )

    @property
    def opening(self) -> OpeningEvaluation:
        """Return this opening's current evaluation."""
        return self.coordinator.data.evaluation.openings[self._opening_id]
