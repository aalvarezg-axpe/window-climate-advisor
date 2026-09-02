# Phase 02 notification validation

- Candidate: `v0.2.0b7`
- Route: public GitHub prerelease through the existing custom HACS repository
- Integration/operational rollback: live-verified `v0.1.0b5`
- Behavioural baseline only: immutable `v4.17_pre` fixture; no longer deployed
- Privacy: evidence records counts and outcomes only; no private entity ID,
  person/device name, presence state, message content, endpoint, or token

## Local acceptance

P02-T13's state/notification/coordinator gate passes 33 tests; adding the
manifest gate passes 36. The complete candidate gate passes 183 tests at
95.73% coverage with Ruff, formatting, strict mypy, artifact/secret checks,
integration lifecycle, replay, privacy and safety checks.

| Boundary | Redacted evidence |
|---|---|
| Lifecycle | Schema-v4 revision-1 recipients migrate in place to person-only revision 2 without changing subentry identity or the loadable major-version downgrade path; setup, unload, reload, restart-state restoration, and migration tests pass. |
| Ordinary delivery | Native person→Mobile App tracker→device→notify joins, per-device home filtering at change and delivery time, several devices per person, malformed shared-target deduplication, away/unavailable/disabled/missing paths, deterministic latest-target batching with a normal 10-minute deadline and bounded same-opening blind pairing to 20 minutes, one grouped message per target, unchanged/degraded suppression, unload discard, and exact-call-count tests pass. |
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
four-room topology from the component's first deployment. This describes what
was executable after migration, not the complete physical inventory.

The owner's correction prompted inspection of the full predecessor source and
handoff. They preserve seven intended openings: the five executable v4.17
blocks plus Dormitorio 2 NE and Baño SO, both fully parameterized and commented
only while their real temperature entities were pending. The two bedroom
blocks have the same north-east orientation, 0.50 m overhang, 0.50 m gap and
1.20 m height. Baño retains its south-west orientation, 1.00 m overhang,
0.50 m gap, 1.20 m height and rain protection. All windows were documented
with manual blinds.

The predecessor deliberately ignored window width. The five live migrated
openings consistently use the same 1.60 m width estimate, 1.20 m height, tilt
support and manual-blind capability, so the missing openings can use that
already accepted migration boundary without inventing a new estimate. The
generic bedroom identity/opening will be reused deterministically for Anto and
an identical Eli opening will be created; swapping those labels has no thermal
or safety effect because their frozen geometries are identical. P02-T10 now
targets six rooms and seven openings transactionally. No room/opening flow had
been submitted, no entry reloaded, and no notification or physical action
called at this checkpoint.

### Restored live topology

Supported Home Assistant subentry flows now configure Salón, Baño, Despacho,
Cocina, Anto and Eli with the temperature and humidity sensor from the display
device bearing that room's name. The generic bedroom identity and opening were
reused for Anto; Eli received the same frozen north-east geometry; Baño received
the recovered south-west overhang and rain-protection geometry. No entity ID
was renamed and no helper, schema, production code, dashboard write, synthetic
message or physical action was introduced.

The first combined attempt exposed a flow-client defect in the operation, not
the integration: optional contact/cover selectors were resubmitted as null.
Home Assistant rejected the opening step and deleted the newly created rooms,
but those same nulls also invalidated restoration of the four already-updated
room subentries. Immediate read-back found the partial state—four correct new
room sources and no new topology—before it was reported as rolled back. The
corrected forward pass omitted absent optional fields and completed the target.
This required extra diagnostic and recovery reloads beyond the planned single
final reload; the deviation is retained rather than hidden.

The final redacted gate reports loaded schema v4, 6 rooms, 7 openings,
3 recipients, 8 integration devices and 23/23 available unique entities.
Diagnostics contain 14 ready source classes and seven ready recommendation,
blind and safety triples with bounded targets and no non-closed/0% violation.
All 17 entity references that already existed in the dashboard still resolve.
The legacy automation remains off, and duplicate identities, Repairs,
integration errors/services and owned persistent notifications are zero.
Focused integration coverage passes 32 tests; the canonical gate passes all
179 tests at 95.75% coverage. P02-T10 is complete.

### Bedroom identity correction

The owner subsequently identified historical Dormitorio 1 as Eli's room and
Dormitorio 2 as Anto's room; every other physical parameter is identical. The
first restoration had allocated those stable identities in the opposite
direction. A safe-refactoring audit found zero consumers of the three
provisional Eli entities across dashboards, automations, scripts, scenes,
config-entry data/options, UI groups and state attributes. The inherited
opening retained three existing dashboard references.

Supported subentry APIs deleted only the zero-consumer provisional Eli pair,
reconfigured the inherited room/opening and Eli display sources in place, and
recreated Anto from the identical geometry. The inherited three entity IDs now
belong to Eli and their dashboard references remain intact; the new Anto triple
has no stale references. One final reload retained 6 rooms, 7 openings,
3 recipients, 8 integration devices, 23/23 available unique entities,
14 ready sources and seven valid recommendation/blind/safety triples. All
17 dashboard references resolve, the legacy automation remains off, and
Repairs, integration errors/services, owned persistent notifications and
invalid targets remain zero. No entity-registry rename, dashboard write,
synthetic message or physical action occurred.

## Local b5 thermal explanation

The owner observed a natural Salón notification rendered as
`Oscilobatiente` without a parenthetical explanation. A read-only check found
the bounded reason was `optimizer`; the formatter already covered every
wind/rain restriction. P02-T11 therefore adds only one presentation rule:
optimizer-selected `tilt` and `closed` window rows say `Mejor equilibrio
térmico` (or `Better thermal balance`). Full-open rows, blind-only changes,
weather reasons, routing, policy and action boundaries remain unchanged.

The focused ordinary/arrival formatter gate passes 12 tests; adding the
manifest gate passes 15. The canonical gate passes 179 tests at 95.77% with
Ruff, formatting, strict mypy, replay, privacy, artifact/secret and
zero-actuator checks green. Consolidated Ponytail review found no further
layer to remove. No synthetic message or Home Assistant mutation was used for
the local correction.

## Live b5 thermal-explanation installation

Commit `b8a3864`, remote `release/0.2.0`, annotated tag and public prerelease
identify the same `v0.2.0b5` candidate. HACS refreshed only this custom
repository and exposed exactly b5. A new supported full backup including the
database completed with one stored copy, the backup manager idle and zero
agent errors before the native update entity downloaded the exact beta.
Configuration validation passed and the single required restart produced an
observed down/up recovery on Home Assistant 2026.8.3.

The redacted post-live gate confirms installed b5/schema v4, one loaded entry,
6 rooms, 7 openings, 3 recipients, 8 integration devices and 23/23 available
unique entities. Diagnostics contain 14 ready source classes and seven valid
recommendation/blind/safety results with no invalid target. The retained legacy
window/blind automation remains off. Duplicate identities, integration
Repairs, log matches, services and owned persistent notifications are zero.
No synthetic message, configuration/recipient change or physical action was
called. P02-T11 and P02-T04 retain only natural-device rendering/presence
evidence; the new wording will be accepted when the next genuine applicable
change produces it.

## Local b6 Summer free-cooling correction

The owner rejected the presentation-only explanation after observing that the
`Pruebas` table showed high indoor temperatures while outdoor air was suitable
for ventilation. A supported read-only reproduction separated two defects.
The live Salón source was fresh, outdoor air was 3.4 °C cooler, and façade
radiation was low. The physical model estimated about -443 W with full opening
versus -47 W with tilt, but the Summer neutral branch minimized absolute heat
flow because the room was below the preconditioning target even though it was
still above the lower comfort boundary plus hysteresis.

P02-T12 moves only the Summer free-cooling stop to that lower boundary. The
exact boundary remains neutral; Winter no-active-cooling, Shoulder symmetry,
weather safety, movement/forecast penalties, minimum benefit, stability delays,
notification routing and the zero-actuator boundary remain unchanged. A
production-shaped regression plus optimizer/application/replay suites pass
29/29. The same read-only audit found that the custom-component comparison
card still contained five historical openings and none of its room-temperature
references matched the integration's six configured sources. One supported
Lovelace save changed only that component card: it now has seven opening rows,
six exact configured room sources and no entity rename. Every other dashboard
card remained byte-equivalent in the verified configuration; no service,
notification or physical action was called.

## Live b6 Summer free-cooling installation

Commit `51d176c`, remote `release/0.2.0`, annotated tag and public prerelease
identify the same `v0.2.0b6` candidate. HACS refreshed only this custom
repository and exposed exactly b6. The supported backup manager created one
full local backup including the database with zero agent errors before the
native update entity downloaded the exact beta. The supported configuration
check passed and one observed down/up restart recovered Home Assistant 2026.8.3.
An earlier attempt to request a structured check response was rejected before
mutation because that action exposes only its simple form; the supported form
then completed normally.

The final redacted gate confirms installed b6/schema v4, one loaded entry,
6 rooms, 7 openings, 3 recipients, 8 integration devices, 23/23 available
unique entities, 14/14 ready source classes and seven valid recommendation,
blind and safety triples. The corrected Salón optimum was immediately
`open/100%`, with about 331 W benefit over the persisted stable tilt and the
50 W minimum. Without a forced refresh, the stable recommendation crossed its
10-minute opening gate and became `open` with reason `optimizer`.

The retained legacy automation remains off. Duplicate identities, integration
Repairs, log matches, services and owned persistent notifications are zero.
The `Pruebas` component card retains six configured room sources and seven
opening rows. No entity rename, synthetic notification or physical action was
called. P02-T12 terminates; P02-T04 remains open only for the naturally
observed presence/arrival delivery matrix.

## Local b7 notification batching and profile preparation

The owner's natural-device evidence showed stable room transitions arriving as
separate notifications about five minutes apart and rejected the generic
`Mejor equilibrio térmico` text as non-explanatory. P02-T13 removes only that
optimizer parenthetical while retaining rain, wind and unobservable-manual-
blind reasons in ordinary and arrival summaries.

Ordinary candidates now share one non-resetting 10-minute in-memory window
from the first retained change. The latest target/reason per opening and the
union of changed window/blind components are rendered once in deterministic
order. Only people with a usable home Mobile App route when a retained change
occurs are eligible, delivery checks home/availability again, and an arriving
person is removed from the pending ordinary batch before receiving immediate
fresh arrival advice. Unload cancels and discards the batch; no setting,
persisted queue, helper, entity, dependency, schema, service or actuator path
was added.

The focused gate passes 33/33, focused plus manifest passes 36/36, and the
canonical gate passes 183/183 at 95.73% with Ruff, formatting, strict mypy,
artifact/secret, replay, privacy and zero-actuator checks green. The first
style command accidentally began recreating the ignored repository `.venv`
without the established external environment override; it was stopped and the
reproducible environment was then fully restored from the frozen lock. No
tracked artifact or Home Assistant state was affected. Consolidated Ponytail
review removed one redundant exclusion collection and parameter, then reported
`Lean already. Ship.`

## Live b7 grouped-notification installation and Summer profile

Commit `728efd7`, remote `release/0.2.0`, annotated tag and public prerelease
identify the same `v0.2.0b7` candidate. HACS refreshed only this custom
repository and exposed b7. A supported full backup completed with the database,
one complete local-agent copy and zero agent errors before the native update
path installed the beta. The supported configuration check passed. The single
restart request lost its HTTP response while Core shut down, so it was not
repeated; read-only polling observed the expected recovery and loaded entry.

The supported complete options form preserved its other 17 values while
changing Summer lower/upper bounds to 21–24 °C, preconditioning target to
22 °C and hysteresis to 0.5 °C. A second read-only flow exposed all 21 fields
with those exact values and was aborted. The effective Summer free-cooling stop
is therefore 21.5 °C.

The final redacted gate confirms installed b7/schema v4, one loaded entry,
6 rooms, 7 openings, 3 recipients, 8 integration devices, 23/23 available
unique entities, 14/14 ready source classes and seven valid recommendation,
blind and safety triples. The retained legacy automation remains off.
Duplicate identities, integration Repairs, log matches, services and owned
persistent notifications are zero. No synthetic notification or physical
action was called. P02-T13 and P02-T14 terminate; P02-T04 remains open only for
natural-device batching and present/away/mixed/arrival delivery evidence.

## Local b8 explanatory and coupled-target correction

The owner's natural-device report was reproduced without changing Home
Assistant. Antonio and Despacho had converged to a closed window and 0% blind,
but the 10-minute message batch could precede a new 15-minute blind-direction
confirmation or omit a later percentage change in the already confirmed
direction. Cocina's modest outdoor cooling was outweighed by estimated façade
radiation, so tilt was thermally preferred to full opening. Eli alone was
degraded because its room-temperature report exceeded the configured
125-minute maximum; all shared environmental and safety sources were ready.

B8 replaces the undifferentiated thermal reason with bounded Summer causes,
keeps optimizer window/blind transitions coherent through the existing
confirmation period, marks same-direction blind changes, and makes missing or
stale room temperature explicit. The formatter only translates those evaluated
codes. No entity, option, helper, queue, dependency, schema, service or actuator
path was added. Focused domain/application/adapter/notification/entity and
diagnostic coverage passes 118/118; publication and protected deployment remain.
The canonical gate passes 187/187 at 95.75% branch coverage with Ruff,
formatting, strict mypy, artifact/secret, replay, privacy and zero-actuator
checks green. Consolidated Ponytail review reports `Lean already. Ship.`

## Live b8 explanatory and coupled-target installation

Commit `d5362ae`, remote `release/0.2.0`, annotated tag and public prerelease
identify the same `v0.2.0b8` candidate. A repository-scoped HACS information
refresh exposed exactly b8. A supported full backup then completed with Home
Assistant and the database included and zero failed agents, folders or add-ons.
The native update entity downloaded exactly b8, the supported configuration
check passed, and one observed down/up restart recovered Home Assistant
2026.8.3.

The final redacted gate confirms installed b8/schema v4, one loaded entry,
6 rooms, 7 openings, 3 recipients, 8 integration devices, 23/23 available
unique entities, 14/14 ready source classes and seven valid recommendation,
blind and safety triples. Salón, Despacho and Anto expose the bounded façade-
radiation reason; Cocina exposes that outdoor air is no longer cooler. Eli's
previously stale room source reported again after restart and recovered to a
ready full-open result, proving degradation recovery without borrowing another
room source.

The legacy automation remains off. Duplicate identities, integration Repairs,
log matches, services and owned persistent notifications are zero. No synthetic
notification, configuration/source/recipient change or physical action was
called. P02-T15 terminates; P02-T04 retains natural-device rendering and the
present/away/mixed/arrival delivery matrix.

## Local b9 direct-sun blind correction

A read-only live reconstruction found both Cocina façades outside direct solar
incidence while each retained the fixed 15% diffuse vertical estimate. Both
stable recommendations were tilt with the minimum positive 10% blind opening.
The positive-blind invariant explains the exact percentage, but diffuse load
and persisted movement cost made that target inappropriate after direct sun had
left the openings.

P02-T16 keeps the combined diffuse façade load in the window thermal balance
and independently derives direct incidence through the same façade/overhang
projection with a zero diffuse fraction. With no positive direct component,
the Summer optimizer now admits only a fully raised blind; direct sun restores
the existing complete candidate range, while Winter retains its historical
night-insulation candidate space. The notification formatter also chooses the
shortest unique configured suffix, so the live Cocina titles render as
`Cocina SO` and `Cocina NO` without physical overhang qualifiers.

The focused geometry/optimizer/evaluator/adapter/notification/replay gate
passes 69/69. The canonical WSL verifier passes 192/192 at 95.74% branch
coverage with Ruff, formatting, strict mypy, artifact/secret, replay, privacy
and zero-actuator checks green. The Windows launcher stopped before checks on
an inaccessible ignored `.venv/lib64` link; no repository artifact was changed
to work around it. Consolidated Ponytail review reports `Lean already. Ship.`
The verified b9 candidate was published and installed, but protected live
observation then showed that both no-direct-sun Cocina targets remained at 10%
beyond the confirmation period. The optimizer correctly admitted only 100%,
while the stability layer treated the required move as an optional improvement
and vetoed it because the previous 10% state scored thermally cheaper.

The b10 correction marks only this Summer no-direct-sun blind target as
required. It bypasses the optional minimum-benefit veto while preserving the
15-minute confirmation, deadband, weather policy, Winter candidates and
zero-actuator boundary. Focused state/evaluator/optimizer/adapter/notification/
replay coverage passes 71/71. The canonical WSL verifier passes 193/193 at
95.74% branch coverage with Ruff, formatting, strict mypy, artifact/secret,
replay, privacy and zero-actuator checks green. Protected publication and live
verification remain.

GitHub branch, annotated tag and prerelease published the verified b10 commit,
but the live HACS comparator listed b10 while still ranking b9 as the available
version. Installing that identifier would expose b9 as a false upgrade. The
published b10 artifact remains immutable and uninstalled; rc1 reissues the
same production correction with only manifest and release-document changes.
A fresh full backup completed before any candidate installation with database
and Home Assistant included and zero failed agents, add-ons or folders.

## Live rc1 constrained-blind installation

Commit `c2a6c77`, remote `release/0.2.0`, annotated tag and public prerelease
identify the same `v0.2.0rc1` distribution candidate; its production correction
is commit `f09a710`. HACS exposed rc1 above installed b9, the native update
entity downloaded exactly rc1, configuration validation passed, and one
observed down/up restart recovered Home Assistant 2026.8.3.

The final redacted gate confirms rc1/schema v4, one loaded entry, 6 rooms,
7 openings, 3 recipients, 8 integration devices, 23/23 available unique
entities, 14/14 ready source classes and seven valid recommendations. There
are zero disabled or duplicate entities, integration Repairs, log matches,
services and owned persistent notifications; the legacy automation remains
off.

Immediately after restart, both Cocina openings were still outside direct
solar incidence, admitted only the three 100%-blind window candidates, and
retained the restored 10% stable target. After continuous confirmation both
changed naturally to 100%, proving that rc1 preserves the delay and removes the
b9 minimum-benefit veto. Exact formatter tests cover the concise `Cocina SO`
and `Cocina NO` rows. No synthetic notification, option/source/recipient
mutation or physical action occurred. P02-T16 terminates.

## Local rc2 forecast- and occupancy-aware diffuse protection

P02-T17 retains the Summer 100% blind default when geometry reports no direct
sun, but conditionally unlocks the existing joint candidate space when current
outdoor temperature or today's first daily maximum reaches the active Summer
upper bound. While occupied, the room must also reach the upper bound; when
every selected thermal occupant is known away, the lower bound permits earlier
protection. The active profile therefore remains the only heat threshold and
the daily maximum remains context rather than an invented thermal horizon.

One optional multi-person dwelling selector separates thermal occupancy from
notification recipients. Empty selection, missing person, and
`unknown`/`unavailable` state remain conservatively occupied. The selected
people are normal coordinator inputs. Accepted no-direct-sun blind targets
below 100% carry the bounded diffuse-heat reason through the entity,
diagnostics, ordinary notification and arrival formatter. Away-time delivery
still creates no batch or message, and arrival performs a fresh occupied
evaluation. No helper, entity, dependency, queue, service, physical action or
separate heat/radiation setting was added.

The exact focused optimizer/evaluator/config/adapter/coordinator/notification/
manifest/replay gate passes 93/93. The canonical WSL verifier passes 204/204 at
95.62% branch coverage with Ruff, formatting, strict mypy, artifact/secret,
replay, privacy and zero-actuator checks green. Consolidated Ponytail review:
`Lean already. Ship.` Publication, supported occupancy reconfiguration and
protected live verification remain.

## Local rc3 Summer hot-air closure

A read-only live reconstruction reproduced the owner's Cocina report on rc1
with every source ready and no weather restriction. Outdoor air was about
0.8 °C hotter than the room. The no-direct-sun opening retained `tilt/100%`
with `outdoor_not_cooler`: closing avoided about 17.5 W of modeled heat, but
the existing 20 W recommendation-movement cost made retained tilt score lower.
The component has no contact sensor on that opening, so its current action is
stable recommendation memory rather than observed physical position.

P02-T18 makes current Summer outdoor temperature at/above room temperature a
window feasibility boundary. Only closed-window candidates remain, and the
existing `outdoor_not_cooler` reason bypasses optional movement, uncertainty,
minimum-benefit and coupled-blind delay for the window close. Blind scoring and
confirmation remain independent; cooler-air reopening retains the existing
benefit and opening-improvement gates. No new threshold, option, selector,
entity, helper, dependency, queue, service or actuator path was added.

The exact focused optimizer/state/evaluator/replay gate passes 58/58. The
canonical WSL verifier passes 207/207 at 95.62% branch coverage with Ruff,
formatting, strict mypy, artifact/secret, replay, privacy and zero-actuator
checks green. Consolidated Ponytail review reports `Lean already. Ship.` Rc3
combines this correction with the accepted but not yet installed rc2 occupancy
and diffuse-protection work; publication and protected live verification
remain.

## Live rc3 occupancy and hot-air deployment

Commit `a0bf991`, remote `release/0.2.0`, annotated tag and the public
prerelease identify the same `v0.2.0rc3` candidate. HACS exposed rc3 above the
installed rc1. Before installation, a supported complete backup finished with
Home Assistant, the database, all available add-ons and data folders, one
positive-size stored copy, and zero failed agents, add-ons or folders. The
native update entity downloaded exactly rc3, configuration validation passed,
and one down/up restart was observed.

The supported dwelling reconfigure flow preserved all eight existing climate
source fields and stored Elisa and Antonio as exactly two thermal occupants;
the three notification recipients remain a separate unchanged contract. The
final redacted gate reports rc3/schema v4, one loaded entry, 6 rooms, 7
openings, 3 recipients, 8 devices, 23/23 available unique entities, 14/14
ready source classes and seven valid recommendation, blind and safety triples.
There are zero disabled or duplicate entities, integration Repairs, log
matches, services or owned persistent notifications. The retained legacy
automation remains off.

By final inspection, outdoor air was again cooler than the Cocina room, so the
reported hot-air boundary could not be truthfully reobserved. Both Cocina
targets were closed at that instant, but that is not recorded as causal proof
of P02-T18. The exact production-shaped positive delta and equality cases are
instead carried by the accepted 58-test focused gate and the 207-test canonical
gate. No synthetic notification or physical action was called. P02-T17 and
P02-T18 terminate; P02-T04 retains only natural-device batching and the
presence/arrival observation matrix.

## Local rc4 single-round notification pairing

P02-T19 corrects the deterministic mismatch between the normal 10-minute
ordinary notification batch and the existing 15-minute blind confirmation. At
the normal deadline, only a retained window change whose own opening still has
a blind pending confirmation is rescheduled. It retries at the existing
5-minute coordinator cadence and stops at 20 minutes from the first change.
A confirmed blind enters the existing latest-state/component-union merge, so
the final multiline body contains both the window and blind work; cancellation
or the hard bound releases the window-only message. Blind-only batches,
unrelated openings, arrival delivery, presence gates and unload discard are
unchanged.

The focused state/notification/coordinator gate passes 38/38. The canonical
WSL verifier passes 209/209 at 95.64% branch coverage with Ruff, formatting,
strict mypy, artifact/secret, replay, privacy and zero-actuator checks green.
Consolidated Ponytail review reports `Lean already. Ship.` Publication and
protected live verification remain.

## Live rc4 single-round deployment

Commit `de5a8e1`, remote `release/0.2.0`, annotated tag and the public
prerelease identify the same `v0.2.0rc4` candidate. A repository-scoped HACS
refresh exposed exactly rc4 above installed rc3. Before installation, a
supported full backup including the database completed and returned a backup
identifier. The native update entity installed exactly rc4, the supported
configuration check passed, and one down/up restart recovered Home Assistant
2026.8.3.

The final redacted gate reports rc4/schema v4, one loaded entry, 6 rooms, 7
openings, 3 recipients, 8 devices, 23/23 available unique entities, 14/14 ready
source classes and seven valid recommendation, blind and safety triples. There
are zero disabled or duplicate entities, integration Repairs, log matches,
services or owned persistent notifications. The retained legacy automation
remains off. No synthetic message, configuration change or physical action was
called. P02-T19 terminates; P02-T04 retains natural-device confirmation of the
new single-round behavior and the remaining presence/arrival matrix.

## Local rc5 compact and complete work-round summary

Natural rc4 evidence confirms one grouped seven-window message, but the mobile
parentheticals repeat full diagnostic sentences and the blind section omits a
stable position whenever only the window target changed. P02-T20 keeps the
same candidate, batching and delivery path while replacing mobile-only thermal
phrases with compact bilingual action categories. Every blind-capable opening
shown for a window change now includes its stable recommended blind percentage;
only an actual blind change receives a compact parenthetical.

The related thermal audit changes no decision. At equal blind position the
existing model transmits façade radiation at 1.0 through a fully open aperture
and at the provisional 0.55 coefficient through closed glazing, so closing
reduces modeled solar load by 45% while ventilation competes through its own
load term. The new characterization makes that assumption explicit without
inventing an aperture view factor or calibration option.

The focused thermal/notification gate passes 30/30 and the focused gate plus
manifest passes 33/33. The canonical WSL verifier passes 222/222 at 95.64%
branch coverage with Ruff, formatting, strict mypy, artifact/secret, replay,
privacy and zero-actuator checks green. Consolidated Ponytail review reports
`Lean already. Ship.` Publication and protected live verification remain.

## Live rc5 compact-summary deployment

Commit `d41b873`, remote `release/0.2.0`, annotated tag and the public
prerelease identify the same `v0.2.0rc5` candidate. A repository-scoped HACS
refresh exposed exactly rc5 above installed rc4. A supported full backup with
database completed first, the native update entity installed exactly rc5, the
supported configuration check passed, and one down/up restart recovered Home
Assistant 2026.8.3.

The first read immediately after restart captured 8/14 source classes and 9/23
entities ready. Without a forced refresh, reload or second restart, the next
read recovered 14/14 sources, 23/23 entities and seven valid recommendation,
blind and safety triples. The final redacted gate retains one loaded schema-v4
entry, 6 rooms, 7 openings, 3 recipients and 8 devices, with zero disabled or
duplicate entities, integration Repairs, log matches, services or owned
persistent notifications. The legacy automation remains off. No synthetic
message, configuration change or physical action was called. P02-T20
terminates; P02-T04 retains natural-device rendering of rc5 and the remaining
presence/arrival matrix.

## Local rc6 advisor-day preparation

The owner confirmed that the custom component, not the retired automation,
must start each household day from the manual assumption that windows are
closed and blinds are down. P02-T21 adds one native options-flow time with an
08:00 local default, one versioned local-date marker and a native boundary
refresh. The existing periodic evaluation catches a boundary missed during a
restart. Resetting clears prior pending stability and the non-persistent
ordinary notification batch before the normal optimizer runs; configured
contact and cover observations remain current physical inputs.

A read-only Home Assistant audit from 2026-09-02 00:00 through 10:26 CEST found
one loaded rc5 entry, three configured recipients and four valid native Mobile
App routes. Recorder contains zero stable window-target changes, zero stable
numeric blind-target changes and zero real recipient arrivals. Those are the
only component delivery triggers, so it sent no notification today by that
checkpoint. The 37 recorded recommendation/blind availability transitions are
explicitly non-actionable, and the current system log contains zero delivery
failures. No Home Assistant state changed during the audit.

The P02-T21 focused state/evaluator/config/adapter/coordinator/lifecycle gate
passes 98/98; adding the manifest contract passes 101/101. The canonical WSL
gate passes 242/242 at 95.05% branch coverage with Ruff, formatting, strict
mypy, artifact/secret, replay, privacy and zero-actuator checks green.
Consolidated Ponytail review inlined one single-use validator for a net eight
lines removed, then found the result lean. Publication and protected deployment
remain.
