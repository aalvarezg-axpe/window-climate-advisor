"""Tests for coupled window/blind thermal load."""

import math

import pytest

from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    OpeningDimensions,
    ThermalConditions,
    WindowState,
)
from custom_components.window_climate_advisor.domain.thermal import (
    ThermalCalibration,
    ThermalLoad,
    candidate_thermal_load,
)
from custom_components.window_climate_advisor.domain.ventilation import (
    AirflowCalibration,
)

DIMENSIONS = OpeningDimensions(1.6, 1.2)


def test_closed_load_uses_glazing_and_has_no_ventilation() -> None:
    """Apply SHGC and U-value to a closed window in explicit watts."""
    conditions = ThermalConditions(27, 22, 500)
    load = candidate_thermal_load(
        DIMENSIONS, WindowState.CLOSED, BlindOpening(100), conditions
    )

    assert load.solar_w == pytest.approx(500 * 1.92 * 0.55)
    assert load.conduction_w == pytest.approx(1.4 * 1.92 * -5)
    assert load.ventilation_w == 0
    assert load.total_w == pytest.approx(
        load.solar_w + load.conduction_w + load.ventilation_w
    )


def test_solar_gain_can_reverse_an_opening_that_otherwise_cools() -> None:
    """Characterize the accepted sign reversal from catalog case C014."""
    without_sun = candidate_thermal_load(
        DIMENSIONS,
        WindowState.OPEN,
        BlindOpening(100),
        ThermalConditions(27, 22, 0, wind_speed_kmh=8, gust_speed_kmh=12),
    )
    with_sun = candidate_thermal_load(
        DIMENSIONS,
        WindowState.OPEN,
        BlindOpening(100),
        ThermalConditions(27, 22, 1200, wind_speed_kmh=8, gust_speed_kmh=12),
    )

    assert without_sun.total_w < -150
    assert with_sun.total_w > 0
    assert with_sun.solar_w > without_sun.solar_w


def test_blind_opening_changes_solar_and_ventilation_monotonically() -> None:
    """Expose both sides of the coupled blind sensitivity for optimization."""
    conditions = ThermalConditions(27, 22, 600, wind_speed_kmh=8, gust_speed_kmh=12)
    loads = [
        candidate_thermal_load(
            DIMENSIONS, WindowState.OPEN, BlindOpening(percent), conditions
        )
        for percent in range(0, 101, 10)
    ]

    assert [load.solar_w for load in loads] == sorted(load.solar_w for load in loads)
    assert [abs(load.ventilation_w) for load in loads] == sorted(
        abs(load.ventilation_w) for load in loads
    )
    assert loads[0].ventilation_w == 0


def test_direct_sun_exposes_the_linear_airflow_tradeoff() -> None:
    """Bound where the assumed ventilation gain can reverse admitted sun."""
    percentages = range(0, 101, 10)

    def totals(irradiance_w_m2: float) -> list[float]:
        conditions = ThermalConditions(
            27,
            22,
            irradiance_w_m2,
            wind_speed_kmh=8,
            gust_speed_kmh=12,
        )
        return [
            candidate_thermal_load(
                DIMENSIONS,
                WindowState.OPEN,
                BlindOpening(percent),
                conditions,
            ).total_w
            for percent in percentages
        ]

    assert totals(300) == sorted(totals(300), reverse=True)
    assert totals(600) == sorted(totals(600))


def test_tilt_mix_and_closed_blind_residual_are_explicitly_sensitive() -> None:
    """Vary the two provisional assumptions without hiding calibration."""
    conditions = ThermalConditions(22, 22, 1000)
    default_tilt = candidate_thermal_load(
        DIMENSIONS, WindowState.TILT, BlindOpening(100), conditions
    )
    wider_tilt = candidate_thermal_load(
        DIMENSIONS,
        WindowState.TILT,
        BlindOpening(100),
        conditions,
        ThermalCalibration(airflow=AirflowCalibration(tilt_opening_fraction=0.24)),
    )
    low_residual = candidate_thermal_load(
        DIMENSIONS,
        WindowState.CLOSED,
        BlindOpening(0),
        conditions,
        ThermalCalibration(closed_blind_solar_residual=0.1),
    )
    high_residual = candidate_thermal_load(
        DIMENSIONS,
        WindowState.CLOSED,
        BlindOpening(0),
        conditions,
        ThermalCalibration(closed_blind_solar_residual=0.3),
    )

    assert wider_tilt.solar_w > default_tilt.solar_w
    assert high_residual.solar_w > low_residual.solar_w


def test_thermal_calibration_and_load_contract_are_bounded() -> None:
    """Reject impossible coefficients and preserve the component sum."""
    for kwargs in (
        {"glazing_shgc": -0.1},
        {"glazing_shgc": 1.1},
        {"glazing_u_w_m2k": 0},
        {"air_density_kg_m3": math.inf},
        {"air_heat_capacity_j_kgk": -1},
        {"closed_blind_solar_residual": math.nan},
    ):
        with pytest.raises(ValueError):
            ThermalCalibration(**kwargs)

    assert ThermalLoad(1, -2, 3).total_w == 2
