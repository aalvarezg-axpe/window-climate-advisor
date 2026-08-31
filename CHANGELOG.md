# Changelog

All notable changes will be documented here. The project intends to follow
Semantic Versioning after the first distributable integration release.

## Unreleased

## 0.2.0b8 - 2026-08-31

### Changed

- Summer `Oscilobatiente` and `Cerrar` recommendations now carry one concrete
  evaluated cause: lower comfort limit, outdoor air that is not cooler,
  estimated façade radiation that outweighs ventilation cooling, insufficient
  benefit to clear the stability margin, or a still-active confirmation period.
- Optimizer-driven window and blind changes are published as one coherent
  recommendation. A same-direction blind target change is no longer silent,
  while changes inside the configured blind deadband remain suppressed.
- A degraded room now distinguishes missing room temperature from a room
  temperature older than its configured maximum age.

### Safety and privacy

- Weather reasons and immediate safety overrides retain priority. The change
  adds no entity, option, helper, queue, dependency, schema, service or
  actuator action, and records no raw household state.

## 0.2.0b7 - 2026-08-30

### Changed

- Ordinary stable changes received during one fixed 10-minute window are now
  combined into at most one deterministic notification instead of being sent
  room by room. Arrival advice remains fresh and immediate.
- Removed the generic `Better thermal balance` / `Mejor equilibrio térmico`
  parenthetical; concrete rain, wind and manual-blind reasons remain.
- The deployed Summer comfort profile is adjusted separately through supported
  options to 21–24 °C, target 22 °C and 0.5 °C hysteresis.

### Safety and privacy

- A recipient must have a usable home Mobile App route both when a retained
  change occurs and at delivery. The in-memory batch is discarded on unload,
  never becomes an away-time queue, and adds no option, entity, dependency,
  schema, service or physical action.

## 0.2.0b6 - 2026-08-30

### Changed

- Summer free cooling now remains active until the room reaches its lower
  comfort boundary plus hysteresis. This uses materially cooler outdoor air
  before returning to thermal neutrality instead of stopping at the higher
  preconditioning target.
- The live `Pruebas` comparison card is aligned separately through Home
  Assistant's supported Lovelace API with all six configured room sources and
  seven current openings.

### Safety and privacy

- Winter still never actively cools, Shoulder-season remains symmetric, and
  all weather-safety, stability, notification-routing, privacy and
  zero-actuator gates are unchanged. The dashboard correction renames no
  entity and stores no household state in the repository.

## 0.2.0b5 - 2026-08-30

### Changed

- Optimizer-selected `Oscilobatiente` and `Cerrada` window rows now explain
  that they provide the better thermal balance. The note appears in ordinary
  and arrival notifications, while full-open and blind-only rows stay compact.

### Safety and privacy

- Existing wind/rain explanations retain priority. No optimizer, safety,
  source, recipient, entity, queue, dependency, notification action, or
  physical-action behaviour changed.

## 0.2.0b4 - 2026-08-30

### Changed

- Rain now restricts only façades reached by a meaningful projected gust.
  Zero/near-zero gust and leeward façades retain the optimizer target through
  the normal wind policy instead of closing for vertical rain alone.
- The existing typed wind-direction source is reused for gust exposure because
  the deployed Home Assistant inventory has no distinct gust-direction source.

### Safety and privacy

- The 45 km/h all-façade close, missing/stale fail-closed handling, protected
  tilt geometry, positive-blind invariant, notification routing, privacy and
  zero-actuator boundary remain unchanged.
- The legacy advisor automation was turned off through Home Assistant's
  supported service after proving it had no executable consumers. Its
  configuration remains intact for reversible rollback while notifications
  come only from the custom component.

## 0.2.0b3 - 2026-08-30

### Changed

- Notifications now separate window and blind changes into multiline bullet
  sections and omit components that did not change.
- Single-opening rooms use only the room title; multi-opening rooms retain a
  non-duplicated configured suffix for disambiguation.
- Weather-forced rows show the concise reason already produced by the safety
  policy. Arrival advice uses the same structure and retains the manual-blind
  observation note.

### Safety and privacy

- Rain, gust, direction, façade exposure, overhang, recipient, presence,
  no-queue, and zero-actuator policies are unchanged. Degraded rows remain
  non-actionable and message content is not persisted by the integration.

## 0.2.0b2 - 2026-08-30

### Changed

- Recipient configuration now stores only a native `person` entity. Associated
  Home Assistant Mobile App trackers and sibling `notify` entities are resolved
  through the entity/device registries without comparing names.
- Delivery targets every associated mobile device whose own tracker is
  currently `home`; multiple home devices for one person are supported and a
  malformed shared target is called at most once.
- Schema-v4 revision 2 removes the redundant beta `notify_entity_id` while
  retaining recipient subentry identity and the major-version downgrade path.

### Safety and privacy

- Missing, disabled, away, or unavailable tracker/notification paths send
  nothing. Configuration, diagnostics, and logs retain no device names,
  notification target IDs, presence details, coordinates, or message backlog.

## 0.2.0b1 - 2026-08-30

### Added

- Explicit repeatable recipient configuration mapping one native `person`
  entity to one selected native `notify` entity without inferred action names.
- One translated, deterministic notification per accepted grouped
  recommendation change, delivered only to configured occupants currently at
  home.
- Fresh arrival advice on real non-home-to-home transitions, omitting targets
  already confirmed by contact/cover feedback and identifying unobservable
  manual blind positions.

### Safety and privacy

- Away-time changes are discarded instead of queued, startup/restoration does
  not count as an arrival, notification failure is isolated, and diagnostics
  expose only a recipient count.
- Notification delivery uses only fixed `notify.send_message`; no actuator,
  helper, entity, dependency, service-name parser, or presence ledger was
  added.

## 0.1.0b5 - 2026-08-30

### Added

- Initial repository governance, product goal, bootstrap phase, architecture
  decisions, local-development runbook, and secret-variable contract.
- Local Sol/xhigh manager, Luna/max executor, and Ponytail workflow restored.
- Reproducible Python 3.14.2/Home Assistant 2026.8.2 development environment
  with a locked `uv` dependency graph and one cross-platform verification gate.
- Immutable v4.17_pre migration inventory, scenario provenance, verified
  hashes, and the minimal fixture-import manifest.
- Minimal installable custom-integration scaffold with typed dwelling, room,
  and opening configuration flows, lifecycle reload handling, and complete
  English/Spanish translations.
- Exact v4.17_pre and v4.16_pre migration fixtures with executable integrity,
  YAML/Jinja, version-independence, and recommendation-only characterization.
- Frozen Phase 1 optimizer/shadow plan with all v4.18_pre requirements mapped,
  exact local gates, bounded write sets, and deployment stop conditions.
- Versioned v4.17_pre behaviour catalog separating weather safety, replaceable
  thermal heuristics, state stability, and unavailable-data handling.
- Pure coupled opening/blind model with explicit geometry, solar transmission,
  unilateral airflow, thermal-load components, bounds, and assumption tests.
- User-supplied Summer, Shoulder-season, and Winter comfort profiles with
  deterministic automatic/manual selection and a translated options flow.
- Dependency-free exhaustive window/blind optimizer with current/forecast
  scoring, explicit movement/uncertainty costs, and stable tie-breaking.
- Negative migration gate preventing `terraza_caliente` from becoming a new
  thermal-policy input while retaining measured radiation and real geometry.
- Typed recommendation-only weather policy with fail-closed degraded inputs,
  absolute rain/gust priority, continuous façade wind limits, and protected
  tilt geometry.
- Cost/benefit and time-based recommendation stability with versioned UTC
  memory, blind-direction deduplication, and one delivery-free grouped
  notification candidate per evaluation.
- Versioned synthetic Summer, Shoulder-season, and Winter replay evidence with
  v4.17 action provenance, physical-model comparison, and bounded sensitivity.
- Corrected joint window/blind feasibility so every non-closed resolved target
  requires a positive blind opening.
- Version-2 unit-explicit opening geometry migration and required runtime
  optimizer, stability, and source-age options.
- Typed Home Assistant source/forecast adapters, conservative degradation, one
  five-minute event-aware coordinator, and restart-safe state storage.
- Stable recommendation, blind-position, active-profile, evaluation-time, and
  safety entities with translated English/Spanish state names.
- Duplicate entity-link validation and redacted diagnostics that omit names,
  entity IDs, raw states, tokens, coordinates, and household history.
- Bounded per-façade solar projection from global radiation, `sun.sun`,
  orientation, opening height, and overhang shade.
- Public custom-HACS repository metadata, inline brand icon, and reversible
  numbered-beta installation contract, currently `0.1.0b5`.

### Fixed

- Forecast diagnostics now describe only daily-profile selection. The live
  optimizer explicitly keeps its thermal horizon unavailable because the
  configured sources provide no future irradiance, avoiding invented solar or
  indoor conditions.
- Seasonal optimization is one-sided by explicit profile season: Summer no
  longer seeks heat and Winter no longer seeks cooling on their inactive side;
  each seeks minimum absolute thermal load there, while Shoulder season remains
  symmetric and weather safety is unchanged.
- Recommendation entities expose the resolved stable `open`, `tilt`, or
  `close` target instead of the ambiguous public `hold` state. A translated,
  bounded reason attribute preserves Recorder reconstruction without changing
  entity identity or adding an entity.
- Home Assistant 2026.8 can serialize every config-flow schema for its HTTP
  frontend while empty and whitespace-only dwelling, room, and opening names
  remain rejected.
- Manual blinds are represented independently from optional automated Home
  Assistant cover entities, retaining recommendations and persisted position
  without introducing an actuator path.
- Slow room-temperature observations have one explicit maximum age independent
  from the stricter safety/environmental-source age. Version-3 entries migrate
  without changing behaviour until the new option is confirmed.
