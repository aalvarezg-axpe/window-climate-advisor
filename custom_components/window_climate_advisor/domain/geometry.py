"""Opening and blind geometry used by the thermal model."""

from math import isfinite

from .models import BlindOpening, WindowState


def opening_fraction(state: WindowState, *, tilt_fraction: float = 0.12) -> float:
    """Return the free opening fraction before blind obstruction."""
    if not isfinite(tilt_fraction) or not 0 < tilt_fraction <= 1:
        raise ValueError("tilt_fraction must be finite and within (0, 1]")
    return {
        WindowState.CLOSED: 0.0,
        WindowState.TILT: tilt_fraction,
        WindowState.OPEN: 1.0,
    }[state]


def blind_solar_factor(blind: BlindOpening, *, closed_residual: float = 0.15) -> float:
    """Return linear solar transmission through the blind-covered area."""
    if not isfinite(closed_residual) or not 0 <= closed_residual <= 1:
        raise ValueError("closed_residual must be finite and within [0, 1]")
    return closed_residual + blind.fraction * (1 - closed_residual)
