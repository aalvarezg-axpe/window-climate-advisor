# ADR 0009 — Solar façade boundary

- Status: accepted for P01-T11
- Date: 2026-08-25
- Sources: imported HANDOFF scenarios 1–6, predecessor v4.17 thermal geometry,
  inventory gap at `docs/migration/v4_17_inventory.md`, and ADR 0004

## Context

The thermal engine correctly requires irradiance on each opening's vertical
plane, but the initial Home Assistant adapter passed the selected global
horizontal radiation directly. That made the configured façade azimuth and
overhang irrelevant to solar load. The migration inventory had already marked
front/side and overhang scenarios 1–6 as an unresolved P01 gap.

## Decision

Use Home Assistant's built-in `sun.sun` azimuth/elevation and the configured
global horizontal irradiance to calculate current façade irradiance before
constructing `ThermalConditions`. `sun` is an explicit manifest dependency and
state-change subscription, not another user-selected entity.

The dependency-free projection retains the bounded v4.17 geometry:

```text
incidence = shortest angular distance(sun azimuth, façade azimuth)
sun in front = elevation > 3°, incidence <= 80°, global radiation >= 20 W/m²
vertical shadow = overhang depth × tan(elevation) / cos(incidence)
unshaded fraction = clamp((gap + opening height - shadow) / height, 0, 1)
vertical projection = clamp(cos(elevation) × cos(incidence)
                            / max(sin(elevation), 0.25), 0, 2)
façade factor = clamp(0.15 + 0.85 × projection × unshaded fraction,
                      0, 1.8)
façade irradiance = global horizontal irradiance × façade factor
```

The 0.15 diffuse vertical fraction, 3°/80° front gates, and 1.8 cap remain
historical/provisional assumptions, not measured calibration. Property tests
cover frontal, lateral, rear, north-wrap, low-sun, zero-radiation, bounds, and
monotonic shade from deeper overhangs.

P02-T16 also evaluates the same projection with the diffuse fraction set to
zero at the adapter boundary. A positive result means direct sun reaches the
opening after façade incidence and overhang shade; only then may the optimizer
enumerate lowered-blind candidates during Summer. The original combined
projection remains the thermal-condition irradiance, so diffuse load still
influences window opening without independently lowering a Summer blind.
Winter night-insulation candidates remain outside this solar gate.

Missing, unavailable, malformed, future-dated, or stale `sun.sun` data degrades
the opening exactly like another required thermal input. The adapter records
only source quality. It does not expose raw position through entities or
diagnostics.

## Exclusions

- No future sun position, radiation, indoor temperature, wind, or gust is
  invented. The optimizer's accepted missing-forecast change penalty remains
  active until a complete forecast horizon exists.
- No `terraza_caliente`, empirical terrace bubble, cloud service, external
  solar library, new option, helper, diagnostic sensor, or actuator is added.
- Overhang depth zero naturally means no direct overhang shade; no additional
  shade-type schema is required for the accepted initial contract.
