# ADR 0010 — Native contextual notification delivery

- Status: accepted for Phase 02
- Date: 2026-08-30
- Sources: owner presence requirements, P01-T17, and Home Assistant 2026.8

## Decision

Represent each notification recipient as one config subentry containing only
an explicit `person` entity. At delivery time, follow the person's native
`device_trackers` attribute, retain Mobile App trackers, join each tracker to
its sibling native `notify` entity through Home Assistant's entity/device
registries, and retain only trackers whose own state is `home`. Delivery uses
only Home Assistant's fixed `notify.send_message` action targeted by entity ID.
The integration never stores a target or arbitrary service string and never
derives an action from a person/device/entity name.

Duplicate persons are invalid. The config flow requires the person, at least
one associated Mobile App notification target in the registries, and the native
action surface. Runtime delivery revalidates each device's presence and target
availability, suppresses duplicate target calls, and isolates a failed device
from the advisor evaluation and all other devices.

Schema-v4 revision 2 removes `notify_entity_id` from any beta revision-1
recipient subentry while retaining its person and stable subentry identity.
The major schema stays at v4 so the verified `v0.1.0b5` downgrade remains
loadable. No recipient subentry still means delivery is disabled. Diagnostics
expose only a recipient count,
never person IDs, notification entity IDs, presence, device names, or message
content.

## Consequences

- The existing grouped stable-change candidate remains the only ordinary
  notification trigger.
- Away-time changes are discarded rather than queued.
- A later arrival uses the native non-home to `home` person-state edge and a
  fresh evaluation sent only to that person's associated devices then home;
  startup restoration is ignored, so no presence ledger is needed.
- The arriving person is excluded from ordinary change delivery in that same
  evaluation. Contact and cover feedback remove targets already satisfied;
  absent feedback never claims success, and manual blind advice says that its
  applied position is not observable.
- No helper, service-name parser, new entity, dependency, notification queue,
  or physical-action path is introduced.
