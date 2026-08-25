# Phase 01 shadow status

- Status: shadow observation running
- Candidate: `v0.1.0b4` / commit `f9d91aa`
- Candidate route: public GitHub prerelease installed through custom HACS
- Target: Home Assistant Core 2026.8.2
- Baseline: one available `v4.17_pre` automation
- Observation duration after the gate: four consecutive calendar days

## Completed gate evidence

- The named full pre-deployment backup exists.
- Home Assistant configuration validation passed before the candidate restart.
- HACS reports the exact candidate installed.
- Restart unavailability and successful Core recovery were observed.
- HACS reports installed `v0.1.0b4`, whose annotated tag and release branch
  resolve to commit `f9d91aa`.
- Exactly one config entry is loaded at schema version 4.
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
- All owner-approved profiles and runtime values are stored through the
  supported options flow: safety/environmental age remains 15 minutes and the
  room-temperature age is provisionally 60 minutes.
- The explicit reload and final full restart both completed. After the restart,
  required sources initially degraded safely and recovered without manual
  intervention; the final evaluation reports 12 ready source classes, five
  non-degraded recommendations, five numeric blind targets, five boolean
  safety states, active Summer profile, and available forecast.
- The final inventory is one loaded entry, six devices, and 17 available
  entities with 17 unique IDs and no duplicates or disabled entities.
- Final Repairs, system-log, integration-service, and owned persistent-
  notification counts are zero.

## Observation in progress

Record rain, heat, and sun coverage; recommendation/reason changes; source
degradation and recovery; and comparison with `v4.17_pre`. The 60-minute room
boundary remains provisional and must be assessed from this evidence. Do not
change options, deliver notifications, or introduce physical actions during
the period without stopping and restarting the comparison explicitly.

Codex heartbeat `seguimiento-shadow-window-climate-advisor` performs a
read-only checkpoint every six hours through the scheduled end. It may update
and publish only redacted observation evidence on the feature branch; it must
not change Home Assistant options, reload/restart Core, call a service, or
deliver a notification/action.

## Checkpoints

| Checked UTC | Runtime and integrity | Weather/behaviour evidence |
|---|---|---|
| 2026-08-25T14:33:25Z | Candidate/schema, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, clean Repairs/logs/services/owned notifications, and the available baseline remain correct. One report-local room-temperature source exceeded the provisional 60-minute age: 11/12 source classes were ready, one of five recommendations degraded, and its recommendation/blind entities were unavailable as designed. | Solar source was ready and `sun.sun` remained above the horizon; Summer profile and forecast were active. Recorder since shadow start contains `open`, `tilt`, `close`, `hold`, and explicit `degraded` recommendation states. Seven degradation episodes were reconstructed: two whole-dwelling episodes recovered in under one minute, while five were partial; one partial episode was still open after about 178 minutes. Safety history contained `on` or explicit `unavailable`, never an unsafe observation presented as safe; current ready targets had zero non-closed/0%-blind violations. No explicit rain-safety event has occurred yet. |

The open partial episode proves that 60 minutes is not sufficient to keep this
source continuously usable, but does not yet distinguish a healthy sparse
report cadence from a sensor fault. Do not raise the threshold during the
shadow period; record its recovery or persistence and assess it at closure.

Shadow start UTC: 2026-08-25T08:26:50Z

Scheduled shadow end UTC: 2026-08-29T08:26:50Z
