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
| 2026-08-25T14:33:25Z | Candidate/schema, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, clean Repairs/logs/services/owned notifications, and the available baseline remain correct. One report-local room-temperature source exceeded the provisional 60-minute age: 11/12 source classes were ready, one of five recommendations reported `degraded`, and its blind/safety entities were unavailable as designed. | Solar source was ready and daylight remained above the horizon; Summer profile and forecast were active. Recorder since shadow start contains `open`, `tilt`, `close`, `hold`, and explicit `degraded` recommendation states. Seven minute-grouped degradation cohorts were reconstructed: two with five openings recovered in under one minute, while five were partial; one partial interval was still open after about 178 minutes. Safety history contained `on` or explicit `unavailable`; current ready targets had zero non-closed/0%-blind violations. No explicit rain-safety reason was captured. |
| 2026-08-25T20:32:04Z | The live gate recovered without intervention: 12/12 sources and 5/5 recommendations were ready, all 17 entities were available, and candidate/schema/structure plus clean Repairs/logs/services/owned notifications and baseline remained unchanged. All five public recommendations were stable `hold`; their resolved targets were three closed and two tilt with zero non-closed/0%-blind violations. | Daylight history now contains both above- and below-horizon states; Summer profile and forecast remain active. Cumulative Recorder evidence contains 13 minute-grouped degradation cohorts: four with five openings and nine partial, all recovered by this checkpoint. The longest partial interval lasted about 238 minutes and one five-opening cohort included an interval of about 63 minutes. Safety history still contains only `on` or explicit `unavailable`; no explicit rain-safety reason was captured. |
| 2026-08-26T02:34:40Z | Availability degraded again: report-local `room_2:temperature` and `room_4:temperature` report `stale_input`, leaving 10/12 source classes ready. Two recommendations explicitly report `degraded`; their two blind and two safety entities are unavailable, so 13/17 entities are available. The other three recommendations are `hold`/`optimizer`, with two closed targets and one tilt; all ready blind targets are numeric, bounded, and satisfy the non-closed/positive-blind rule. Neither degraded opening reports safe. Candidate/schema, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/domain logs/services/active owned persistent notifications, and one available baseline remain correct. | Since the previous checkpoint, Recorder adds 18 per-opening degraded intervals in eight partial minute-grouped cohorts; 16 intervals recovered and two remain open, about 258 and 155 minutes. The cumulative total is 54 intervals in 21 cohorts (four with five openings, 17 partial). New recommendation records are one `close`, 17 `hold`, and 18 `degraded`; safety records are 16 `on` and 18 `unavailable`. Current reasons are three `optimizer` and two `stale_input`. Summer profile and forecast remain available; day/night history provides no new direct rain, heat, or irradiance evidence. No Home Assistant mutation was performed. |

The observed partial episode proves that 60 minutes is not sufficient to keep this
source continuously usable, but does not yet distinguish a healthy sparse
report cadence from a sensor fault. Do not raise the threshold during the
shadow period; record recurrence and assess it at closure.
The new overnight recurrence shows that this is not confined to the first
daytime incident or a single room source. The 60-minute threshold remains an
open acceptance finding, not authorization to raise it.

Recorder cohorts group per-opening degradation starts within the same UTC
minute; they are not proven causal incidents or exact simultaneous-outage
durations. The recovered five-opening cohort includes an interval of about
63 minutes, but does not identify a shared source or prove which freshness
boundary was exceeded. Historical source quality and reason codes were not
recorded by those entity histories; point-in-time diagnostics cannot supply
them retroactively.

Evidence limits: safety `on`/`unavailable` counts alone cannot establish the
absence of every historical false-safe result or rain event. The current
diagnostic confirms that neither degraded opening reports safe. Above/below
horizon confirms day/night coverage, not direct solar irradiance; an active
Summer profile does not prove heat exposure. Direct rain/heat/solar coverage
and the approved baseline comparison remain required at closure. These
clarifications correct the earlier overbroad safety and shared-source claims;
they do not change the observed counts or weaken acceptance gates.

Shadow start UTC: 2026-08-25T08:26:50Z

Scheduled shadow end UTC: 2026-08-29T08:26:50Z
