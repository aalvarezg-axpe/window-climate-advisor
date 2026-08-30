"""Recommendation-only weather safety policy around optimizer output."""

from dataclasses import dataclass
from enum import StrEnum
from math import cos, isfinite, radians

from .models import BlindOpening, WindowState
from .optimizer import OptimizationResult


class Recommendation(StrEnum):
    """Public advisor recommendation state."""

    OPEN = "open"
    TILT = "tilt"
    CLOSE = "close"
    DEGRADED = "degraded"


class ReasonCode(StrEnum):
    """Stable reason for the policy result."""

    OPTIMIZER = "optimizer"
    WIND_CLOSE = "wind_close"
    WIND_TILT_ONLY = "wind_tilt_only"
    RAIN_CLOSE = "rain_close"
    RAIN_TILT_ONLY = "rain_tilt_only"
    MISSING_SAFETY_DATA = "missing_safety_data"
    STALE_SAFETY_DATA = "stale_safety_data"


@dataclass(frozen=True, slots=True)
class SafetySnapshot:
    """Current weather safety observations; None means unusable input."""

    rain_rate_mm_h: float | None
    gust_kmh: float | None
    wind_direction_deg: float | None
    mean_wind_direction_deg: float | None = None
    stale: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("rain_rate_mm_h", self.rain_rate_mm_h),
            ("gust_kmh", self.gust_kmh),
        ):
            if value is not None and (not isfinite(value) or value < 0):
                raise ValueError(f"{name} must be finite and non-negative")
        for name, value in (
            ("wind_direction_deg", self.wind_direction_deg),
            ("mean_wind_direction_deg", self.mean_wind_direction_deg),
        ):
            if value is not None and (not isfinite(value) or not 0 <= value < 360):
                raise ValueError(f"{name} must be finite and within [0, 360)")


@dataclass(frozen=True, slots=True)
class SafetyGeometry:
    """Opening geometry needed only for façade wind and rain exposure."""

    facade_azimuth_deg: float
    overhang_depth_m: float
    overhang_gap_m: float
    rain_protected: bool

    def __post_init__(self) -> None:
        if (
            not isfinite(self.facade_azimuth_deg)
            or not 0 <= self.facade_azimuth_deg < 360
        ):
            raise ValueError("facade_azimuth_deg must be finite and within [0, 360)")
        for name, value in (
            ("overhang_depth_m", self.overhang_depth_m),
            ("overhang_gap_m", self.overhang_gap_m),
        ):
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and physically valid")


@dataclass(frozen=True, slots=True)
class SafetySettings:
    """Accepted v4.17 weather thresholds and geometry margins."""

    absolute_close_gust_kmh: float = 45
    full_open_frontal_kmh: float = 10
    full_open_leeward_kmh: float = 20
    tilt_frontal_kmh: float = 35
    tilt_leeward_kmh: float = 45
    direction_margin_deg: float = 15
    light_rain_max_mm_h: float = 1.2
    rain_tilt_max_gust_kmh: float = 18
    rain_gust_factor: float = 1.2
    rain_gust_margin_kmh: float = 2
    rain_vertical_speed_kmh: float = 15
    tilt_opening_height_m: float = 0.20
    rain_vertical_margin_m: float = 0.15

    def __post_init__(self) -> None:
        values = (
            self.absolute_close_gust_kmh,
            self.full_open_frontal_kmh,
            self.full_open_leeward_kmh,
            self.tilt_frontal_kmh,
            self.tilt_leeward_kmh,
            self.direction_margin_deg,
            self.light_rain_max_mm_h,
            self.rain_tilt_max_gust_kmh,
            self.rain_gust_factor,
            self.rain_gust_margin_kmh,
            self.rain_vertical_speed_kmh,
            self.tilt_opening_height_m,
            self.rain_vertical_margin_m,
        )
        if any(not isfinite(value) or value < 0 for value in values):
            raise ValueError("safety settings must be finite and non-negative")
        if not (
            self.full_open_frontal_kmh <= self.full_open_leeward_kmh
            and self.tilt_frontal_kmh <= self.tilt_leeward_kmh
            and self.direction_margin_deg <= 90
            and self.light_rain_max_mm_h > 0
            and self.rain_vertical_speed_kmh > 0
            and self.tilt_opening_height_m > 0
        ):
            raise ValueError("safety setting relationships are invalid")


DEFAULT_SAFETY_SETTINGS = SafetySettings()


@dataclass(frozen=True, slots=True)
class PolicyResult:
    """Typed recommendation with no action or service surface."""

    recommendation: Recommendation
    recommended_window_state: WindowState
    recommended_blind: BlindOpening
    safe_to_open: bool
    reason: ReasonCode


def recommendation_for_state(state: WindowState) -> Recommendation:
    """Map a resolved physical target to its public recommendation."""
    return {
        WindowState.CLOSED: Recommendation.CLOSE,
        WindowState.TILT: Recommendation.TILT,
        WindowState.OPEN: Recommendation.OPEN,
    }[state]


def _angular_distance(direction_deg: float, facade_azimuth_deg: float) -> float:
    return abs(((direction_deg - facade_azimuth_deg + 180) % 360) - 180)


def _exposure_factor(
    snapshot: SafetySnapshot, geometry: SafetyGeometry, margin: float
) -> float:
    directions = tuple(
        value
        for value in (snapshot.wind_direction_deg, snapshot.mean_wind_direction_deg)
        if value is not None
    )
    distance = min(
        _angular_distance(direction, geometry.facade_azimuth_deg)
        for direction in directions
    )
    safe_distance = max(distance - margin, 0)
    return cos(radians(safe_distance)) if safe_distance < 90 else 0.0


def _wind_limits(exposure: float, settings: SafetySettings) -> tuple[float, float]:
    full_open = (
        settings.full_open_leeward_kmh
        - (settings.full_open_leeward_kmh - settings.full_open_frontal_kmh) * exposure
    )
    tilt = (
        settings.tilt_leeward_kmh
        - (settings.tilt_leeward_kmh - settings.tilt_frontal_kmh) * exposure
    )
    return full_open, tilt


def _rain_tilt_protected(
    gust_kmh: float,
    exposure: float,
    geometry: SafetyGeometry,
    settings: SafetySettings,
) -> bool:
    if not geometry.rain_protected:
        return False
    facade_gust = (
        gust_kmh * settings.rain_gust_factor + settings.rain_gust_margin_kmh
    ) * exposure
    protected_height = (
        99.0
        if facade_gust < 0.5
        else geometry.overhang_depth_m * settings.rain_vertical_speed_kmh / facade_gust
    )
    return protected_height >= (
        geometry.overhang_gap_m
        + settings.tilt_opening_height_m
        + settings.rain_vertical_margin_m
    )


def _result(
    recommendation: Recommendation,
    state: WindowState,
    blind: BlindOpening,
    safe_to_open: bool,
    reason: ReasonCode,
) -> PolicyResult:
    return PolicyResult(recommendation, state, blind, safe_to_open, reason)


def apply_weather_policy(
    optimized: OptimizationResult,
    snapshot: SafetySnapshot,
    geometry: SafetyGeometry,
    *,
    supports_tilt: bool,
    settings: SafetySettings = DEFAULT_SAFETY_SETTINGS,
) -> PolicyResult:
    """Restrict an optimizer recommendation through absolute weather safety."""
    blind = optimized.best.action.blind
    if snapshot.stale:
        return _result(
            Recommendation.DEGRADED,
            WindowState.CLOSED,
            blind,
            False,
            ReasonCode.STALE_SAFETY_DATA,
        )
    if (
        snapshot.rain_rate_mm_h is None
        or snapshot.gust_kmh is None
        or (
            snapshot.wind_direction_deg is None
            and snapshot.mean_wind_direction_deg is None
        )
    ):
        return _result(
            Recommendation.DEGRADED,
            WindowState.CLOSED,
            blind,
            False,
            ReasonCode.MISSING_SAFETY_DATA,
        )

    exposure = _exposure_factor(snapshot, geometry, settings.direction_margin_deg)
    full_open_limit, tilt_limit = _wind_limits(exposure, settings)
    candidate_state = optimized.best.action.window_state

    if snapshot.gust_kmh >= settings.absolute_close_gust_kmh:
        return _result(
            Recommendation.CLOSE,
            WindowState.CLOSED,
            blind,
            False,
            ReasonCode.WIND_CLOSE,
        )

    if snapshot.rain_rate_mm_h > 0:
        tilt_protected = _rain_tilt_protected(
            snapshot.gust_kmh, exposure, geometry, settings
        )
        if (
            snapshot.rain_rate_mm_h <= settings.light_rain_max_mm_h
            and snapshot.gust_kmh < settings.rain_tilt_max_gust_kmh
            and tilt_protected
            and supports_tilt
            and candidate_state is not WindowState.CLOSED
        ):
            return _result(
                Recommendation.TILT,
                WindowState.TILT,
                blind,
                True,
                ReasonCode.RAIN_TILT_ONLY,
            )
        return _result(
            Recommendation.CLOSE,
            WindowState.CLOSED,
            blind,
            False,
            ReasonCode.RAIN_CLOSE,
        )

    if snapshot.gust_kmh >= settings.tilt_frontal_kmh:
        if (
            candidate_state is not WindowState.CLOSED
            and supports_tilt
            and snapshot.gust_kmh < tilt_limit
        ):
            return _result(
                Recommendation.TILT,
                WindowState.TILT,
                blind,
                True,
                ReasonCode.WIND_TILT_ONLY,
            )
        return _result(
            Recommendation.CLOSE,
            WindowState.CLOSED,
            blind,
            False,
            ReasonCode.WIND_CLOSE,
        )

    if candidate_state is WindowState.OPEN and snapshot.gust_kmh >= full_open_limit:
        if supports_tilt and snapshot.gust_kmh < tilt_limit:
            return _result(
                Recommendation.TILT,
                WindowState.TILT,
                blind,
                True,
                ReasonCode.WIND_TILT_ONLY,
            )
        return _result(
            Recommendation.CLOSE,
            WindowState.CLOSED,
            blind,
            False,
            ReasonCode.WIND_CLOSE,
        )
    return _result(
        recommendation_for_state(candidate_state),
        candidate_state,
        blind,
        True,
        ReasonCode.OPTIMIZER,
    )
