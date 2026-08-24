# ADR 0008 — Home Assistant shadow runtime

- Status: accepted for P01-T09
- Date: 2026-08-25
- Sources: ADR 0003, P01-T01–P01-T08, and predecessor F04-09

## Decision

Connect the accepted pure engine through one config-entry coordinator. It
evaluates every configured opening from one coherent Home Assistant snapshot,
refreshes every five minutes, and requests a debounced refresh when a referenced
entity changes. It stores only `AdvisorState` through Home Assistant's supported
`Store` API under a key scoped by config-entry ID. The v4.17 automation remains
operational; this integration registers no service, action, notification, or
physical-control platform.

The coordinator owns translation and scheduling. Home Assistant state objects,
service responses, units, and entity IDs do not cross the adapter boundary.
The application evaluator receives typed conditions, safety snapshots, opening
capabilities, selected profiles, and prior state. Missing, unavailable,
malformed, wrong-unit, or stale required observations produce a `degraded`
recommendation and unsafe-to-open result; they never become zero or favourable.
An `on` binary rain source is conservatively treated as more than light rain.
A numeric rain source is accepted only in mm/h.

Daily weather forecast temperatures are used for automatic profile selection.
The optimizer receives a forecast horizon only when every required thermal
value is available; otherwise its already accepted missing-forecast penalty
applies and diagnostics record that forecast as unavailable. No future indoor
temperature, façade irradiance, wind, or gust is invented.

Profiles plus these runtime parameters are required in the options flow and
have no hidden operational defaults:

- blind step percentage;
- window movement penalty in watt-equivalent units;
- blind full-travel penalty in watt-equivalent units;
- missing-forecast change penalty in watt-equivalent units;
- minimum accepted benefit in watts;
- blind deadband percentage;
- maximum source age in minutes.

The options validator constructs the existing typed optimizer and stability
settings. Until a complete valid option set exists, the entry remains loaded
and publishes explicit degraded recommendations so the user can configure it
through the UI.

Config-entry version 2 renames stored geometry keys to include units
(`*_deg`, `*_m`). Migration changes keys only and preserves values, config-entry
ID, subentry IDs, and entity identity. Runtime state remains the independently
versioned application schema and fails explicitly when structurally invalid.

## Entity and diagnostics surface

The only enabled platforms are `sensor` and `binary_sensor`:

- per opening: recommendation enum and safe-to-open binary sensor;
- per opening with a configured cover: recommended blind position sensor;
- per dwelling: active profile enum and last-evaluation timestamp sensor.

Unique IDs follow ADR 0003 exactly. Opening entities share a device identified
by config-entry/subentry ID and dwelling entities share a config-entry device.
Recommendation is relative to the observed contact when configured; without a
contact, the persisted stable recommendation is the conservative reference and
a new opening starts closed. A configured but unreadable cover position
degrades that opening. An opening without a cover is evaluated with the blind
fixed at 100% and does not create a blind-position entity.

Home Assistant diagnostics return configuration shape, source quality,
reason codes, timestamps, and accepted engine results. Entity IDs and config
names are redacted; tokens, raw entity states, household history, contacts, and
coordinates are absent. No rapidly changing diagnostic attributes or enabled
diagnostic sensors are added in this phase. Subentry IDs are replaced with
stable report-local aliases such as `room_1` and `opening_1`.

All configured `*_entity_id` values are one-to-one across a dwelling. The UI
flows reject duplicates and setup repeats the check defensively for migrated or
corrupted stored data. This prevents one physical observation from silently
standing in for two inputs with different units or meanings.

## Consequences

- Setup, unload, reload, migration, persistence, and entity identity can be
  tested locally without Home Assistant deployment credentials.
- A missing optional forecast reduces confidence conservatively but does not
  disguise missing safety or current thermal data.
- P01-T10 remains a separate reversible deployment and shadow-observation task.
- Additional entities, tuning defaults, notification delivery, and actuator
  paths require a later traced decision rather than extension points here.
