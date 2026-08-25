# Phase 01 shadow status

- Status: pre-shadow gate incomplete; clock not started
- Candidate: `v0.1.0b3` / commit `28a1d46`
- Candidate route: public GitHub prerelease installed through custom HACS
- Target: Home Assistant Core 2026.8.2
- Baseline: one available `v4.17_pre` automation
- Observation duration after the gate: four consecutive calendar days

## Completed gate evidence

- The named full pre-deployment backup exists.
- Home Assistant configuration validation passed before the candidate restart.
- HACS reports the exact candidate installed.
- Restart unavailability and successful Core recovery were observed.
- Exactly one config entry is loaded at schema version 3.
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

The owner has not yet supplied the required Summer, Shoulder-season, and Winter
comfort bounds, preconditioning targets, hysteresis, or the seven runtime
optimizer/stability/source-age settings. The integration intentionally exposes
five degraded recommendations and unavailable dependent values until these
options are completed through the UI/API. No default will be inferred.

Shadow start UTC: not started

Shadow end UTC: not scheduled
