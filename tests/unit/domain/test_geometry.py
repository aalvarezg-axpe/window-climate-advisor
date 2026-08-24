"""Tests for opening and blind geometry."""

import math

import pytest

from custom_components.window_climate_advisor.domain.geometry import (
    blind_solar_factor,
    facade_irradiance_w_m2,
    opening_fraction,
)
from custom_components.window_climate_advisor.domain.models import (
    BlindOpening,
    OpeningDimensions,
    WindowState,
)


def test_dimensions_and_blind_opening_enforce_physical_bounds() -> None:
    """Reject non-finite, non-positive, and out-of-range geometry."""
    assert OpeningDimensions(1.6, 1.2).area_m2 == pytest.approx(1.92)
    assert BlindOpening(35).fraction == pytest.approx(0.35)

    for value in (0, -1, math.inf, math.nan):
        with pytest.raises(ValueError):
            OpeningDimensions(value, 1.2)
    for value in (-0.01, 100.01, math.inf, math.nan):
        with pytest.raises(ValueError):
            BlindOpening(value)


def test_window_state_fraction_uses_the_explicit_tilt_assumption() -> None:
    """Map closed, tilt, and open to their auditable free fractions."""
    assert opening_fraction(WindowState.CLOSED) == 0
    assert opening_fraction(WindowState.TILT) == pytest.approx(0.12)
    assert opening_fraction(WindowState.OPEN) == 1
    assert opening_fraction(WindowState.TILT, tilt_fraction=0.2) == 0.2

    for value in (0, -0.1, 1.1, math.inf, math.nan):
        with pytest.raises(ValueError):
            opening_fraction(WindowState.TILT, tilt_fraction=value)


def test_blind_solar_factor_is_bounded_monotonic_and_sensitive() -> None:
    """Interpolate from the provisional closed residual to full transmission."""
    factors = [blind_solar_factor(BlindOpening(value)) for value in (0, 25, 100)]
    assert factors == pytest.approx([0.15, 0.3625, 1])
    assert factors == sorted(factors)
    assert blind_solar_factor(BlindOpening(0), closed_residual=0.3) == 0.3

    for residual in (-0.1, 1.1, math.inf, math.nan):
        with pytest.raises(ValueError):
            blind_solar_factor(BlindOpening(50), closed_residual=residual)


def test_facade_projection_distinguishes_front_side_rear_and_low_sun() -> None:
    """Project only bounded direct sun in front plus the diffuse component."""

    def project(facade: float, elevation: float = 30) -> float:
        return facade_irradiance_w_m2(
            800,
            180,
            elevation,
            facade,
            1.2,
            0,
            0,
        )

    front = project(180)
    side = project(100)
    rear = project(0)
    assert 0 <= rear < side < front <= 800 * 1.8
    assert front == pytest.approx(1297.794549)
    assert side == pytest.approx(324.521877)
    assert rear == pytest.approx(800 * 0.15)
    assert project(180, elevation=3) == pytest.approx(rear)
    assert facade_irradiance_w_m2(0, 180, 30, 180, 1.2, 0, 0) == 0
    assert facade_irradiance_w_m2(800, 350, 30, 10, 1.2, 0, 0) == pytest.approx(
        facade_irradiance_w_m2(800, 10, 30, 350, 1.2, 0, 0)
    )


def test_deeper_overhang_monotonically_reduces_high_sun() -> None:
    """Shade more of the same opening as overhang depth increases."""
    irradiance = [
        facade_irradiance_w_m2(800, 180, 60, 180, 1.2, depth, 0)
        for depth in (0, 0.5, 1)
    ]
    assert irradiance == sorted(irradiance, reverse=True)
    assert irradiance[0] > irradiance[1] > irradiance[2]
    assert irradiance[2] == pytest.approx(800 * 0.15)


@pytest.mark.parametrize(
    "args",
    [
        (-1, 180, 30, 180, 1.2, 0, 0),
        (800, 360, 30, 180, 1.2, 0, 0),
        (800, 180, 91, 180, 1.2, 0, 0),
        (800, 180, 30, 180, 0, 0, 0),
        (800, 180, 30, 180, 1.2, -1, 0),
        (math.nan, 180, 30, 180, 1.2, 0, 0),
    ],
)
def test_facade_projection_rejects_invalid_geometry(
    args: tuple[float, ...],
) -> None:
    """Reject non-finite and out-of-range solar geometry."""
    with pytest.raises(ValueError):
        facade_irradiance_w_m2(*args)

    with pytest.raises(ValueError):
        facade_irradiance_w_m2(
            800,
            180,
            30,
            180,
            1.2,
            0,
            0,
            diffuse_vertical_fraction=1.1,
        )
