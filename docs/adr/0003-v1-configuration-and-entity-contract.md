# ADR 0003 — Configuration and entity contract

- Status: accepted for P00-T03
- Date: 2026-08-24
- Target: Home Assistant 2026.8.2

## Context

The scaffold needs a real configuration consumer without introducing thermal
logic or placeholder platforms. Home Assistant 2026.8 supports config
subentries and custom-integration translations under `translations/`. The
project models one dwelling per config entry, with rooms and openings as typed
subentries.

## Decision

### Config entry

The user flow creates one dwelling entry. Multiple dwellings are allowed, so
the manifest does not use `single_config_entry`. The entry title is mutable and
is not used for identity. `ConfigEntry.entry_id` is the stable dwelling key.

Version 4 entry data contains only structural inputs needed to assemble an
evaluation snapshot. Version 1 used unit-implicit opening geometry keys; the
P01-T09 migration renames those keys without changing values or identity.
P01-T13 separates physical blind capability from optional Home Assistant
automation: v1/v2 entries infer `has_blind=true` only when an existing
`cover_entity_id` proves the capability, preserving identity and requiring UI
reconfiguration for previously inexpressible manual blinds. P01-T14 separates
room-temperature age from safety/environmental-source age. The v3→v4 migration
copies the prior shared age to both keys, preserving behaviour until the owner
confirms a distinct room value.

| Key | Required | Selector / value |
|---|---|---|
| `name` | yes | non-empty text |
| `outdoor_temperature_entity_id` | yes | `sensor` entity |
| `weather_entity_id` | yes | `weather` entity |
| `solar_radiation_entity_id` | yes | `sensor` entity |
| `wind_speed_entity_id` | yes | `sensor` entity |
| `wind_direction_entity_id` | yes | `sensor` entity |
| `wind_gust_entity_id` | no | `sensor` entity |
| `rain_entity_id` | yes | `binary_sensor` wet/dry or `sensor` mm/h entity |

The built-in `sun` integration will supply solar position once the evaluator
consumes it; users do not select `sun.sun`. It is not a Phase 00 manifest
dependency because the behaviour-free scaffold does not use it yet. Structural
source replacements use the reconfigure flow and reload the existing entry.
`ConfigEntry.options` remains empty until P01-T03 freezes measured
comfort/calibration settings; no speculative options flow or helper entities
are created in Phase 00.

### Room subentry

Subentry type `room` stores:

| Key | Required | Selector / value |
|---|---|---|
| `name` | yes | non-empty text |
| `temperature_entity_id` | yes | `sensor` entity |
| `humidity_entity_id` | no | `sensor` entity |
| `co2_entity_id` | no | `sensor` entity |

### Opening subentry

Subentry type `opening` stores:

| Key | Required | Selector / value |
|---|---|---|
| `name` | yes | non-empty text |
| `room_subentry_id` | yes | existing `room` subentry ID |
| `facade_azimuth_deg` | yes | degrees, 0–359 |
| `width_m` | yes | metres, greater than zero |
| `height_m` | yes | metres, greater than zero |
| `overhang_depth_m` | yes | metres, zero or greater |
| `overhang_gap_m` | yes | vertical metres from overhang to opening top, zero or greater |
| `supports_tilt` | yes | boolean |
| `rain_protected` | yes | boolean calibration flag |
| `has_blind` | yes | physical blind/shutter capability, including manual |
| `contact_entity_id` | no | `binary_sensor` entity |
| `cover_entity_id` | no | automated `cover` observation; requires `has_blind` |

Room links store the immutable subentry ID, never the room title. Subentry IDs,
not names or selected entity IDs, are the stable opening/room identities.
Creation and reconfigure flows validate selector domains, numeric bounds, and
that an opening references a room belonging to the same config entry. One Home
Assistant entity may fill only one semantic input across the dwelling; create,
reconfigure, and runtime setup reject duplicate entity links. Reconfiguring a
subentry excludes its prior data from that comparison, so keeping an unchanged
valid assignment is allowed.

### Frozen entity surface

Phase 00 does not create platform files because no evaluator consumes them yet.
P01-T09 implements this frozen informational surface:

- per opening: enum recommendation sensor with `open`, `tilt`, `close`, `hold`,
  and `degraded` states;
- per opening with a physical blind: recommended blind-position sensor in the
  0–100% Home Assistant convention, whether or not a `cover` is configured;
- per opening: safety-to-open binary sensor;
- per dwelling: active comfort-profile sensor and last-evaluation timestamp
  sensor;
- no diagnostic sensor in Phase 01; detailed values use redacted downloadable
  Home Assistant diagnostics instead.

Entity unique IDs use `<entry_id>:<subentry_id>:<kind>` for opening entities and
`<entry_id>:<kind>` for dwelling entities. Display names and entity IDs never
participate in identity. No service or physical-action entity is permitted.

### Minimal scaffold artifacts

P00-T03 creates only:

- `__init__.py`, `manifest.json`, `const.py`, and `config_flow.py`;
- complete `translations/en.json` and `translations/es.json` files;
- integration tests for manifest/config-flow loading, entry and subentry
  create/reconfigure validation, and setup/unload/reload.

It does not create `sensor.py`, `binary_sensor.py`, `number.py`, `select.py`,
`switch.py`, `diagnostics.py`, domain/application packages, services, or
placeholder entities.

## Consequences

- The UI captures the dwelling geometry and source relationships without YAML.
- Phase 00 remains behaviour-free while testing the complete configuration
  boundary used by later phases.
- Comfort defaults, calibration values, stale-data thresholds, and optimizer
  parameters wait for measured requirements in P01; they are not hidden in
  `.env` or premature helpers.
- English and Spanish translation files are maintained directly because custom
  integrations do not use Core's `strings.json` build pipeline.

P01-T09 activates the frozen entity surface under ADR 0008 and extends the
options flow with required optimizer, stability, safety/environmental-age, and
room-temperature-age settings. It
does not infer values while migrating a v1 entry; incomplete options remain an
explicit degraded configuration until completed in the UI.

References:

- <https://developers.home-assistant.io/docs/core/integration/config_flow/>
- <https://developers.home-assistant.io/docs/internationalization/custom_integration/>
