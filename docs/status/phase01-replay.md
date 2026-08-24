# Phase 01 seasonal replay

- Task: `P01-T08`
- Date: 2026-08-25
- Local status: verified; owner decisions recorded
- Fixture: `tests/fixtures/replay/seasonal_v1.json`, schema 1
- Baseline: characterized v4.17 actions stored per segment with Cxxx sources

## Evidence boundary

The replay contains three synthetic three-day scenarios at 30-minute
resolution: Summer, Shoulder-season, and Winter. It is not measured household
history. Each scenario repeats a reviewable 24-hour set of segments and covers
all six F04-08 requirements: Summer at 25 °C outdoors, nocturnal pre-cooling,
Winter solar gain above 24 °C indoors, no wind, partial solar exposure, and an
adverse forecast. Absolute gust and rain segments verify safety priority.

No legacy evaluator was created. The fixture stores the characterized v4.17
action and its catalog sources for each segment. Both that action and the new
stable recommendation are scored through the same current physical model.

The comfort value is the optimizer's signed seasonal objective integrated over
time; lower is better. Net thermal energy is also signed: positive heats the
room and negative removes heat. Neither number is electrical consumption or a
room-temperature forecast because the project has no calibrated room thermal
capacity model.

## Nominal comparison

| Scenario | Comfort new / v4.17 (Wh-eq) | Net heat new / v4.17 (Wh) | Stable transitions new / v4.17 | Candidates | Churn | Safety violations new / v4.17 |
|---|---:|---:|---:|---:|---:|---:|
| Summer preconditioning | -16,267.2 / -14,961.9 | -18,848.4 / -17,893.2 | 12 / 9 | 12 | 0 | 0 / 0 |
| Shoulder partial exposure | -16,883.2 / -8,567.1 | -16,883.2 / -8,567.1 | 13 / 13 | 13 | 0 | 0 / 0 |
| Winter solar gain | 815.1 / 18,632.4 | 5,433.6 / 26,661.9 | 5 / 6 | 5 | 0 | 0 / 0 |
| **Aggregate** | **-32,335.3 / -4,896.6** | **-30,298.0 / 201.6** | **30 / 28** | **30** | **0** | **0 / 0** |

Every candidate maps one-to-one to a stable action transition and occurs at a
segment boundary or its first confirmation sample. The two-transition count
increase over v4.17 is therefore a behavioural difference, but not percentage
drift, a duplicate, or intra-segment oscillation. Each evaluation still yields
at most one grouped value and delivers nothing. No stable or transient replay
action pairs a non-closed window with 0% blind opening.

## Sensitivity

The provisional closed-blind solar residual was varied from 0.15 nominal to
0.05 and 0.25. Tilt free-opening fraction was varied with it from 0.12 to 0.08
and 0.18. These are conservative test bounds, not measurements.

| Calibration | Aggregate comfort new / v4.17 (Wh-eq) | Net heat new / v4.17 (Wh) | Transitions new / v4.17 | Churn | Safety violations |
|---|---:|---:|---:|---:|---:|
| Low residual / tilt | -38,566.3 / -8,233.1 | -35,583.8 / -1,829.7 | 30 / 28 | 0 | 0 |
| Nominal | -32,335.3 / -4,896.6 | -30,298.0 / 201.6 | 30 / 28 | 0 | 0 |
| High residual / tilt | -27,743.5 / -1,631.1 | -26,516.5 / 2,161.9 | 32 / 28 | 0 | 0 |

The action mix changes under the high bound, as expected for uncalibrated
physics, but safety and stability do not. The new objective remains lower than
the v4.17 reference at both bounds. Operational calibration still belongs to
the shadow period and must not be described as measured.

## Owner decision and corrected difference

1. At partial sun (300 W/m²), 25 °C indoors, 21 °C outdoors, and no wind, the
   joint model keeps `open/100%` instead of the static v4.17 `closed/50%`.
   Stack ventilation provides more modeled cooling than the admitted solar
   load; this is the intended replacement of the disconnected blind rule. The
   owner accepted this difference on 2026-08-25.
2. The owner rejected the former adverse-forecast `tilt/0%` result. P01-T04
   removed non-closed/0% candidates, and P01-T07 coordinated stable joint
   transitions and `hold`. The adverse segment now yields `closed/0%`, matching
   v4.17, and the replay asserts the invariant over every observed action.
3. The owner accepted 33 stable transitions/candidates versus 28 raw v4.17
   transitions on 2026-08-25 because they had zero churn or duplicates. The
   coherence correction groups three intermediate transitions, reducing the
   nominal result to 30/28 without introducing a new behavioural category; the
   remaining two meaningful changes still belong in shadow observation before
   any notification feature is considered.

These decisions permit P01-T09 to connect the engine as informational entities
only. They do not approve a notification delivery path, actuator control, or
deployment; v4.17 remains unchanged and is still the rollback.

## Verification

Focused command:

```powershell
wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/replay -q'
```

Result: 5 passed. The canonical repository gate passed 100 tests with 684
statements and 214 branches at 100% coverage.
