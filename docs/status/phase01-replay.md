# Phase 01 seasonal replay

- Task: `P01-T08`
- Date: 2026-08-24
- Local status: verified; owner decision required
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
| Summer preconditioning | -15,621.8 / -14,961.9 | -18,406.7 / -17,893.2 | 15 / 9 | 15 | 0 | 0 / 0 |
| Shoulder partial exposure | -16,729.6 / -8,567.1 | -16,729.6 / -8,567.1 | 13 / 13 | 13 | 0 | 0 / 0 |
| Winter solar gain | 815.1 / 18,632.4 | 5,433.6 / 26,661.9 | 5 / 6 | 5 | 0 | 0 / 0 |
| **Aggregate** | **-31,536.3 / -4,896.6** | **-29,702.7 / 201.6** | **33 / 28** | **33** | **0** | **0 / 0** |

Every candidate maps one-to-one to a stable action transition and occurs at a
segment boundary or its first confirmation sample. The five-transition count
increase over v4.17 is therefore a behavioural difference, but not percentage
drift, a duplicate, or intra-segment oscillation. Each evaluation still yields
at most one grouped value and delivers nothing.

## Sensitivity

The provisional closed-blind solar residual was varied from 0.15 nominal to
0.05 and 0.25. Tilt free-opening fraction was varied with it from 0.12 to 0.08
and 0.18. These are conservative test bounds, not measurements.

| Calibration | Aggregate comfort new / v4.17 (Wh-eq) | Net heat new / v4.17 (Wh) | Transitions new / v4.17 | Churn | Safety violations |
|---|---:|---:|---:|---:|---:|
| Low residual / tilt | -37,687.6 / -8,233.1 | -34,752.8 / -1,829.7 | 33 / 28 | 0 | 0 |
| Nominal | -31,536.3 / -4,896.6 | -29,702.7 / 201.6 | 33 / 28 | 0 | 0 |
| High residual / tilt | -27,408.1 / -1,631.1 | -26,181.2 / 2,161.9 | 32 / 28 | 0 | 0 |

The action mix changes under the high bound, as expected for uncalibrated
physics, but safety and stability do not. The new objective remains lower than
the v4.17 reference at both bounds. Operational calibration still belongs to
the shadow period and must not be described as measured.

## Intentional differences requiring owner acceptance

1. At partial sun (300 W/m²), 25 °C indoors, 21 °C outdoors, and no wind, the
   joint model keeps `open/100%` instead of the static v4.17 `closed/50%`.
   Stack ventilation provides more modeled cooling than the admitted solar
   load; this is the intended replacement of the disconnected blind rule.
2. During the adverse Summer forecast, the stable state remains `tilt/0%`
   instead of v4.17 `closed/0%`. It is already the joint optimum after the
   preceding solar segment, so the avoided benefit of another movement is
   zero. No rain/wind safety restriction is active.
3. The new strategy produces 33 stable transitions/candidates versus 28 raw
   v4.17 action transitions over the nine synthetic days. There is no churn or
   duplicate candidate, but the five additional meaningful changes must be
   observed during shadow mode before any notification feature is considered.

Accepting these differences permits P01-T09 to connect the engine as
informational entities only. It does not approve a notification delivery path,
actuator control, or deployment. Rejecting them returns the relevant scenario
to its owning domain task; v4.17 remains unchanged and is still the rollback.

## Verification

Focused command:

```powershell
wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/replay -q'
```

Result: 5 passed. The canonical repository result is recorded in the active
phase plan after running the final evidence state.
