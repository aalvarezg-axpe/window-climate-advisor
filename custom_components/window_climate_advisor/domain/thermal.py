"""Candidate thermal load for a coupled window and blind state."""

from dataclasses import dataclass
from math import isfinite

from .geometry import blind_solar_factor, opening_fraction
from .models import BlindOpening, OpeningDimensions, ThermalConditions, WindowState
from .ventilation import (
    DEFAULT_AIRFLOW_CALIBRATION,
    AirflowCalibration,
    unilateral_airflow_m3_s,
)


@dataclass(frozen=True, slots=True)
class ThermalCalibration:
    """Historical and provisional coefficients for candidate comparison."""

    glazing_shgc: float = 0.55
    glazing_u_w_m2k: float = 1.40
    air_density_kg_m3: float = 1.2041
    air_heat_capacity_j_kgk: float = 1005
    closed_blind_solar_residual: float = 0.15
    airflow: AirflowCalibration = DEFAULT_AIRFLOW_CALIBRATION

    def __post_init__(self) -> None:
        fractions = (
            ("glazing_shgc", self.glazing_shgc),
            ("closed_blind_solar_residual", self.closed_blind_solar_residual),
        )
        for name, value in fractions:
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite and within [0, 1]")
        for name, value in (
            ("glazing_u_w_m2k", self.glazing_u_w_m2k),
            ("air_density_kg_m3", self.air_density_kg_m3),
            ("air_heat_capacity_j_kgk", self.air_heat_capacity_j_kgk),
        ):
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and greater than zero")


DEFAULT_THERMAL_CALIBRATION = ThermalCalibration()


@dataclass(frozen=True, slots=True)
class ThermalLoad:
    """Heat-load components in watts; positive values heat the room."""

    solar_w: float
    conduction_w: float
    ventilation_w: float

    @property
    def total_w(self) -> float:
        """Return the sum of all heat-load components."""
        return self.solar_w + self.conduction_w + self.ventilation_w


def candidate_thermal_load(
    dimensions: OpeningDimensions,
    state: WindowState,
    blind: BlindOpening,
    conditions: ThermalConditions,
    calibration: ThermalCalibration = DEFAULT_THERMAL_CALIBRATION,
) -> ThermalLoad:
    """Return the candidate room heat load for one window/blind state."""
    state_fraction = opening_fraction(
        state,
        tilt_fraction=calibration.airflow.tilt_opening_fraction,
    )
    blind_factor = blind_solar_factor(
        blind,
        closed_residual=calibration.closed_blind_solar_residual,
    )
    temperature_delta = (
        conditions.outdoor_temperature_c - conditions.indoor_temperature_c
    )
    solar_transmission = (
        (1 - state_fraction) * calibration.glazing_shgc + state_fraction
    ) * blind_factor
    solar_w = (
        conditions.facade_irradiance_w_m2 * dimensions.area_m2 * solar_transmission
    )
    conduction_w = (
        calibration.glazing_u_w_m2k
        * dimensions.area_m2
        * (1 - state_fraction)
        * temperature_delta
    )
    airflow_m3_s = unilateral_airflow_m3_s(
        dimensions,
        state,
        blind,
        conditions,
        calibration.airflow,
    )
    ventilation_w = (
        calibration.air_density_kg_m3
        * calibration.air_heat_capacity_j_kgk
        * airflow_m3_s
        * temperature_delta
    )
    return ThermalLoad(
        solar_w=solar_w,
        conduction_w=conduction_w,
        ventilation_w=ventilation_w,
    )
