# ADR 0005 — Seasonal comfort profiles

- Status: accepted for P01-T03
- Date: 2026-08-24
- Sources: catalog C020/C021 and predecessor A06

## Decision

Store three complete user-supplied profiles in `ConfigEntry.options`: Summer,
Shoulder season, and Winter. Each has lower and upper comfort bounds, a
preconditioning target inside those bounds, and a positive hysteresis no wider
than the profile band. Store selection as `auto`, `summer`, `shoulder`, or
`winter`. Reusing the existing config-entry update listener reloads the entry
after an options change.

The integration supplies typed number/select forms but no claimed comfort
defaults: the predecessor's shared 18/24 °C helpers are not evidence for three
calibrated profiles. The first options flow therefore requires the owner to
enter all values. Reopening it suggests the stored values.

Manual selection returns the chosen profile. Automatic selection preserves the
characterized order while replacing shared comfort helpers with the selected
profile boundaries:

1. indoor maximum at/above Summer upper bound minus Summer hysteresis;
2. June–September;
3. indoor minimum at/below Winter lower bound plus Winter hysteresis;
4. November–March;
5. a complete forecast with every daily maximum below 25 °C selects Winter;
6. a complete forecast with every maximum above 25 °C selects Summer;
7. otherwise history maximum above 25 °C selects Summer, below 21 °C selects
   Winter, and all other/missing cases select Shoulder season.

The strict 25/21 °C forecast/history thresholds and month sets are historical
selection calibration, not comfort bounds. They stay typed and independently
testable so later replay evidence can change them deliberately. Missing or
non-finite sequences never satisfy a warm/cold test.

## Exclusions

- No `input_number`, `input_select`, or other Home Assistant helper is created.
- No occupancy, schedule, notification, HVAC, or actuator behaviour is added.
- No optimizer objective is defined here; P01-T04 consumes the selected typed
  profile.
