# Phase 02 notification validation

- Candidate: `v0.2.0b1`
- Route: public GitHub prerelease through the existing custom HACS repository
- Integration fallback: live-verified `v0.1.0b5`
- Operational rollback: frozen `v4.17_pre`
- Privacy: evidence records counts and outcomes only; no private entity ID,
  person/device name, presence state, message content, endpoint, or token

## Local acceptance

The frozen P02-T03 focused gate passes 20 tests. The complete candidate gate
passes 164 tests at 95.85% coverage with Ruff, formatting, strict mypy,
artifact/secret checks, integration lifecycle, replay, and safety checks.

| Boundary | Redacted evidence |
|---|---|
| Lifecycle | Current schema-v4 entries load with zero or more optional recipient subentries; setup, unload, reload, restart-state restoration, and migration tests pass. |
| Ordinary delivery | Present, away, mixed-recipient, unavailable-target, deterministic ordering, one grouped message, unchanged/degraded suppression, and exact-call-count tests pass. |
| Failure isolation | A native notification failure is redacted, does not block another recipient, and cannot change evaluation or actuator state. |
| Arrival | Only a real configured non-home-to-`home` edge requests fresh advice for that person. Startup, repeated `home`, and unavailable recovery do not count; the arriving person is excluded from any simultaneous ordinary message. |
| Actionability | Contact/cover feedback removes targets already satisfied. Missing physical feedback does not claim success, and an unobservable manual blind position is identified explicitly. |
| Privacy | Diagnostics expose only recipient count. Logs omit recipient/target IDs and exception text; no queue, coordinates, device IDs, message history, or persistent notification is owned. |
| Physical safety | Production contains no window, cover, shutter, awning, HVAC, or other actuator call. The sole new service boundary is fixed `notify.send_message`. |

## Live acceptance

Pending: publish the immutable prerelease, create or confirm a current backup,
install it through HACS, and explicitly configure owner-selected person-to-notify
mappings. The mapping will not be inferred from private names or devices.

After configuration, record only the installed version/schema, structure and
availability counts, exact notification counts for the bounded presence matrix,
clean Repairs/log outcomes, absence of owned backlog/services/physical calls,
and verified fallback availability.
