# Changelog

All notable changes will be documented here. The project intends to follow
Semantic Versioning after the first distributable integration release.

## Unreleased

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
- Corrected joint window/blind feasibility so every non-closed recommendation,
  including `hold`, requires a positive blind opening.
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
  `0.1.0b2` shadow-candidate installation contract.

### Fixed

- Home Assistant 2026.8 can serialize every config-flow schema for its HTTP
  frontend while empty and whitespace-only dwelling, room, and opening names
  remain rejected.
