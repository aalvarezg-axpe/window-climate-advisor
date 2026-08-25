"""Informational sensors for Window Climate Advisor."""

from datetime import datetime
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_HAS_BLIND, SUBENTRY_TYPE_OPENING
from .coordinator import (
    WindowClimateAdvisorConfigEntry,
    WindowClimateAdvisorCoordinator,
)
from .domain.policy import Recommendation
from .domain.profiles import Season
from .entity import (
    WindowClimateAdvisorDwellingEntity,
    WindowClimateAdvisorOpeningEntity,
)

RECOMMENDATION_DESCRIPTION = SensorEntityDescription(
    key="recommendation",
    translation_key="recommendation",
    device_class=SensorDeviceClass.ENUM,
    options=[item.value for item in Recommendation],
)
BLIND_DESCRIPTION = SensorEntityDescription(
    key="recommended_blind_position",
    translation_key="recommended_blind_position",
    native_unit_of_measurement=PERCENTAGE,
    suggested_display_precision=0,
)
PROFILE_DESCRIPTION = SensorEntityDescription(
    key="active_profile",
    translation_key="active_profile",
    device_class=SensorDeviceClass.ENUM,
    options=[item.value for item in Season],
)
EVALUATED_AT_DESCRIPTION = SensorEntityDescription(
    key="last_evaluation",
    translation_key="last_evaluation",
    device_class=SensorDeviceClass.TIMESTAMP,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WindowClimateAdvisorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the frozen sensor inventory for one dwelling."""
    coordinator = entry.runtime_data
    async_add_entities(
        [ActiveProfileSensor(coordinator), LastEvaluationSensor(coordinator)]
    )
    for opening_id, subentry in entry.subentries.items():
        if subentry.subentry_type != SUBENTRY_TYPE_OPENING:
            continue
        entities: list[SensorEntity] = [
            OpeningRecommendationSensor(coordinator, opening_id)
        ]
        if bool(subentry.data[CONF_HAS_BLIND]):
            entities.append(RecommendedBlindPositionSensor(coordinator, opening_id))
        async_add_entities(entities, config_subentry_id=opening_id)


class OpeningRecommendationSensor(WindowClimateAdvisorOpeningEntity, SensorEntity):
    """Publish the stable recommendation for one opening."""

    entity_description = RECOMMENDATION_DESCRIPTION

    def __init__(
        self, coordinator: WindowClimateAdvisorCoordinator, opening_id: str
    ) -> None:
        """Initialize the recommendation sensor."""
        super().__init__(coordinator, opening_id, self.entity_description.key)

    @property
    @override
    def native_value(self) -> str:
        """Return the public recommendation enum value."""
        return self.opening.recommendation.value


class RecommendedBlindPositionSensor(WindowClimateAdvisorOpeningEntity, SensorEntity):
    """Publish the stable blind recommendation for one opening."""

    entity_description = BLIND_DESCRIPTION

    def __init__(
        self, coordinator: WindowClimateAdvisorCoordinator, opening_id: str
    ) -> None:
        """Initialize the blind-position sensor."""
        super().__init__(coordinator, opening_id, self.entity_description.key)

    @property
    @override
    def available(self) -> bool:
        """Expose no blind target while this opening is degraded."""
        return (
            super().available
            and self.opening.recommendation is not Recommendation.DEGRADED
        )

    @property
    @override
    def native_value(self) -> float | None:
        """Return the recommended Home Assistant cover percentage."""
        blind = self.opening.recommended_blind
        return blind.percent if blind is not None else None


class ActiveProfileSensor(WindowClimateAdvisorDwellingEntity, SensorEntity):
    """Publish the selected comfort profile."""

    entity_description = PROFILE_DESCRIPTION

    def __init__(self, coordinator: WindowClimateAdvisorCoordinator) -> None:
        """Initialize the active-profile sensor."""
        super().__init__(coordinator, self.entity_description.key)

    @property
    @override
    def available(self) -> bool:
        """Remain unavailable until complete options select a profile."""
        return super().available and self.coordinator.data.evaluation.season is not None

    @property
    @override
    def native_value(self) -> str | None:
        """Return the selected profile enum value."""
        season = self.coordinator.data.evaluation.season
        return season.value if season is not None else None


class LastEvaluationSensor(WindowClimateAdvisorDwellingEntity, SensorEntity):
    """Publish the timestamp of the last coherent evaluation."""

    entity_description = EVALUATED_AT_DESCRIPTION

    def __init__(self, coordinator: WindowClimateAdvisorCoordinator) -> None:
        """Initialize the evaluation timestamp sensor."""
        super().__init__(coordinator, self.entity_description.key)

    @property
    @override
    def native_value(self) -> datetime:
        """Return the UTC evaluation timestamp."""
        return self.coordinator.data.evaluation.evaluated_at
