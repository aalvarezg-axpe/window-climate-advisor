# Changelog

All notable changes will be documented here. The project intends to follow
Semantic Versioning after the first distributable integration release.

## Unreleased

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
