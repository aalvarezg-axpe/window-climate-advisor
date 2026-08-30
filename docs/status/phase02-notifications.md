# Phase 02 notification validation

- Candidate: `v0.2.0b4`
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
and zero-actuator checks green.

## Live b3 installation

Commit `f42817d`, the beta release branch, annotated tag and public prerelease
identify the same `v0.2.0b3` candidate. HACS found that exact prerelease after a
repository-scoped refresh. A recent supported backup was complete before the
native update entity installed it, and the one required restart recovered on
Home Assistant 2026.8.3.

The post-restart gate reports installed b3/schema v4, one loaded entry, 4
rooms, 5 openings, 6 devices, 17 enabled unique entities and the unchanged 3
recipient subentries. The fixed native notification action is available, with
zero integration Repairs, system-log records, registered services or owned
persistent notifications. No synthetic message, configuration change or
physical action was used.

Current availability is explicitly degraded by two missing room-temperature
inputs, not by a weather-safety input or the b3 formatter: 10/12 source classes,
2/5 recommendations and 11/17 entities are ready. Three openings fail closed
with `missing_input`; all emitted blind targets remain bounded and every
non-closed target remains positive. P02-T07 is complete. The next natural
stable change must still confirm the real-device multiline rendering, and the
remaining presence/arrival matrix stays open under P02-T04.

## Single notification route cutover

A provenance audit prompted by the owner found that the legacy advisor
automation had remained enabled alongside b3 despite the earlier accepted
cutover wording. It was notification-capable, had run during the prior 24
hours, and each of its four retained traces reached the notify action. The
owner-observed single-line room/opening wording itself matches the b2 component
formatter, so both implementations were capable of producing separate advice.

No automation, script, scene, state attribute or config-entry consumer calls
the legacy automation. Its dashboard references are display-only, and that
dashboard already contains all 17 component entities. The exact legacy entity
was therefore turned off through Home Assistant's supported service with
running actions stopped, while its configuration remains intact for a
reversible emergency rollback.

After cutover, b3 remains one loaded schema-v4 entry with 4 rooms, 5 openings,
3 recipients and an available native notification action. The legacy entity is
off and its retained trace count did not change. No synthetic notification,
recipient/config-entry/dashboard change, restart or physical action occurred.

## Live b4 wind-driven rain correction

The owner rejected dwelling-wide closure for rain alone. The b4 policy keeps
the absolute 45 km/h all-façade close but applies rain restrictions only when
raw `gust × façade exposure` reaches 0.5 km/h. Zero/near-zero gust and leeward
façades retain the optimizer target through the normal wind policy; exposed
façades retain the existing light-rain, protected-tilt and overhang projection
checks. Missing or stale rain, gust or direction still degrades fail-closed.

A redacted live capability audit found zero distinct gust-direction sensors
and zero weather attributes carrying gust direction. B4 therefore reuses the
existing configured typed direction source without a schema, selector or
configuration change. Unit coverage includes cardinal/intercardinal façades,
zero and near-zero gust, leeward rain up to the absolute limit, protected tilt,
missing/stale data and the production adapter's gust/direction delivery. The
focused policy/application/adapter/notification/replay gate passes 75 tests;
the canonical gate passes 179 tests at 95.75% with lint, formatting, strict
typing, replay, privacy, artifact/secret and zero-actuator checks green.

Commit `ee69f38`, the beta release branch, annotated tag and public prerelease
identify the same `v0.2.0b4` candidate. The automatic-backup action did not
produce a verifiable artifact and was rejected; a supported full Supervisor
backup including the database completed before HACS downloaded exactly b4.
Configuration validation passed, and one observed down/up restart recovered on
Home Assistant 2026.8.3.

The post-restart gate confirms b4/schema v4, one loaded entry, 4 rooms, 5
openings, 3 recipients, 6 devices and 17 enabled unique entities. The legacy
automation remains present and off, leaving the component as the sole active
advice route. The native notification action is available, with zero duplicate
identities, integration Repairs, system-log records, services or owned
persistent notifications. No synthetic message, configuration/recipient
change or physical action occurred.

Two missing external inputs currently leave 10/12 source classes, 2/5
recommendations and 11/17 entities ready. All reported blind targets remain
bounded and every non-closed target is positive. This does not block P02-T09;
P02-T04 retains the natural-device multiline and presence/arrival matrix.

## Room-source topology audit

The owner identified the six new display devices as Salón, Baño, Despacho,
Cocina and the two bedrooms Anto and Eli. A redacted registry check confirms
that every device supplies exactly one enabled native temperature sensor and
one enabled native humidity sensor, so sensor identity is no longer ambiguous.

The live integration nevertheless contains four room subentries—Salón,
Despacho, Cocina and one generic Dormitorio—and five openings, only one of
which belongs to that generic bedroom. Historical live gates show the same
four-room topology from the component's first deployment. The immutable v4.17
automation also actively models those four rooms; Baño appears only in a
commented block explicitly pending a temperature entity. It was therefore not
deleted during this task or after component deployment.

Anto and Eli are distinct bedrooms and the owner confirms that their façades
share orientation. Orientation alone does not establish which bedroom owns the
existing generic opening or the other opening's width, height, overhang,
rain protection, tilt and blind geometry. P02-T10 therefore remains blocked
before any partial source assignment. No room flow was submitted, no entry was
reloaded, and no notification or physical action was called.
