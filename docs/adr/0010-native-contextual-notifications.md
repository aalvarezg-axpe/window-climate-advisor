# ADR 0010 — Native contextual notification delivery

- Status: accepted for Phase 02
- Date: 2026-08-30
- Sources: owner presence requirements, P01-T17, and Home Assistant 2026.8

## Decision

Represent each notification recipient as one config subentry containing an
explicit `person` entity and an explicit native `notify` entity. Delivery uses
only Home Assistant's fixed `notify.send_message` action targeted at that
entity. The integration never stores an arbitrary service string, derives an
action from a person/device name, or depends specifically on Mobile App.

Duplicate persons and duplicate notification targets are invalid. The config
flow accepts currently unavailable entities when they still exist in the entity
registry, but requires the native action surface to be registered. Runtime
delivery must revalidate presence and target availability and isolate a failed
recipient from the advisor evaluation and all other recipients.

Existing schema-v4 entries require no migration: no recipient subentry means
notification delivery is disabled. Diagnostics expose only a recipient count,
never person IDs, notification entity IDs, presence, device names, or message
content.

## Consequences

- The existing grouped stable-change candidate remains the only ordinary
  notification trigger.
- Away-time changes are discarded rather than queued.
- A later arrival uses the native non-home to `home` state edge and a fresh
  evaluation; startup restoration is ignored, so no presence ledger is needed.
- No helper, service-name parser, new entity, dependency, notification queue,
  or physical-action path is introduced.
