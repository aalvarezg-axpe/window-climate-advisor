# GOAL — Window Climate Advisor for Home Assistant

> Product source of truth and development roadmap.
>
> Document version: 0.27
> Initial date: 2026-08-24
> Last reviewed: 2026-08-31
> Current state: **active / Phase 02**
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
- keep a blind fully raised during Summer when geometry shows no direct sun
  reaches that opening; diffuse radiation may still affect the window thermal
  balance but does not by itself justify obstructing a manual blind;
- keep the stable physical target when no meaningful advantage exists, without
  exposing a separate public `hold` state;
- never pair a non-closed recommended window target with 0% blind opening;
- recommend a blind opening percentage without creating noisy intermediate
  notifications.

The integration will combine room temperature, outside temperature, radiation,
sun azimuth/elevation, façade and overhang geometry, wind speed/direction/gust,
rain, weather forecasts, comfort policy, schedules, hysteresis, and confidence.

The first release is an **advisor**, not an actuator. It publishes state,
reasoning, diagnostics, and stable recommendation changes. Home Assistant owns
any future action layer.

## 3. Migration baseline

The behavioural baseline was the deployed automation
`asesor_ventanas_automatizacion_v4_17_pre.yaml` and its existing regression,
thermal-balance, blind-percentage, wind-exposure, notification, and simulation
tests in the predecessor repository.

The executable v4.17 list contained five openings because the second bedroom
and bathroom temperature entities were still unavailable. This is a runtime
baseline boundary, not an inventory boundary: the versioned source and its
handoff preserve complete accepted geometry for both dormant openings. The two
bedrooms share the same north-east orientation and overhang geometry; the
bathroom has its own south-west overhang and rain protection. Migration work
must retain that provenance rather than infer that those rooms or openings
never existed merely because their blocks were commented pending real sensors.
The owner identifies historical Dormitorio 1 as Eli's room and Dormitorio 2 as
Anto's room; their remaining physical parameters are identical.

The predecessor remained immutable and operational during migration. Its
automation was the rollback until the new integration had:

1. characterized the baseline with versioned fixtures;
2. matched or intentionally superseded every accepted behaviour;
3. run in shadow mode without controlling notification or actuators;
4. passed an agreed comparison period;
5. been deployed and verified as a single available config entry without
   duplicate entities or configuration errors.

Those gates passed in Phase 01 and the owner accepted continuing exclusively
on the custom integration. A later notification-provenance audit found that
the old automation entity still remained enabled alongside the component and
had executed its notification action. The final cutover on 2026-08-30 left
that exact automation present but turned it off through Home Assistant's
supported service, so it cannot compete with component delivery and remains a
reversible emergency reference only. Its repository fixture and
characterization evidence remain immutable. The last live-verified integration
`v0.1.0b5` is the operational rollback for the Phase 02 notification beta.

The owner fixed the Phase 01 shadow period at four consecutive calendar days
on 2026-08-25 because the expected interval includes rain, heat, and sun. Its
UTC clock starts only after the deployed-entry verification gate passes.

The predecessor also contains a planned but unimplemented v4.18_pre backlog.
That backlog is a requirements source, not a second behavioural baseline and
not an instruction to create another YAML automation. Its accepted intent is
implemented in the custom integration and traced as follows:

| Predecessor task | Integration task | Disposition |
|---|---|---|
| F04-01 heuristic inventory | P01-T01 | Carried forward; weather safety is separated from replaceable thermal policy. |
| F04-02 coupled blind/window model | P01-T02 | Carried forward as pure, bounded, auditable domain logic. |
| F04-03 seasonal comfort profiles | P01-T03 | Carried forward through typed config-entry/options data; separate helpers are not the default. |
| F04-04 numerical optimization | P01-T04 | Carried forward; deterministic enumeration is the initial implementation unless evidence requires a solver. |
| F04-05 remove `terraza_caliente` | P01-T05 | Carried forward; real geometry may remain, the binary thermal heuristic may not. |
| F04-06 replace discrete thermal rules | P01-T06 | Carried forward as recommendation-only policy with absolute weather-safety priority. |
| F04-07 stability and notification control | P01-T07 | Carried forward; shadow mode does not own notifications. |
| F04-08 seasonal simulation | P01-T08 | Carried forward with versioned replay scenarios and comparison against v4.17_pre. |
| F04-09 version, regression, and deployment | P01-T09 and P01-T10 | Adapted to an integration build and reversible shadow deployment; no v4.18 YAML automation is created. |
| Imported HANDOFF solar-geometry scenarios 1–6 | P01-T11 | Close the recorded inventory gap by projecting global radiation onto each façade and overhang before deployment. |

## 4. Scope

### 4.1 Initial product scope

- UI setup through a config flow.
- One config entry per dwelling.
- Reconfigurable room subentries with temperature and optional humidity/CO2
  sources.
- Reconfigurable opening subentries linked to rooms, including orientation,
  dimensions, overhang geometry, rain protection, physical blind capability,
  optional contact sensor, and optional automated blind/cover entity.
- Global outdoor-temperature, weather/forecast, radiation, wind, and rain
  source selection through typed Home Assistant selectors; solar position comes
  from Home Assistant's built-in `sun` integration when the evaluator consumes
  it. Daily forecast maxima select the seasonal profile; in Summer, today's
  first maximum is also a bounded heat-risk switch for diffuse blind
  protection, not a predicted thermal state. The live optimizer has no thermal
  forecast horizon because the standard weather contract and configured
  sources do not provide future irradiance; the product states that absence
  explicitly and applies its missing-horizon penalty instead of inventing solar
  or indoor conditions.
- Pure Python domain models for geometry, solar exposure, ventilation, thermal
  balance, safety, strategy, hysteresis, and recommendation aggregation.
- Deterministic joint evaluation of window state and recommended blind opening,
  initially by exhaustive enumeration of the small auditable action space.
- Independent Summer, Shoulder-season, and Winter comfort profiles with lower
  and upper bounds, preconditioning target, hysteresis, automatic selection,
  and manual override.
- Native informational entities and diagnostics.
- Supported config-entry schema migrations and restart-safe state.
- Stable, consolidated, presence-aware recommendation notifications only after
  shadow parity, as the separately activated Phase 02 delivery.

### 4.2 Explicitly outside the initial release

- Direct physical control of windows, covers, awnings, HVAC, or irrigation.
- A bespoke JavaScript/TypeScript floor-plan or façade editor. Standard Home
  Assistant config-flow forms and subentries are sufficient initially.
- Cloud services, multi-user accounts, external databases, MQTT publication, or
  a standalone web service.
- Submission to Home Assistant Core, inclusion in HACS's default catalog, or a
  public license before shadow stability and ownership decisions. The owner
  approved a public GitHub custom repository on 2026-08-25 solely as the
  versioned installation channel for the local HACS shadow deployment.
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
  translations/en.json       # complete English custom-integration strings
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

Custom integrations ship complete language files under `translations/` and do
not use Core's build-time `strings.json` pipeline.

### 5.2 Configuration ownership

- Config entry: dwelling identity and global source assignments.
- Room subentry: room-level environmental sources and metadata.
- Opening subentry: geometry, façade, protection, contact, cover, and room link.
- Recipient subentry: one `person` entity. At delivery time the Home Assistant
  adapter follows that person's configured Mobile App `device_tracker`
  entities through the entity/device registries to their sibling native
  `notify` entities. Configuration stores neither a target nor a service/action
  name. Only explicitly selected occupants are recipients: a tracker shared by
  several Home Assistant persons does not implicitly authorize every one of
  those persons.
- Reconfigure flow: structural changes and entity replacements.
- Options flow: infrequent tuning of accepted user-visible settings.
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

Boundary tests must prove that every advertised decision input reaches the
typed domain request used in production. The four-day follow-up audit found
that the live coordinator could report forecast availability while the adapter
supplied `None` as every opening's thermal forecast horizon; domain-only replay
coverage did not detect that disconnect. Phase 01 cannot close until the
forecast contract is either implemented end to end or deliberately narrowed in
the public product contract. P01-T16 deliberately narrows it: the diagnostic
flag and production-boundary regression distinguish daily forecast availability
from a thermal forecast horizon. P02-T17 may pass today's first maximum only as
a heat-risk context value; it still does not enter `OptimizationRequest` as
invented thermal conditions. A later real horizon requires a demonstrated,
time-aligned future irradiance source and an explicit indoor reference
contract.

The owner froze one-sided seasonal intent on 2026-08-30 and corrected its
Summer stop boundary after a live false-tilt reproduction. Summer may actively
remove heat while the room is above the lower comfort boundary plus hysteresis;
at or below that boundary it must seek thermal neutrality rather than
deliberately admit hotter outdoor air or solar gain to heat a cool room. Winter
is the inverse in direction, not in target range: it may actively add heat, but
once heating is no longer required it must stop further gains and seek
neutrality rather than deliberately admit colder outdoor air to cool a warm
room. Weather safety remains absolute. Shoulder-season keeps the existing
symmetric comfort objective until separately reviewed; this decision does not
silently alter it. Phase 01 encodes the one-sided directions and P02-T12
corrects the Summer free-cooling cutoff from the preconditioning target to the
lower boundary plus hysteresis. P01-T19 retains the linear blind/free-area
multiplier as the owner's accepted best defensible unmeasured estimate for the
initial product: a first-order 0–100% uncovered-area geometry bound, not an
empirical airflow curve or a calibrated building simulation.

The owner selected a 21–24 °C live Summer comfort band on 2026-08-30 with a
22 °C in-band preconditioning target and 0.5 °C hysteresis. This is dwelling
configuration applied through the supported options flow, not a hidden product
default or migration. Under the accepted Summer policy, free cooling remains
active above 21.5 °C when the thermal and safety model favours it; at or below
that stop boundary the optimizer seeks neutrality.

Summer ventilation is also one-sided at the current indoor/outdoor boundary:
when the current outdoor temperature is equal to or above the room temperature,
the optimizer must resolve the window target to closed. Movement cost, missing-
forecast uncertainty and the optional minimum-benefit veto cannot retain `tilt`
or `open` against that boundary. The blind remains independently optimized and
confirmed. When outdoor air becomes cooler again, the existing benefit and
opening-improvement confirmation gates govern reopening; no separate temperature
threshold or option is introduced.

Published experiments require device/geometry/flow-specific correction, while
current Recorder history lacks actual manual blind/window positions, airflow
observations, and an identifiable room response. The owner ruled out a
dedicated physical calibration campaign as disproportionate on 2026-08-30.
The product therefore does not invent an exponent, discharge coefficient, or
new option and does not keep missing physical calibration as blocked work. The
relation may be revisited only if manufacturer data or passive operational
evidence later supplies a defensible correction.

Summer blind solar protection uses the same direct projection and overhang
geometry as the façade model. The fixed diffuse vertical component remains in
the joint window/blind thermal load. With no direct projection, a fully raised
blind remains the required default and cannot be discarded by the optional
minimum-benefit veto. P02-T17 unlocks the existing candidate space only when
current outdoor temperature or today's first daily maximum reaches the active
Summer upper bound. While the dwelling is occupied, the room must also have
reached that upper bound; when every selected occupant is known away, the lower
bound permits earlier protection. Below the lower bound diffuse radiation alone
never justifies shading. This reuses the configured comfort bounds and adds no
separate heat or radiation threshold. The normal 15-minute blind confirmation,
direct-sun behaviour and Winter night-insulation candidates remain unchanged.

Dwelling occupancy for thermal policy is an optional structural selection of
native `person` entities and is deliberately independent of notification
recipients. The dwelling is unoccupied only when every selected person has a
known non-`home` state; an empty selection, missing person or
`unknown`/`unavailable` state remains conservatively occupied. Relevant person
state changes trigger a fresh evaluation. This policy does not infer presence
from VPN, Wi-Fi, names or device connectivity and does not authorize an
actuator.

Missing or stale safety inputs do not become zero wind, no rain, or favourable
temperature. Degradation is explicit in recommendation, availability, reason
code, and diagnostics.

Room-temperature degradation identifies that source specifically: missing
means the configured room temperature is unavailable or malformed; stale means
its last report exceeded the independently configured room age. It never
silently borrows another room or treats an old value as current.

Rain restricts an opening only when it is wind-driven onto that façade. The
policy projects the configured gust through the existing conservative façade
exposure function; below 0.5 km/h of raw projected gust, including zero gust
or a leeward façade, rain does not override the optimizer target and the normal
wind policy still applies. On an exposed façade, the accepted rain intensity,
gust, protection and overhang geometry decide between tilt and close. A gust
at or above 45 km/h still closes every façade before rain handling. The
configured direction remains required even at zero gust so unavailable or
stale safety data cannot silently become favourable.

The live source inventory exposes no separate gust-direction entity or weather
attribute, so the existing typed wind-direction selector supplies the best
available bearing for both wind and gust exposure. Add a distinct selector only
when Home Assistant exposes a real source that can be selected and verified at
the production boundary.

Safety and environmental observations use an independent, strict maximum age.
Slow battery room-temperature observations may use one separately configured
maximum age; changing that room boundary must never relax wind, gust, rain,
outdoor-temperature, radiation, or solar-position freshness. Four-day shadow
evidence rejected the initial 60-minute room boundary for continuous
availability. The owner selected 125 minutes—two expected 60-minute report
cycles plus five minutes of margin—for later deployment through supported
options and live verification. It is not deployed by the read-only shadow; the
independent 15-minute safety/environmental boundary remains unchanged.

## 6. Entity contract

The exact entity inventory is frozen in a phase plan before implementation. The
initial design favours:

- one enum-like recommendation sensor per opening;
- one recommended blind-position sensor per opening when a blind exists;
- the existing recommendation sensor always exposes its resolved stable window
  target; `hold` is not a public state, and unchanged evaluations produce no
  notification candidate;
- the current reason is Recorder-visible through the smallest verified surface,
  preferably a bounded attribute on that same sensor rather than another
  entity;
- explicit safety/availability state;
- global strategy and last-evaluation sensors;
- redacted downloadable diagnostics for reason codes, source quality, and
  bounded engine results; no rapidly changing diagnostic sensors in Phase 01.

Avoid large or rapidly changing attributes that inflate Recorder. Configuration
belongs in config entries; detailed troubleshooting belongs in redacted
diagnostics.

### 6.1 Presence-aware notification contract

Notification delivery is owned by the active
[`Phase 02 plan`](phases/02-contextual-notifications/PLAN.md). Each recipient is
a native config subentry containing one configured `person` entity. At runtime,
the Home Assistant adapter reads that person's native `device_trackers`
relationship, joins each Mobile App tracker to sibling `notify` entities by
registry `device_id`, and delivers only to linked trackers whose own state is
`home`. The registry identifier is used only for this native join; delivery
still targets entity IDs through Home Assistant's fixed
`notify.send_message` action. Names and arbitrary action strings are never
stored or inferred.

Accepted ordinary stable window or blind target changes are retained only in
one non-persistent batch beginning with the first change and delivered at most
once after its fixed 10-minute window. The latest state and reason per opening
win while its changed window/blind components are combined. A recipient is
eligible only if a usable linked device is `home` when a retained change occurs
and remains `home` at delivery; a person with several home devices may receive
the same consolidated advice on each of them. Unload cancels and discards the
batch rather than persisting a notification queue.
If every linked device is away, the integration sends nothing and stores no
backlog. When a configured person later enters `home`, the integration performs
a fresh evaluation and sends only to that arriving person's linked devices that
are then home any recommendation that remains current and actionable. It does
not replay obsolete away-time transitions. Arrival delivery is deduplicated per
real away-to-home transition and remains restart-safe. An arriving person is
removed from any pending ordinary batch and receives only this immediate fresh
summary. Contact and cover feedback suppress targets already satisfied; when a
manual blind position cannot be observed, the arrival message states that
explicitly.

Thermal occupants and notification recipients are separate configured sets.
Away-time blind recommendations may change under the more protective empty-home
policy, but the existing event-time and delivery-time recipient gates still
create neither a pending batch nor a message while no recipient device is home.
An arrival triggers a fresh occupied evaluation before actionable advice is
formatted, so an empty-home target is not replayed as stale work.

Notification bodies separate `Windows` and `Blinds` into multiline bullet
sections and include only the component that changed or remains actionable. A
room with one opening is identified only by its room title; a room with several
openings appends the shortest configured opening suffix needed to distinguish
them without repeating the room title or retaining later physical qualifiers
once an orientation token is already unique. Weather-forced rows include a concise
reason propagated from the evaluated policy result rather than inferred during
delivery. In Summer, every resolved target below full opening likewise states
one bounded cause: the lower comfort limit, outdoor air that is not cooler,
estimated façade radiation exceeding ventilation cooling, benefit below the
stability margin, or an opening still inside its confirmation period. A
coupled optimizer window/blind change is published as one stable
recommendation; the blind deadband suppresses a small target change instead of
changing the published percentage silently. Ordering is deterministic and
degraded rows remain non-actionable.

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
- production-boundary tests that distinguish an input-availability indicator
  from actual delivery of that input to the optimizer;
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
- HACS shadow candidates use numbered beta GitHub prereleases from the matching
  `release/<version>` branch. They do not make `main` releasable or replace the
  final annotated stable tag.
- During the initial beta-only bootstrap, the public repository may temporarily
  use that matching `release/<version>` branch as its GitHub default because
  HACS validates custom-repository structure from the default branch before it
  can expose a prerelease. `main` still contains accepted releases only; restore
  it as the GitHub default when the first accepted release is merged there.

No phase is complete until its plan records tests, review, artifact inventory,
and relevant external verification. Deployment and Home Assistant mutation are
root-owned and require exact target verification.

The authorized public remote is
`https://github.com/aalvarezg-axpe/window-climate-advisor`. It is a custom HACS
repository, not a request for inclusion in HACS's default catalog. Public
visibility does not grant a public license; that remains a separate owner
decision.

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
9. the immutable old-automation fixture remains characterized, while the last
   live-verified integration remains the operational rollback after cutover;
10. no physical action path exists.
