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

The schedule audit on 2026-08-26 found that its expiry excluded the first
post-deadline run needed to compile the report and stop the heartbeat. Only
the scheduler expiry was extended by one six-hour cadence, to
2026-08-29T14:26:50Z, to admit that closing run. The existing prompt, thread,
frequency, and notification policy were preserved and verified. The
observation end remains 2026-08-29T08:26:50Z: comparison intervals must be
clipped there, and the first run at/after that time must stop this heartbeat.

## Checkpoints

| Checked UTC | Runtime and integrity | Weather/behaviour evidence |
|---|---|---|
| 2026-08-25T14:33:25Z | Candidate/schema, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, clean Repairs/logs/services/owned notifications, and the available baseline remain correct. One report-local room-temperature source exceeded the provisional 60-minute age: 11/12 source classes were ready, one of five recommendations reported `degraded`, and its blind/safety entities were unavailable as designed. | Solar source was ready and daylight remained above the horizon; Summer profile and forecast were active. Recorder since shadow start contains `open`, `tilt`, `close`, `hold`, and explicit `degraded` recommendation states. Seven minute-grouped degradation cohorts were reconstructed: two with five openings recovered in under one minute, while five were partial; one partial interval was still open after about 178 minutes. Safety history contained `on` or explicit `unavailable`; current ready targets had zero non-closed/0%-blind violations. No explicit rain-safety reason was captured. |
| 2026-08-25T20:32:04Z | The live gate recovered without intervention: 12/12 sources and 5/5 recommendations were ready, all 17 entities were available, and candidate/schema/structure plus clean Repairs/logs/services/owned notifications and baseline remained unchanged. All five public recommendations were stable `hold`; their resolved targets were three closed and two tilt with zero non-closed/0%-blind violations. | Daylight history now contains both above- and below-horizon states; Summer profile and forecast remain active. Cumulative Recorder evidence contains 13 minute-grouped degradation cohorts: four with five openings and nine partial, all recovered by this checkpoint. The longest partial interval lasted about 238 minutes and one five-opening cohort included an interval of about 63 minutes. Safety history still contains only `on` or explicit `unavailable`; no explicit rain-safety reason was captured. |
| 2026-08-26T02:34:40Z | Availability degraded again: report-local `room_2:temperature` and `room_4:temperature` report `stale_input`, leaving 10/12 source classes ready. Two recommendations explicitly report `degraded`; their two blind and two safety entities are unavailable, so 13/17 entities are available. The other three recommendations are `hold`/`optimizer`, with two closed targets and one tilt; all ready blind targets are numeric, bounded, and satisfy the non-closed/positive-blind rule. Neither degraded opening reports safe. Candidate/schema, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/domain logs/services/active owned persistent notifications, and one available baseline remain correct. | Since the previous checkpoint, Recorder adds 18 per-opening degraded intervals in eight partial minute-grouped cohorts; 16 intervals recovered and two remain open, about 258 and 155 minutes. The cumulative total is 54 intervals in 21 cohorts (four with five openings, 17 partial). New recommendation records are one `close`, 17 `hold`, and 18 `degraded`; safety records are 16 `on` and 18 `unavailable`. Current reasons are three `optimizer` and two `stale_input`. Summer profile and forecast remain available; day/night history provides no new direct rain, heat, or irradiance evidence. No Home Assistant mutation was performed. |
| 2026-08-26T08:37:38Z | Recovery passed at 08:34 and remained confirmed: installed b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17/17 available unique entities, 12/12 ready source classes, and five `hold`/`optimizer` recommendations. Resolved targets are four closed and one tilt; all five blind targets are numeric, bounded, and coherent, including `hold`. Zero duplicates/disabled entities/Repairs/domain logs/services/active owned persistent notifications; v4.17_pre remains available. | Both previously open intervals recovered without intervention after 468.7 and 240.9 minutes, at 06:05:42Z and 04:00:56Z respectively. Nine new per-opening degraded intervals in five partial cohorts also recovered. Cumulative evidence is 63 intervals in 26 minute-grouped cohorts (four with five openings, 22 partial; no repeated opening within a cohort), none still open. New records are nine `degraded` and 11 `hold`, with matching nine safety `unavailable` and 11 `on`; current reasons are five `optimizer`. Summer/forecast remain available. The completed first-day weather/availability evidence is summarized below. |

The observed partial episode proves that 60 minutes is not sufficient to keep this
source continuously usable, but does not yet distinguish a healthy sparse
report cadence from a sensor fault. Do not raise the threshold during the
shadow period; record recurrence and assess it at closure.
The overnight recurrence shows that this is not confined to the first
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
absence of every historical false-safe result or rain event. The 02:34 UTC
diagnostic confirmed that neither degraded opening reported safe. Above/below
horizon confirms day/night coverage, not direct solar irradiance; an active
Summer profile does not prove heat exposure. Direct rain/heat/solar coverage
and the approved baseline comparison remain required at closure. These
clarifications correct the earlier overbroad safety and shared-source claims;
they do not change the observed counts or weaken acceptance gates.

## Completed daily evidence

Day 1 spans 2026-08-25T08:26:50Z–2026-08-26T08:26:50Z. All five Recorder
recommendation series cover its start and contain only expected enum values.
Intervals are clipped to this exact window, not to the later checkpoint.

| Day | Non-degraded opening-time | At least one opening degraded | All five degraded simultaneously | Longest per-opening degraded interval |
|---|---|---|---|---|
| 1 | 70.23% | 974.2 min | 33.8 min | 468.7 min |

The percentage is time-weighted over five openings: 2,143.6 degraded
opening-minutes out of 7,200 possible. Simultaneous duration is computed from
interval overlap, independently of minute-grouped cohorts. This measures
recorded recommendation availability, not physical safety or report cadence.

Weather provenance: read-only retrieval of the deployed baseline's explicit
source selectors, followed by Recorder history for the same Day 1 window;
current source units were validated. No identifiers or raw readings are stored.

| Coverage criterion | Day 1 baseline-source evidence |
|---|---|
| Positive rainfall | Not observed among three numeric records; two unusable records. |
| Positive global irradiance | Observed in 856 of 857 numeric records; two unusable records. This does not establish direct-beam sunshine. |
| Outdoor temperature at/above the approved Summer upper bound (27 °C) | Not observed among 201 numeric records; two unusable records. |

All three weather series cover the start, but state-change histories do not
prove continuous freshness or absence of rain/heat between reports. These are
baseline-selected sources; the integration's redacted diagnostics do not
independently expose source identity. Positive irradiance now has direct
baseline-source evidence; rain/heat coverage and paired behavioural comparison
remain open. The 60-minute room boundary is unchanged and not yet accepted.

Shadow start UTC: 2026-08-25T08:26:50Z

Scheduled shadow end UTC: 2026-08-29T08:26:50Z
