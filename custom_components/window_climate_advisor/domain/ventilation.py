"""Conservative unilateral airflow through one opening."""

from dataclasses import dataclass
from math import isfinite, sqrt

from .geometry import opening_fraction
from .models import BlindOpening, OpeningDimensions, ThermalConditions, WindowState


@dataclass(frozen=True, slots=True)
class AirflowCalibration:
    """Historical coefficients for the unilateral airflow approximation."""

    tilt_opening_fraction: float = 0.12
    gust_speed_factor: float = 0.35
    wind_coefficient: float = 0.001
    stack_coefficient: float = 0.0035

    def __post_init__(self) -> None:
        values = (
            ("tilt_opening_fraction", self.tilt_opening_fraction, False),
            ("gust_speed_factor", self.gust_speed_factor, True),
            ("wind_coefficient", self.wind_coefficient, True),
            ("stack_coefficient", self.stack_coefficient, True),
        )
        for name, value, allow_zero in values:
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
            if value < 0 or (not allow_zero and value == 0):
                raise ValueError(f"{name} must be positive")
        if self.tilt_opening_fraction > 1:
            raise ValueError("tilt_opening_fraction must not exceed 1")


DEFAULT_AIRFLOW_CALIBRATION = AirflowCalibration()


def effective_free_area_m2(
    dimensions: OpeningDimensions,
    state: WindowState,
    blind: BlindOpening,
    calibration: AirflowCalibration = DEFAULT_AIRFLOW_CALIBRATION,
) -> float:
    """Return opening area available to airflow after blind obstruction."""
    return (
        dimensions.area_m2
        * opening_fraction(state, tilt_fraction=calibration.tilt_opening_fraction)
        * blind.fraction
    )


def unilateral_airflow_m3_s(
    dimensions: OpeningDimensions,
    state: WindowState,
    blind: BlindOpening,
    conditions: ThermalConditions,
    calibration: AirflowCalibration = DEFAULT_AIRFLOW_CALIBRATION,
) -> float:
    """Return conservative unilateral airflow in cubic metres per second."""
    free_area = effective_free_area_m2(dimensions, state, blind, calibration)
    if free_area == 0:
        return 0.0

    speed_m_s = (
        max(
            conditions.wind_speed_kmh,
            calibration.gust_speed_factor * conditions.gust_speed_kmh,
        )
        / 3.6
    )
    driver = max(
        calibration.wind_coefficient * speed_m_s**2,
        calibration.stack_coefficient
        * dimensions.height_m
        * abs(conditions.outdoor_temperature_c - conditions.indoor_temperature_c),
    )
    return free_area / 2 * sqrt(driver)
