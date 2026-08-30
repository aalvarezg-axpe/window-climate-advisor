# Phase 02 notification validation

- Candidate: `v0.2.0b3`
- Route: public GitHub prerelease through the existing custom HACS repository
- Integration/operational rollback: live-verified `v0.1.0b5`
- Behavioural baseline only: immutable `v4.17_pre` fixture; no longer deployed
- Privacy: evidence records counts and outcomes only; no private entity ID,
  person/device name, presence state, message content, endpoint, or token

## Local acceptance

The P02-T07 focused gate passes 28 tests. The complete candidate gate passes
167 tests at 95.75% coverage with Ruff, formatting, strict mypy,
artifact/secret checks, integration lifecycle, replay, and safety checks.

| Boundary | Redacted evidence |
|---|---|
| Lifecycle | Schema-v4 revision-1 recipients migrate in place to person-only revision 2 without changing subentry identity or the loadable major-version downgrade path; setup, unload, reload, restart-state restoration, and migration tests pass. |
| Ordinary delivery | Native person→Mobile App tracker→device→notify joins, per-device home filtering, several devices per person, malformed shared-target deduplication, away/unavailable/disabled/missing paths, deterministic ordering, one grouped message per target, unchanged/degraded suppression, and exact-call-count tests pass. |
| Failure isolation | A native notification failure is redacted, does not block another recipient, and cannot change evaluation or actuator state. |
| Arrival | Only a real configured non-home-to-`home` edge requests fresh advice for that person. Startup, repeated `home`, and unavailable recovery do not count; the arriving person is excluded from any simultaneous ordinary message. |
| Actionability | Contact/cover feedback removes targets already satisfied. Missing physical feedback does not claim success, and an unobservable manual blind position is identified explicitly. |
| Privacy | Configuration stores only persons and diagnostics expose only recipient count. Logs omit recipient/target IDs and exception text; no queue, coordinates, device names, message history, or persistent notification is owned. Registry device IDs are transient join keys only. |
| Physical safety | Production contains no window, cover, shutter, awning, HVAC, or other actuator call. The sole new service boundary is fixed `notify.send_message`. |

## Superseded b1 deployment

The immutable `release/0.2.0` branch, annotated `v0.2.0b1` tag, and public
GitHub prerelease resolve to the same candidate. HACS beta tracking was enabled
only for this repository after it listed the exact prerelease. Home Assistant
configuration validation passed, a new supported backup completed with the
database, HACS downloaded the exact version, and the required restart returned
Home Assistant 2026.8.3 without intervention.

The post-restart gate passes with installed `v0.2.0b1`, schema v4, one loaded
entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicate
identities, zero integration Repairs/log records/services/owned persistent
notifications, recipient-flow support, and the frozen baseline available. The
first immediate poll saw only 7 entities ready while startup evaluation was
settling; the subsequent coherent gate recovered to 15/17. The remaining two
unavailable entities belong to one opening explicitly degraded for one missing
input class; the other 11 source classes and four recommendations are ready.

No recommendation notification was sent because the b1 entry had zero
recipients. The owner then rejected b1's redundant explicit target selector;
the live deployment remains valid evidence for installation/lifecycle only and
will be superseded by b2 before recipient configuration.

## Live b2 installation and recipient registration

The published feature/release candidate, annotated tag, and non-draft GitHub
prerelease point to `v0.2.0b2`. HACS refreshed and downloaded that exact beta
after a valid Home Assistant configuration check and a completed supported
backup. Home Assistant 2026.8.3 recovered after installation and again after
the final verification restart.

The first broad person-only registration added all four Home Assistant persons.
The registry join then exposed five person-to-Mobile-App-device links and four
unique targets: the owner's phone was linked to both the owner and `Codex`
persons. Duplicate-call suppression prevented an ordinary double send, but
retaining `Codex` would have left an incorrect arrival route to the owner's
phone.

After the owner's clarification, the supported subentry API removed only the
`Codex` recipient. The current configuration has three explicitly authorized
persons, four person-device links, and four distinct enabled/available Mobile
App targets. The owner's person retains the phone route; the underlying Home
Assistant person/tracker association is unchanged, and no target is selected
or stored by the integration.

Post-correction reload evidence reports one loaded schema-v4 revision-2 entry,
three recipient subentries, 4 rooms, 5 openings, 6 integration devices, and 17
enabled entities with unique identities. Fifteen entities and 11/12 source
classes are ready; one `missing_input` safely degrades one opening and its
blind/safety pair. The four ready recommendations and their blind positions
are coherent, including a positive blind opening for every non-closed window
target; the degraded opening does not report safe.

There are zero integration Repairs, system-log records, registered services,
or owned persistent notifications. The fixed native `notify.send_message`
surface is available. No synthetic message, queue, YAML, `.storage` edit, or
physical action was used. `v0.1.0b5` remains the operational fallback;
read-only inspection found that `v4.17_pre` is no longer deployed, so living
rollback documentation now retains it only as an immutable behavioural
fixture.

## Remaining live acceptance

The real present/away/mixed/stable-change/arrival delivery matrix remains to
be observed through natural events. Configuration and lifecycle evidence are
complete, but no synthetic notification will be sent solely to close that
gate.

## Owner-observed presentation correction

The first naturally observed b2 delivery proved routing but exposed a compact
presentation defect: room and opening titles could repeat, orientation remained
visible for a single-opening room, and window plus blind advice shared one long
line. P02-T07 owns the correction. The local contract now uses separate
multiline window/blind sections, room-only single-opening labels,
non-duplicated multi-opening suffixes, changed/actionable components only, and
concise weather reasons carried from the evaluated policy. No private message,
recipient, room/opening name, or raw household state is retained here.

The focused formatter/state/delivery gate passes 28 tests; adding the manifest
gate passes 31. The complete b3 candidate gate passes 167 tests at 95.75%
coverage with lint, formatting, strict typing, replay, privacy, artifact/secret,
and zero-actuator checks green. Publication, HACS installation, restart, and
natural-message observation remain; b2 stays installed until that reversible
deployment completes.
