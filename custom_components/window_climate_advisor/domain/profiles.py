"""Seasonal comfort profiles and deterministic selection."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class Season(StrEnum):
    """Configured comfort profile."""

    SUMMER = "summer"
    SHOULDER = "shoulder"
    WINTER = "winter"


class SelectionMode(StrEnum):
    """Automatic selection or a manual season override."""

    AUTO = "auto"
    SUMMER = "summer"
    SHOULDER = "shoulder"
    WINTER = "winter"


@dataclass(frozen=True, slots=True)
class ComfortProfile:
    """One bounded comfort band in degrees Celsius."""

    lower_c: float
    upper_c: float
    preconditioning_target_c: float
    hysteresis_c: float

    def __post_init__(self) -> None:
        values = (
            self.lower_c,
            self.upper_c,
            self.preconditioning_target_c,
            self.hysteresis_c,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("comfort profile values must be finite")
        if self.lower_c >= self.upper_c:
            raise ValueError("comfort lower bound must be below upper bound")
        if not self.lower_c <= self.preconditioning_target_c <= self.upper_c:
            raise ValueError("preconditioning target must lie within comfort bounds")
        if not 0 < self.hysteresis_c <= self.upper_c - self.lower_c:
            raise ValueError("hysteresis must be positive and no wider than the band")


@dataclass(frozen=True, slots=True)
class ComfortProfiles:
    """Complete seasonal comfort configuration."""

    summer: ComfortProfile
    shoulder: ComfortProfile
    winter: ComfortProfile

    def for_season(self, season: Season) -> ComfortProfile:
        """Return the profile selected by a typed season."""
        return {
            Season.SUMMER: self.summer,
            Season.SHOULDER: self.shoulder,
            Season.WINTER: self.winter,
        }[season]


@dataclass(frozen=True, slots=True)
class AutoSelectionCalibration:
    """Historical thresholds used only to choose a profile automatically."""

    warm_daily_max_c: float = 25
    cold_history_max_c: float = 21
    summer_months: tuple[int, ...] = (6, 7, 8, 9)
    winter_months: tuple[int, ...] = (11, 12, 1, 2, 3)

    def __post_init__(self) -> None:
        if not (
            isfinite(self.warm_daily_max_c)
            and isfinite(self.cold_history_max_c)
            and self.cold_history_max_c < self.warm_daily_max_c
        ):
            raise ValueError("automatic temperature thresholds are invalid")
        months = (*self.summer_months, *self.winter_months)
        if any(month not in range(1, 13) for month in months):
            raise ValueError("automatic season months must be within 1..12")
        if set(self.summer_months) & set(self.winter_months):
            raise ValueError("automatic summer and winter months must not overlap")


DEFAULT_AUTO_SELECTION = AutoSelectionCalibration()


def _complete_values(values: Sequence[float | None]) -> tuple[float, ...] | None:
    """Return a finite complete sequence or explicit incompleteness."""
    if not values or any(value is None or not isfinite(value) for value in values):
        return None
    return tuple(value for value in values if value is not None)


def temperate_season(
    forecast_daily_max_c: Sequence[float | None],
    history_daily_max_c: Sequence[float | None],
    calibration: AutoSelectionCalibration = DEFAULT_AUTO_SELECTION,
) -> Season:
    """Select a season from strict forecast/history boundaries."""
    forecast = _complete_values(forecast_daily_max_c)
    if forecast and all(value < calibration.warm_daily_max_c for value in forecast):
        return Season.WINTER
    if forecast and all(value > calibration.warm_daily_max_c for value in forecast):
        return Season.SUMMER

    history = _complete_values(history_daily_max_c)
    if history and max(history) > calibration.warm_daily_max_c:
        return Season.SUMMER
    if history and max(history) < calibration.cold_history_max_c:
        return Season.WINTER
    return Season.SHOULDER


def select_season(
    mode: SelectionMode,
    profiles: ComfortProfiles,
    *,
    month: int,
    indoor_min_c: float | None,
    indoor_max_c: float | None,
    forecast_daily_max_c: Sequence[float | None] = (),
    history_daily_max_c: Sequence[float | None] = (),
    calibration: AutoSelectionCalibration = DEFAULT_AUTO_SELECTION,
) -> Season:
    """Resolve manual override or the deterministic automatic profile."""
    if mode is not SelectionMode.AUTO:
        return Season(mode.value)
    if month not in range(1, 13):
        raise ValueError("month must be within 1..12")

    if (
        indoor_max_c is not None
        and isfinite(indoor_max_c)
        and indoor_max_c >= profiles.summer.upper_c - profiles.summer.hysteresis_c
    ):
        return Season.SUMMER
    if month in calibration.summer_months:
        return Season.SUMMER
    if (
        indoor_min_c is not None
        and isfinite(indoor_min_c)
        and indoor_min_c <= profiles.winter.lower_c + profiles.winter.hysteresis_c
    ):
        return Season.WINTER
    if month in calibration.winter_months:
        return Season.WINTER
    return temperate_season(
        forecast_daily_max_c,
        history_daily_max_c,
        calibration,
    )
