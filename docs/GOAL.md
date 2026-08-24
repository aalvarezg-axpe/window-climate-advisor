# GOAL — Window Climate Advisor for Home Assistant

> Product source of truth and development roadmap.
>
> Document version: 0.2
> Initial date: 2026-08-24
> Last reviewed: 2026-08-24
> Initial state: **planned / bootstrap**
> Home Assistant display timezone: `Europe/Madrid`
> Internal operational timezone: UTC

## 1. Purpose of this document

This document defines the product, non-negotiable architecture, safety gates,
delivery model, and completion criteria for migrating the existing window and
blind advisor from a large Home Assistant automation into a maintainable custom
integration.

The root manager reads this document and the active phase plan before planning
or editing. Executors read them at the start of a persistent work wave. Code
existence alone never completes a phase: its declared tests, integration gates,
shadow comparison, deployment, and Home Assistant verification must pass.

This document, `AGENTS.md`, and every phase `PLAN.md` are living references.
When implementation or review exposes an inefficiency, contradiction, stale
assumption, or omitted accepted requirement, the root manager corrects the
affected documents as part of the same traceable task. A documentation update
may clarify or reorganize accepted scope, but cannot silently authorize a new
product capability or weaken a safety, privacy, rollback, or verification gate.

The owner may update task state, evidence, dates, links, and ADRs without
changing product scope. Changes to physical-action safety, behavioural parity,
rollback, privacy, GitFlow, or completion gates require an explicit owner
decision.

## 2. Product vision

Build a Home Assistant custom integration that models a dwelling, its rooms,
openings, orientations, solar protections, and environmental sources, then
recommends per opening whether to:

- open fully;
- use the tilt/oscillating position;
- close for rain or wind safety;
- close to preserve coolness or warmth;
- raise a blind to capture useful solar gain;
- lower a blind to reduce solar load or night heat loss;
- keep the current action when no meaningful advantage exists;
- recommend a blind opening percentage without creating noisy intermediate
  notifications.

The integration will combine room temperature, outside temperature, radiation,
sun azimuth/elevation, façade and overhang geometry, wind speed/direction/gust,
rain, weather forecasts, comfort policy, schedules, hysteresis, and confidence.

The first release is an **advisor**, not an actuator. It publishes state,
reasoning, diagnostics, and stable recommendation changes. Home Assistant owns
any future action layer.

## 3. Migration baseline

The behavioural baseline is the deployed automation
`asesor_ventanas_automatizacion_v4_17_pre.yaml` and its existing regression,
thermal-balance, blind-percentage, wind-exposure, notification, and simulation
tests in the predecessor repository.

The predecessor remains immutable and operational during migration. Its
automation is the rollback until the new integration has:

1. characterized the baseline with versioned fixtures;
2. matched or intentionally superseded every accepted behaviour;
3. run in shadow mode without controlling notification or actuators;
4. passed an agreed comparison period;
5. been deployed and verified as a single available config entry without
   duplicate entities or configuration errors.

The predecessor also contains a planned but unimplemented v4.18_pre backlog.
That backlog is a requirements source, not a second behavioural baseline and
not an instruction to create another YAML automation. Its accepted intent is
implemented in the custom integration and traced as follows:

| Predecessor task | Integration task | Disposition |
|---|---|---|
| F04-01 heuristic inventory | P01-T01 | Carried forward; weather safety is separated from replaceable thermal policy. |
| F04-02 coupled blind/window model | P01-T02 | Carried forward as pure, calibrated domain logic. |
| F04-03 seasonal comfort profiles | P01-T03 | Carried forward through typed config-entry/options data; separate helpers are not the default. |
| F04-04 numerical optimization | P01-T04 | Carried forward; deterministic enumeration is the initial implementation unless evidence requires a solver. |
| F04-05 remove `terraza_caliente` | P01-T05 | Carried forward; real geometry may remain, the binary thermal heuristic may not. |
| F04-06 replace discrete thermal rules | P01-T06 | Carried forward as recommendation-only policy with absolute weather-safety priority. |
| F04-07 stability and notification control | P01-T07 | Carried forward; shadow mode does not own notifications. |
| F04-08 seasonal simulation | P01-T08 | Carried forward with versioned replay scenarios and comparison against v4.17_pre. |
| F04-09 version, regression, and deployment | P01-T09 and P01-T10 | Adapted to an integration build and reversible shadow deployment; no v4.18 YAML automation is created. |

## 4. Scope

### 4.1 Initial product scope

- UI setup through a config flow.
- One config entry per dwelling.
- Reconfigurable room subentries with temperature and optional humidity/CO2
  sources.
- Reconfigurable opening subentries linked to rooms, including orientation,
  dimensions, overhang geometry, rain protection, optional contact sensor, and
  optional blind/cover entity.
- Global weather, radiation, wind, rain, sun, and forecast source selection
  through typed Home Assistant selectors.
- Pure Python domain models for geometry, solar exposure, ventilation, thermal
  balance, safety, strategy, hysteresis, and recommendation aggregation.
- Deterministic joint evaluation of window state and recommended blind opening,
  initially by exhaustive enumeration of the small auditable action space.
- Independent Summer, Shoulder-season, and Winter comfort profiles with lower
  and upper bounds, preconditioning target, hysteresis, automatic selection,
  and manual override.
- Native informational entities and diagnostics.
- Supported config-entry schema migrations and restart-safe state.
- Stable, consolidated recommendation notifications only after shadow parity.

### 4.2 Explicitly outside the initial release

- Direct physical control of windows, covers, awnings, HVAC, or irrigation.
- A bespoke JavaScript/TypeScript floor-plan or façade editor. Standard Home
  Assistant config-flow forms and subentries are sufficient initially.
- Cloud services, multi-user accounts, external databases, MQTT publication, or
  a standalone web service.
- Submission to Home Assistant Core, public HACS distribution, or a public
  license before local stability and ownership decisions.
- Inventing missing room sensors, cover entities, positions, or geometry.

## 5. Architecture

### 5.1 Modular custom integration

The project is one repository and one distributable custom integration:

```text
custom_components/window_climate_advisor/
  __init__.py                 # setup/unload and platform forwarding
  manifest.json               # integration metadata
  config_flow.py              # setup, reconfigure, options, subentries
  const.py                    # stable integration constants only
  sensor.py                   # thin Home Assistant sensor platform
  binary_sensor.py            # thin availability/safety platform
  number.py                   # operational numeric controls, if justified
  select.py                   # operational strategy control, if justified
  switch.py                   # operational feature toggles, if justified
  diagnostics.py              # redacted diagnostics
  strings.json                # canonical translations
  translations/es.json
  domain/
    models.py                 # typed input/output values
    geometry.py               # façade, sun, overhang calculations
    ventilation.py            # airflow model
    thermal.py                # thermal/solar balance
    policy.py                 # recommendation priority and safety
    state_machine.py          # hysteresis and stable transitions
  application/
    evaluator.py              # orchestration over a complete snapshot
    state.py                  # restart-safe application state contract
  adapters/
    home_assistant.py         # entity-state translation and subscriptions
    forecast.py               # Home Assistant weather translation
tests/
  unit/domain/
  unit/application/
  integration/
  fixtures/
docs/
  adr/
  operations/
  phases/
  status/
```

Home Assistant-required platform files stay at the integration root, but all
non-trivial decisions live behind typed boundaries. Domain modules have no Home
Assistant imports and no I/O, which allows fast deterministic tests and replay
of the v4.17 baseline.

### 5.2 Configuration ownership

- Config entry: dwelling identity and global source assignments.
- Room subentry: room-level environmental sources and metadata.
- Opening subentry: geometry, façade, protection, contact, cover, and room link.
- Reconfigure flow: structural changes and entity replacements.
- Options flow: infrequent tuning and calibration.
- Native `select`, `number`, or `switch` entities: only controls that users
  reasonably change from dashboards or automations.
- Supported Home Assistant storage API: compact runtime state and hysteresis;
  never direct `.storage` edits or `input_text` serialization.

Every stored schema has an explicit version and tested migration. Entity unique
IDs derive from stable config-entry/subentry identifiers, never display names or
mutable entity IDs.

### 5.3 Evaluation lifecycle

The application assembles one immutable snapshot from referenced Home Assistant
entities and forecast data, evaluates all openings coherently, and publishes one
result set. Relevant entity changes trigger a debounced evaluation; a bounded
periodic evaluation provides recovery. One coordinator owns scheduling,
availability, and entity updates.

Missing or stale safety inputs do not become zero wind, no rain, or favourable
temperature. Degradation is explicit in recommendation, availability, reason
code, and diagnostics.

## 6. Entity contract

The exact entity inventory is frozen in a phase plan before implementation. The
initial design favours:

- one enum-like recommendation sensor per opening;
- one recommended blind-position sensor per opening when a blind exists;
- explicit safety/availability state;
- global strategy and last-evaluation sensors;
- disabled-by-default diagnostics for thermal watts, airflow, effective solar
  load, source age, confidence, and reason codes.

Avoid large or rapidly changing attributes that inflate Recorder. Configuration
belongs in config entries; detailed troubleshooting belongs in redacted
diagnostics.

## 7. Safety and privacy gates

### 7.1 Physical actions

Physical actions are prohibited. A future actuator phase requires all of:

- explicit owner approval recorded in this document;
- confirmed `cover.*` or actuator identities and position semantics;
- actual-position/contact feedback where needed;
- obstruction, rain, wind, occupancy, manual override, and stale-data policy;
- fail-safe behaviour on restart and communication loss;
- rate limits, hysteresis, emergency stop, rollback, and audit trail;
- local tests, shadow validation, and deployed verification.

Until then, 0–100% blind values are recommendations only.

### 7.2 Secrets and private data

Secrets live only in the ignored `.env` or the deployment system. Never commit
tokens, credentials, exact private coordinates, Home Assistant backups, entity
dumps, or traces containing household state. Diagnostics redact entity state
values when they reveal private behaviour and never expose access tokens.

## 8. Quality target

The integration aims beyond the minimum custom-integration skeleton:

- UI-only configuration and reconfiguration;
- strict typing for owned code;
- deterministic domain tests independent of Home Assistant;
- full config-flow and migration coverage;
- setup, unload, reload, restart, entity identity, and availability tests;
- at least 90% branch coverage overall and near-complete useful coverage for
  safety/state transitions;
- Ruff formatting/lint, mypy strict, pytest, coverage, manifest/translation
  checks, secret/artifact checks, and one canonical verification command;
- redacted diagnostics and a repeatable deployment/rollback runbook;
- ADRs for durable architecture or contract decisions.

Home Assistant's official integration quality rules are a floor and checklist,
not the repository architecture. The project additionally enforces domain
isolation, phase plans, immutable baselines, manager-executor waves, artifact
ownership, shadow comparison, and deployment evidence.

Repository work uses a Sol/xhigh root manager and one persistent Luna/max
executor by default. The root applies Ponytail `full` while freezing a wave,
`ponytail-review` during consolidated review, and `ponytail-audit` before phase
closure. These complexity gates never override safety, validation, tests,
migrations, deployment verification, or rollback.

## 9. GitFlow and delivery

- `main`: accepted releases only.
- `develop`: integrated, verified development.
- `feature/<NN>-<slug>`: one phase or coherent delivery.
- `release/<version>`: release candidate stabilization.
- Conventional Commits with a `Task: PNN-TXX` trailer.
- Completed phases merge `--no-ff` to `develop`.
- Releases merge to `main`, receive an annotated tag, and merge back to
  `develop`.

No phase is complete until its plan records tests, review, artifact inventory,
and relevant external verification. Deployment and Home Assistant mutation are
root-owned and require exact target verification.

## 10. Initial milestone criteria

The first useful milestone is complete only when:

1. the config flow creates one dwelling, rooms, and openings entirely via UI;
2. invalid entity domains, duplicate links, impossible geometry, and missing
   required safety sources are rejected before setup;
3. the Python engine reproduces the accepted v4.17 scenarios and simulations;
4. restart-safe hysteresis does not use `input_text` helpers;
5. informational entities load, unload, reload, migrate, and remain uniquely
   identified;
6. missing/stale data produces explicit degradation, never a safe default;
7. the integration runs in shadow mode for the agreed comparison period;
8. Home Assistant shows the expected integration, devices/entities, aliasing,
   availability, diagnostics, and no duplicates or config errors;
9. the old automation remains a verified rollback until cutover is approved;
10. no physical action path exists.
