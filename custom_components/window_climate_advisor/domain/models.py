"""Typed inputs shared by the pure thermal domain."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


def _require_finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


class WindowState(StrEnum):
    """Candidate physical state of an opening."""

    CLOSED = "closed"
    TILT = "tilt"
    OPEN = "open"


@dataclass(frozen=True, slots=True)
class OpeningDimensions:
    """Rectangular opening dimensions in metres."""

    width_m: float
    height_m: float

    def __post_init__(self) -> None:
        for name, value in (("width_m", self.width_m), ("height_m", self.height_m)):
            _require_finite(name, value)
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

    @property
    def area_m2(self) -> float:
        """Return the rectangular area in square metres."""
        return self.width_m * self.height_m


@dataclass(frozen=True, slots=True)
class BlindOpening:
    """Recommended blind opening: 0% closed, 100% raised."""

    percent: float

    def __post_init__(self) -> None:
        _require_finite("blind opening", self.percent)
        if not 0 <= self.percent <= 100:
            raise ValueError("blind opening must be between 0 and 100 percent")

    @property
    def fraction(self) -> float:
        """Return the opening as a 0-1 fraction."""
        return self.percent / 100


@dataclass(frozen=True, slots=True)
class ThermalConditions:
    """Environmental observations in explicit domain units."""

    indoor_temperature_c: float
    outdoor_temperature_c: float
    facade_irradiance_w_m2: float
    wind_speed_kmh: float = 0
    gust_speed_kmh: float = 0

    def __post_init__(self) -> None:
        values = (
            ("indoor_temperature_c", self.indoor_temperature_c, False),
            ("outdoor_temperature_c", self.outdoor_temperature_c, False),
            ("facade_irradiance_w_m2", self.facade_irradiance_w_m2, True),
            ("wind_speed_kmh", self.wind_speed_kmh, True),
            ("gust_speed_kmh", self.gust_speed_kmh, True),
        )
        for name, value, non_negative in values:
            _require_finite(name, value)
            if non_negative and value < 0:
                raise ValueError(f"{name} must not be negative")
