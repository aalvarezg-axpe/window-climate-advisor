# ADR 0001 — Modular custom integration with a pure domain core

- Status: accepted
- Date: 2026-08-24

## Context

The current advisor has grown into a versioned decision engine with thermal and
solar models, weather/history integration, persistent hysteresis, consolidated
notifications, and more than one hundred regression/simulation tests. Keeping
that behaviour in one large YAML/Jinja automation makes validation, state
migration, configuration, and reuse increasingly difficult.

Home Assistant requires recognizable integration entrypoints, but it does not
require the decision model to depend on Home Assistant internals.

## Decision

Build one custom integration named `window_climate_advisor`. Keep its
Home Assistant entrypoints at the integration root and isolate domain,
application, and adapter modules inside the same distributable package.

The domain core:

- accepts typed snapshots and configuration;
- returns typed recommendations and diagnostics;
- performs no I/O and imports no Home Assistant modules;
- owns geometry, ventilation, thermal balance, safety priority, hysteresis, and
  recommendation transitions;
- is exercised directly by deterministic tests and predecessor replays.

The Home Assistant adapter owns config flows, subentries, state conversion,
subscriptions, coordinator lifecycle, entity publication, supported storage,
and redacted diagnostics.

## Consequences

- The repository is more structured than a generated Home Assistant skeleton,
  while remaining installable as one custom integration.
- Domain tests are fast and do not require a Home Assistant fixture.
- Platform files remain thin and must not accumulate business logic.
- No separate PyPI domain package or microservice is introduced initially.
- The architecture has more explicit boundaries, which require typed contracts
  and deliberate mapping tests.

## Rejected alternatives

- Continue extending the YAML/Jinja automation: rejected for maintainability,
  validation, persistence, and configurability.
- AppDaemon-only application: rejected because UI config flows, config-entry
  migrations, entities, diagnostics, and lifecycle integration are product
  requirements.
- Separate domain package from day one: rejected as premature distribution and
  release overhead without a second consumer.
- Custom frontend configurator in the first release: rejected until standard
  Home Assistant forms and subentries prove insufficient.
