# ADR 0010 — Native contextual notification delivery

- Status: accepted for Phase 02
- Date: 2026-08-30
- Last amended: 2026-08-31
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
  notification trigger. It carries the already-evaluated policy reason only
  for presentation; delivery does not reconstruct weather decisions.
- Ordinary and arrival bodies use the same deterministic two-section format:
  window rows, then blind rows. Single-opening rooms use the room title alone;
  multi-opening rooms add the shortest unique word prefix of their configured
  opening suffix, omitting later physical qualifiers such as overhang wording
  when orientation already distinguishes the row. Only changed or
  still-actionable components appear and weather-forced rows show a concise
  reason. Summer optimizer targets below full opening carry the bounded cause
  already selected by evaluation; delivery never infers it from text or state.
- Ordinary candidates normally merge for 10 minutes beginning at the first
  change. If a retained window change has a blind on the same opening still
  inside its existing confirmation period, delivery retries on the existing
  5-minute coordinator cadence up to 20 minutes from that first change. A
  confirmed blind joins the same deterministic message; cancellation or the
  hard bound flushes the window-only advice. Blind-only and unrelated batches
  retain the normal deadline. The batch is memory only, is discarded on
  unload, and introduces neither a configurable timer nor a persisted queue.
- A coupled optimizer window/blind target is published coherently: a new blind
  direction reuses the existing 15-minute confirmation before the window state
  changes, while a confirmed same-direction percentage change is explicitly
  marked for notification. The deadband suppresses the target rather than
  changing a published percentage silently. Weather restrictions stay
  immediate.
- Away-time changes are discarded rather than queued.
- A later arrival uses the native non-home to `home` person-state edge and a
  fresh evaluation sent only to that person's associated devices then home;
  startup restoration is ignored, so no presence ledger is needed.
- Ordinary eligibility requires a usable home route both when a retained
  change occurs and at delivery. An arriving person is removed from a pending
  ordinary batch and receives only the fresh arrival summary. Contact and cover
  feedback remove targets already satisfied;
  absent feedback never claims success, and manual blind advice says that its
  applied position is not observable.
- No helper, service-name parser, new entity, dependency, notification queue,
  or physical-action path is introduced.
