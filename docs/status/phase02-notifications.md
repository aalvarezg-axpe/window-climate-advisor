# Phase 02 notification validation

- Candidate: `v0.2.0b2`
- Route: public GitHub prerelease through the existing custom HACS repository
- Integration fallback: live-verified `v0.1.0b5`
- Operational rollback: frozen `v4.17_pre`
- Privacy: evidence records counts and outcomes only; no private entity ID,
  person/device name, presence state, message content, endpoint, or token

## Local acceptance

The P02-T05 focused gate passes 30 tests. The complete candidate gate passes
166 tests at 95.71% coverage with Ruff, formatting, strict mypy,
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

## Pending b2 live acceptance

Publish and install `v0.2.0b2`, verify schema v4 revision 2, then add all four
owner-authorized persons through supported config subentry flows. A redacted
preflight resolved five associated Mobile App targets (three single-device
persons and one two-device person) without names. No target is selected or
stored explicitly.

After configuration, record only installed version/schema revision, recipient
and associated-device counts, structure and availability counts, clean
Repairs/log outcomes, absence of owned backlog/services/physical calls, and
verified fallback availability. Do not send a synthetic notification solely
for verification.
