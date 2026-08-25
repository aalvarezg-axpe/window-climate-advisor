# Phase 01 shadow status

- Status: pre-shadow gate incomplete; clock not started
- Candidate: `v0.1.0b4` / commit pending publication
- Candidate route: public GitHub prerelease through custom HACS
- Target: Home Assistant Core 2026.8.2
- Baseline: one available `v4.17_pre` automation
- Observation duration after the gate: four consecutive calendar days

## Completed gate evidence

- The named full pre-deployment backup exists.
- Home Assistant configuration validation passed before the candidate restart.
- HACS reports the exact candidate installed.
- Restart unavailability and successful Core recovery were observed.
- Exactly one config entry is loaded at schema version 3 pending the v4
  migration.
- Four verified rooms and five accepted openings are configured.
- All five openings declare a physical manual blind; no nonexistent contact or
  automated cover entity was invented.
- The entry exposes 17 unique informational entities without duplicates.
- A deliberate entry reload retained the same 17-entity inventory.
- Downloadable diagnostics are redacted and report five manual blinds, zero
  covers, zero contacts, and no domain Repair.
- The current system log contains no entry for this integration.
- The integration owns no service, notification, helper, or physical action.
- The `v4.17_pre` baseline remains available.

## Open gate

The owner approved and the supported options flow accepted all comfort and
runtime values. The first complete evaluation exposed one valid slow
room-temperature observation older than the shared 15-minute boundary while
all safety/environmental inputs were ready. Candidate `v0.1.0b4` must be
published, installed, migrated, and explicitly configured with the provisional
60-minute room boundary while retaining 15 minutes for safety/environmental
sources. The reload/restart and clean-runtime checks must then pass before the
clock starts.

Shadow start UTC: not started

Shadow end UTC: not scheduled
