"""Tests for conservative unilateral airflow."""

import math

import pytest

from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    OpeningDimensions,
    ThermalConditions,
    WindowState,
)
from custom_components.window_climate_advisor.domain.ventilation import (
    AirflowCalibration,
    effective_free_area_m2,
    unilateral_airflow_m3_s,
)

DIMENSIONS = OpeningDimensions(1.6, 1.2)
CONDITIONS = ThermalConditions(27, 22, 0, wind_speed_kmh=8, gust_speed_kmh=12)


def test_effective_free_area_couples_window_and_blind_opening() -> None:
    """Scale usable area by both physical window state and blind opening."""
    assert (
        effective_free_area_m2(DIMENSIONS, WindowState.CLOSED, BlindOpening(100)) == 0
    )
    assert effective_free_area_m2(
        DIMENSIONS, WindowState.TILT, BlindOpening(100)
    ) == pytest.approx(1.92 * 0.12)
    assert effective_free_area_m2(
        DIMENSIONS, WindowState.OPEN, BlindOpening(50)
    ) == pytest.approx(1.92 * 0.5)
    assert effective_free_area_m2(DIMENSIONS, WindowState.OPEN, BlindOpening(0)) == 0


def test_airflow_matches_the_historical_expression_and_scales_monotonically() -> None:
    """Preserve the unilateral formula while varying usable blind area."""
    expected_driver = max(
        0.001 * (max(8, 0.35 * 12) / 3.6) ** 2,
        0.0035 * 1.2 * 5,
    )
    expected_full = 1.92 / 2 * math.sqrt(expected_driver)
    full = unilateral_airflow_m3_s(
        DIMENSIONS, WindowState.OPEN, BlindOpening(100), CONDITIONS
    )
    half = unilateral_airflow_m3_s(
        DIMENSIONS, WindowState.OPEN, BlindOpening(50), CONDITIONS
    )
    tilt = unilateral_airflow_m3_s(
        DIMENSIONS, WindowState.TILT, BlindOpening(100), CONDITIONS
    )

    assert full == pytest.approx(expected_full)
    assert half == pytest.approx(full * 0.5)
    assert tilt == pytest.approx(full * 0.12)
    assert (
        unilateral_airflow_m3_s(
            DIMENSIONS, WindowState.CLOSED, BlindOpening(100), CONDITIONS
        )
        == 0
    )


def test_conditions_and_airflow_calibration_reject_invalid_values() -> None:
    """Keep malformed observations and coefficients outside the model."""
    for kwargs in (
        {"indoor_temperature_c": math.nan},
        {"outdoor_temperature_c": math.inf},
        {"facade_irradiance_w_m2": -1},
        {"wind_speed_kmh": -1},
        {"gust_speed_kmh": -1},
    ):
        values = {
            "indoor_temperature_c": 20,
            "outdoor_temperature_c": 15,
            "facade_irradiance_w_m2": 0,
            **kwargs,
        }
        with pytest.raises(ValueError):
            ThermalConditions(**values)

    for kwargs in (
        {"tilt_opening_fraction": 0},
        {"tilt_opening_fraction": 1.1},
        {"gust_speed_factor": -1},
        {"wind_coefficient": -1},
        {"stack_coefficient": math.nan},
    ):
        with pytest.raises(ValueError):
            AirflowCalibration(**kwargs)
