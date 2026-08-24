"""Tests for opening and blind geometry."""

import math

import pytest

from custom_components.window_climate_advisor.domain.geometry import (
    blind_solar_factor,
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
