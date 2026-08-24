"""Opening and blind geometry used by the thermal model."""

from math import cos, isfinite, radians, sin, tan

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


def facade_irradiance_w_m2(
    global_horizontal_w_m2: float,
    sun_azimuth_deg: float,
    sun_elevation_deg: float,
    facade_azimuth_deg: float,
    opening_height_m: float,
    overhang_depth_m: float,
    overhang_gap_m: float,
    *,
    diffuse_vertical_fraction: float = 0.15,
) -> float:
    """Project global radiation onto a shaded vertical opening plane."""
    values = (
        global_horizontal_w_m2,
        sun_azimuth_deg,
        sun_elevation_deg,
        facade_azimuth_deg,
        opening_height_m,
        overhang_depth_m,
        overhang_gap_m,
        diffuse_vertical_fraction,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("solar geometry values must be finite")
    if global_horizontal_w_m2 < 0:
        raise ValueError("global irradiance must be non-negative")
    if not 0 <= sun_azimuth_deg < 360 or not 0 <= facade_azimuth_deg < 360:
        raise ValueError("azimuths must be within [0, 360)")
    if not -90 <= sun_elevation_deg <= 90:
        raise ValueError("sun elevation must be within [-90, 90]")
    if opening_height_m <= 0 or overhang_depth_m < 0 or overhang_gap_m < 0:
        raise ValueError("opening and overhang dimensions are invalid")
    if not 0 <= diffuse_vertical_fraction <= 1:
        raise ValueError("diffuse vertical fraction must be within [0, 1]")

    incidence_deg = abs(((sun_azimuth_deg - facade_azimuth_deg + 180) % 360) - 180)
    sun_in_front = (
        sun_elevation_deg > 3 and incidence_deg <= 80 and global_horizontal_w_m2 >= 20
    )
    projection = 0.0
    unshaded_fraction = 0.0
    if sun_in_front:
        elevation_rad = radians(sun_elevation_deg)
        incidence_rad = radians(incidence_deg)
        vertical_shadow_m = overhang_depth_m * tan(elevation_rad) / cos(incidence_rad)
        unshaded_fraction = min(
            max(
                (overhang_gap_m + opening_height_m - vertical_shadow_m)
                / opening_height_m,
                0.0,
            ),
            1.0,
        )
        projection = min(
            max(
                cos(elevation_rad) * cos(incidence_rad) / max(sin(elevation_rad), 0.25),
                0.0,
            ),
            2.0,
        )
    factor = min(
        max(
            diffuse_vertical_fraction
            + (1 - diffuse_vertical_fraction) * projection * unshaded_fraction,
            0.0,
        ),
        1.8,
    )
    return global_horizontal_w_m2 * factor
