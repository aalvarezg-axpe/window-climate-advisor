"""Tests for seasonal comfort profiles and selection."""

import math

import pytest

from custom_components.window_climate_advisor.domain.profiles import (
    AutoSelectionCalibration,
    ComfortProfile,
    ComfortProfiles,
    Season,
    SelectionMode,
    select_season,
    temperate_season,
)

PROFILES = ComfortProfiles(
    summer=ComfortProfile(22, 25, 23, 0.5),
    shoulder=ComfortProfile(20, 24, 22, 0.5),
    winter=ComfortProfile(19, 23, 21, 0.5),
)


def test_profiles_are_complete_typed_and_bounded() -> None:
    """Return every typed profile and reject inconsistent comfort bands."""
    assert PROFILES.for_season(Season.SUMMER).upper_c == 25
    assert PROFILES.for_season(Season.SHOULDER).preconditioning_target_c == 22
    assert PROFILES.for_season(Season.WINTER).lower_c == 19

    for values in (
        (24, 24, 24, 0.5),
        (25, 24, 24.5, 0.5),
        (20, 24, 19, 0.5),
        (20, 24, 25, 0.5),
        (20, 24, 22, 0),
        (20, 24, 22, 4.1),
        (20, math.inf, 22, 0.5),
    ):
        with pytest.raises(ValueError):
            ComfortProfile(*values)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (SelectionMode.SUMMER, Season.SUMMER),
        (SelectionMode.SHOULDER, Season.SHOULDER),
        (SelectionMode.WINTER, Season.WINTER),
    ],
)
def test_manual_override_ignores_automatic_inputs(
    mode: SelectionMode, expected: Season
) -> None:
    """Return the manual season without consulting observations."""
    assert (
        select_season(
            mode,
            PROFILES,
            month=99,
            indoor_min_c=None,
            indoor_max_c=None,
        )
        is expected
    )


def test_automatic_indoor_and_calendar_boundaries_have_frozen_precedence() -> None:
    """Apply indoor boundaries before the historical calendar months."""
    assert (
        select_season(
            SelectionMode.AUTO,
            PROFILES,
            month=1,
            indoor_min_c=21,
            indoor_max_c=24.5,
        )
        is Season.SUMMER
    )
    assert (
        select_season(
            SelectionMode.AUTO,
            PROFILES,
            month=6,
            indoor_min_c=19.5,
            indoor_max_c=22,
        )
        is Season.SUMMER
    )
    assert (
        select_season(
            SelectionMode.AUTO,
            PROFILES,
            month=4,
            indoor_min_c=19.5,
            indoor_max_c=22,
        )
        is Season.WINTER
    )
    assert (
        select_season(
            SelectionMode.AUTO,
            PROFILES,
            month=11,
            indoor_min_c=21,
            indoor_max_c=22,
        )
        is Season.WINTER
    )

    with pytest.raises(ValueError):
        select_season(
            SelectionMode.AUTO,
            PROFILES,
            month=13,
            indoor_min_c=None,
            indoor_max_c=None,
        )


def test_temperate_selection_preserves_strict_forecast_history_boundaries() -> None:
    """Characterize catalog case C020 including exact threshold fallbacks."""
    assert temperate_season([22, 24.9], [26]) is Season.WINTER
    assert temperate_season([25.1, 28], [20]) is Season.SUMMER
    assert temperate_season([24, 27], [23, 25.1]) is Season.SUMMER
    assert temperate_season([24, 27], [20, 20.9]) is Season.WINTER
    assert temperate_season([24, 25], [26]) is Season.SUMMER
    assert temperate_season([24, 27], [20, 21]) is Season.SHOULDER


def test_missing_or_non_finite_sequences_remain_shoulder_season() -> None:
    """Do not turn incomplete observations into warm or cold evidence."""
    assert temperate_season([], []) is Season.SHOULDER
    assert temperate_season([24, None], []) is Season.SHOULDER
    assert temperate_season([math.nan], [math.inf]) is Season.SHOULDER
    assert (
        select_season(
            SelectionMode.AUTO,
            PROFILES,
            month=5,
            indoor_min_c=math.nan,
            indoor_max_c=math.inf,
        )
        is Season.SHOULDER
    )


def test_selection_calibration_rejects_invalid_thresholds_and_months() -> None:
    """Keep auto-selection calibration finite, ordered, and unambiguous."""
    for kwargs in (
        {"warm_daily_max_c": math.nan},
        {"warm_daily_max_c": 20, "cold_history_max_c": 21},
        {"summer_months": (0,)},
        {"winter_months": (13,)},
        {"summer_months": (6,), "winter_months": (6,)},
    ):
        with pytest.raises(ValueError):
            AutoSelectionCalibration(**kwargs)
