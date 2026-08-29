# Phase 01 shadow status

- Status: four-day observation closed; acceptance blocked on comparison scope
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

## Observation closed

The exact four-day window closed with positive rain, exterior heat, and solar
irradiance evidence. Home Assistant remained read-only throughout. The
deployed 60-minute room-temperature age was rejected from the evidence; the
owner selected 125 minutes for later supported-options deployment and live
verification. The independent 15-minute safety/environmental age is unchanged.

Codex heartbeat `seguimiento-shadow-window-climate-advisor` performed
read-only checkpoints every six hours. This closing checkpoint records the
final evidence and removes the heartbeat; it does not change options,
reload/restart Core, call a service, or deliver a notification/action.

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
| 2026-08-26T14:44:33Z | Availability degraded again: report-local `room_2:temperature` and `room_4:temperature` are `stale_input`, leaving 10/12 ready classes, three `hold`/`optimizer` recommendations and two explicitly `degraded`, and 13/17 available entities. The two degraded blind/safety pairs are unavailable; neither degraded opening reports safe. All three ready targets resolve to closed and have valid bounded blind targets. Installed b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/domain logs/services/active owned persistent notifications, and available v4.17_pre remain correct. | Since 08:37:38Z, 12 new degraded opening intervals form seven cohorts: one with five openings, six partial; ten intervals recovered and two remain open for 156.1/32.2 minutes. The five-opening cohort recovered with a longest interval of 5.0 minutes. Cumulative totals: 75 intervals, 33 cohorts, two open; maximum duration remains 468.7 minutes. New recommendation records: three `close`, four `open`, 17 `hold`, 12 `degraded`; safety: ten `on`, 12 `unavailable`. Summer/forecast remain available. Partial Day 2 (08:26:50Z–14:44:33Z) now contains baseline-source heat evidence: 85/129 numeric exterior records meet the approved 27 °C upper bound, 365/365 irradiance records are positive, and no positive rainfall appears in one numeric record; no unusable weather records. Sources/units/start coverage were verified; the existing identity/cadence and direct-sun limits still apply. No Home Assistant mutation. |
| 2026-08-26T20:47:51Z | The same two report-local room-temperature classes remain `stale_input`: 10/12 source classes are ready, three recommendations are `hold`/`optimizer`, two are explicitly `degraded`, and 13/17 entities are available. The degraded blind/safety pairs remain unavailable and do not report safe. The three ready resolved targets are one open and two tilt; all have numeric, bounded, positive blind targets. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, and available v4.17_pre remain correct. The system log also contains the standard global loader warning that groups unverified custom integrations; it has no candidate exception or traceback and is not an integration-attributable error record. | Both intervals open at 14:44 recovered without intervention after 212.2/34.2 minutes. Eleven new degraded intervals form five partial cohorts; nine recovered and two are open for 246.5/4.5 minutes. Two four-opening cohorts recovered in at most 1.8/1.0 minutes, and another partial interval recovered after 59.8 minutes. Cumulative totals are 86 intervals in 38 cohorts (five with all openings and 33 partial), with two open; maximum duration remains 468.7 minutes. New recommendation records: three `open`, five `tilt`, 18 `hold`, 11 `degraded`; safety: 11 `on`, 11 `unavailable`. Partial Day 2 now has 104/195 numeric exterior records at/above 27 °C, 644/645 positive irradiance records, and no positive rainfall in one numeric record; no unusable records. Source/unit/start checks and the existing identity/cadence/direct-sun limits still apply. No Home Assistant mutation. |
| 2026-08-27T02:44:44Z | The same two report-local room-temperature classes remain `stale_input`: 10/12 source classes are ready, three recommendations are `hold`/`optimizer`, two are explicitly `degraded`, and 13/17 entities are available. The degraded blind/safety pairs remain unavailable and do not report safe. The three ready resolved targets remain one open and two tilt with numeric, bounded, positive blind targets. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | Of the two intervals open at 20:47, one recovered without intervention after 60.2 minutes and one remains open for 603.4 minutes. Seven new degraded intervals form five partial cohorts; six recovered and one remains open for 15.4 minutes. The recovered intervals include one further 60.2-minute episode. Cumulative totals are 93 intervals in 43 cohorts (five with all openings and 38 partial), with two open; the new maximum duration is 603.4 minutes. New recommendation records: one `open`, one `tilt`, nine `hold`, seven `degraded`; safety: seven `on`, seven `unavailable`. Partial Day 2 has 104/251 numeric exterior records at/above 27 °C, 644/645 positive irradiance records, and no positive rainfall in one numeric record; no unusable records. Source/unit/start checks and the existing identity/cadence/direct-sun limits still apply. No Home Assistant mutation. |
| 2026-08-27T08:45:51Z | Recovery passed without intervention: 12/12 source classes, five `hold`/`optimizer` recommendations, all five blind/safety pairs, and 17/17 entities are available. Resolved targets are two closed and three tilt; all five blind targets are numeric, bounded, and coherent, including `hold`. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | Both intervals open at 02:44 recovered without intervention after 803.7/263.2 minutes. Eleven new degraded intervals in five partial cohorts also recovered; their longest duration was 58.9 minutes. Cumulative totals are 104 intervals in 48 cohorts (five with all openings and 43 partial), none open; maximum duration is 803.7 minutes. New recommendation records: three `close`, two `open`, 18 `hold`, 11 `degraded`; safety: 13 `on`, 11 `unavailable`. Summer/forecast remain available. The completed second-day weather and availability evidence is summarized below. No Home Assistant mutation. |
| 2026-08-27T14:45:04Z | One report-local room-temperature class is `stale_input`: 11/12 source classes are ready, four recommendations are `hold`/`optimizer`, one is explicitly `degraded`, and 15/17 entities are available. Its blind/safety pair is unavailable and does not report safe. The four ready resolved targets are one open and three closed; all have numeric, bounded, coherent blind targets. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | Seven new degraded intervals form six partial cohorts; six recovered and one remains open for 81.7 minutes. Cumulative totals are 111 intervals in 54 cohorts (five with all openings and 49 partial), with one open; maximum duration remains 803.7 minutes. New recommendation records: three `close`, four `open`, one `tilt`, 12 `hold`, seven `degraded`; safety: three `off`, nine `on`, seven `unavailable`. Partial Day 3 contains the first positive-rain evidence: three of five numeric rainfall records are positive; all three new safety-`off` records and two of three new `close` records occur within one minute of a positive-rain record. This is temporal alignment, not historical reason attribution: current reasons are four `optimizer` and one `stale_input`. Irradiance is positive in 377/377 numeric records, no exterior record among 108 meets 27 °C, and no weather record is unusable. No Home Assistant mutation. |
| 2026-08-27T20:49:56Z | One report-local room-temperature class remains `stale_input` and now affects two openings: 11/12 source classes are ready, three recommendations are `hold`/`optimizer`, two are explicitly `degraded`, and 13/17 entities are available. Both degraded blind/safety pairs are unavailable and do not report safe. The three ready resolved targets are closed, with numeric and bounded blind targets. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | The interval open at 14:45 recovered without intervention after 119.8 minutes. Ten new degraded intervals form five cohorts: one with all openings and four partial; eight recovered, with a longest duration of 258.2 minutes, and two are open for about 1.4 minutes. Cumulative totals are 121 intervals in 59 cohorts (six with all openings and 53 partial), with two open; maximum duration remains 803.7 minutes. New recommendation records: four `close`, two `open`, three `tilt`, 17 `hold`, and ten `degraded`; safety: five `off`, 14 `on`, and ten `unavailable`. Partial Day 3 now has four positive rainfall records out of six numeric records; all five new safety-`off` records and one of four new `close` records occur within one minute of a positive-rain record. This remains temporal alignment rather than retained reason attribution; current reasons are three `optimizer` and two `stale_input`. Irradiance is positive in 657/658 numeric records, no exterior record among 182 meets 27 °C, and no weather record is unusable. No Home Assistant mutation. |
| 2026-08-28T02:47:03Z | Three report-local room-temperature classes are `stale_input` and affect four openings: 9/12 source classes are ready, one recommendation is `hold`/`optimizer`, four are explicitly `degraded`, and 9/17 entities are available. All four degraded blind/safety pairs are unavailable and do not report safe. The one ready resolved target is open with a numeric, bounded, positive blind target. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | Both intervals open at 20:49 recovered without intervention after 9.6 minutes. Eighteen new degraded intervals form nine cohorts: one with all openings and eight partial; 14 recovered, with a longest duration of 77.0 minutes, and four remain open for about 144.7, 98.5, and twice 23.7 minutes. Cumulative totals are 139 intervals in 68 cohorts (seven with all openings and 61 partial), with four open; maximum duration remains 803.7 minutes. New recommendation records: one `open`, 16 `hold`, and 18 `degraded`; safety: 16 `on` and 18 `unavailable`, with no new `off` or `close`. Partial Day 3 retains four positive rainfall records out of six numeric records and 657/658 positive irradiance records; no exterior record among 212 meets 27 °C, and no weather record is unusable. Current reasons are one `optimizer` and four `stale_input`. No Home Assistant mutation. |
| 2026-08-28T08:47:10Z | Full recovery passed without intervention: 12/12 source classes, five `hold`/`optimizer` recommendations, all five blind/safety pairs, and 17/17 entities are available. Resolved targets are four closed and one open; all five blind targets are numeric, bounded, and coherent, including a positive target for the open state. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | All four intervals open at 02:47 recovered without intervention after 350.2, 179.5, and twice 46.5 minutes. Seven new degraded intervals in three cohorts—one with all openings and two partial—also recovered, with a longest duration of 55.3 minutes. Cumulative totals are 146 intervals in 71 cohorts (eight with all openings and 63 partial), none open; maximum duration remains 803.7 minutes. New recommendation records: one `close`, one `open`, 13 `hold`, and seven `degraded`; safety: 11 `on` and seven `unavailable`, with no new `off`. Current reasons are five `optimizer`. The completed third-day weather and availability evidence is summarized below. No Home Assistant mutation. |
| 2026-08-28T14:48:04Z | One report-local room-temperature class is again `stale_input`: 11/12 source classes are ready, four recommendations are `hold`/`optimizer`, one is explicitly `degraded`, and 15/17 entities are available. Its blind/safety pair is unavailable and does not report safe. All ready targets remain numeric, bounded, and coherent. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | Six new degraded intervals form five partial cohorts; five recovered without intervention in at most 59.9 minutes and one remains open after 185.7 minutes. Cumulative totals are 152 intervals in 76 cohorts (eight with all openings and 68 partial), with one open; maximum duration remains 803.7 minutes. New recommendation records: three `open`, eight `hold`, and six `degraded`; safety: five `on` and six `unavailable`, with no new `off` or `close`. Partial Day 4 has 8/100 numeric exterior records at/above 27 °C and 380/380 positive irradiance records; no numeric rainfall record or unusable weather record appears. Source/unit/start checks and the existing identity/cadence/direct-sun limits still apply. No Home Assistant mutation. |
| 2026-08-28T20:46:32Z | Full recovery passed without intervention: 12/12 source classes, five `hold`/`optimizer` recommendations, all five blind/safety pairs, and 17/17 entities are available. Resolved targets are two open and three tilt; all five blind targets are numeric, bounded, and positive as required. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | The interval open at 14:48 recovered after 234.3 minutes. Nineteen new degraded intervals form eight cohorts—one with all openings and seven partial—and all recovered, with a longest duration of 204.6 minutes. Cumulative totals are 171 intervals in 84 cohorts (nine with all openings and 75 partial), none open; maximum duration remains 803.7 minutes. New recommendation records: one `close`, two `open`, three `tilt`, 25 `hold`, and 19 `degraded`; safety: 20 `on` and 19 `unavailable`, with no new `off`. Partial Day 4 has 10/170 numeric exterior records at/above 27 °C and 660/661 positive irradiance records; no numeric rainfall record or unusable weather record appears. No rain alignment is inferred for the isolated `close` record. Source/unit/start checks and the existing identity/cadence/direct-sun limits still apply. No Home Assistant mutation. |
| 2026-08-29T02:46:08Z | Two report-local room-temperature classes are `stale_input` and affect three openings: 10/12 source classes are ready, two recommendations are `hold`/`optimizer`, three are explicitly `degraded`, and 11/17 entities are available. The three degraded blind/safety pairs are unavailable and do not report safe. The two ready resolved targets are one open and one tilt, both with numeric, bounded, positive blind targets. Candidate b4/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/active owned persistent notifications, available v4.17_pre, and the previously classified global loader warning remain unchanged. | Twenty-two new degraded intervals form nine partial cohorts; 19 recovered in at most 136.0 minutes and three remain open for 172.7/37.5/37.5 minutes. Cumulative totals are 193 intervals in 93 cohorts (nine with all openings and 84 partial), with three open; maximum duration remains 803.7 minutes. New recommendation records: one `open`, one `tilt`, 20 `hold`, and 22 `degraded`; safety: 19 `on` and 22 `unavailable`, with no new `off` or `close`. Partial Day 4 retains 10/195 numeric exterior records at/above 27 °C and 660/661 positive irradiance records; no numeric rainfall record or unusable weather record appears. No Home Assistant mutation. |
| 2026-08-29T08:50:44Z | Closing read-only gate retains installed `v0.1.0b4`/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, and 11/12 ready source classes. Four recommendations are `hold`/`optimizer`; one is explicitly `degraded`/`stale_input`, leaving 15/17 entities available. The degraded blind/safety pair is unavailable and does not report safe. Four ready targets are one closed and three tilt, all numeric, bounded, and coherent. Zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/owned persistent notifications; `v4.17_pre` remains available. | The three intervals open at 02:46 recovered without intervention after 241.3/59.2/59.2 minutes. Eleven new degraded intervals formed ten partial cohorts: ten recovered, with a 299.3-minute maximum, and one was open for 100.3 minutes at the checkpoint. Cumulative evidence through 08:50 is 204 intervals in 99 cohorts, with one open and an 803.7-minute maximum. New recommendation records are two `close`, 14 `hold`, and 11 `degraded`; safety records are 13 `on` and 11 `unavailable`, with no `off`. Exact Day 4 and the four-day comparison are clipped to 08:26:50Z below. No Home Assistant mutation. |
| 2026-08-29T21:42:04Z | A manual post-window read-only check retains installed `v0.1.0b4`/schema v4, one loaded entry, 4 rooms, 5 openings, 6 devices, 17 unique entities, zero duplicates/disabled entities/Repairs/integration-attributable error logs/services/owned persistent notifications, and one available `v4.17_pre` baseline. Availability is 11/12 ready source classes and 15/17 entities: one room-temperature class explicitly reports `missing_input`. Four recommendations are `hold`/`optimizer`; one is `degraded`/`missing_input`. | All four ready blind targets are numeric, bounded, and coherent; the degraded blind/safety pair is unavailable and does not report safe. Supported redacted diagnostics identify the source class but intentionally do not expose the selected source or option values, so the incident cannot be narrowed further without crossing the read-only/privacy boundary. This checkpoint is outside the fixed shadow window and adds no weather or comparison metric. No Home Assistant mutation. |

Repeated daytime and overnight episodes prove that 60 minutes is insufficient
for continuous availability. The owner identified an exact 60-minute device
cadence and selected 125 minutes as the post-shadow room-temperature boundary:
two expected cycles plus five minutes of scheduling margin. This cadence is
owner-supplied, not inferred from Recorder history. All comparison metrics use
the unchanged deployed 60-minute value; 125 minutes is not deployed yet and
must be applied through supported options and verified live. The independent
15-minute safety/environmental limit remains unchanged.

Recorder cohorts group per-opening degradation starts within the same UTC
minute; they are not proven causal incidents or exact simultaneous-outage
durations. The recovered five-opening cohort includes an interval of about
63 minutes, but does not identify a shared source or prove which freshness
boundary was exceeded. Historical source quality and reason codes were not
recorded by those entity histories; point-in-time diagnostics cannot supply
them retroactively.

Evidence limits: safety-state counts alone cannot establish the absence of
every historical false-safe result or attribute a recommendation reason. The
point-in-time diagnostics confirmed that degraded openings did not report
safe. Above/below horizon confirms day/night coverage, not direct solar
irradiance; an active Summer profile does not prove heat exposure.
Baseline-source history covers positive irradiance on Days 1–4, heat on Days 2
and 4, and positive rain on Day 3. The rain/safety/close alignment is temporal,
not a retained reason code. These clarifications do not change the observed
counts or weaken acceptance gates.

## Four-day evidence

Days 1–4 span consecutive exact windows from 2026-08-25T08:26:50Z through
2026-08-29T08:26:50Z. All five Recorder recommendation series cover every
start and contain only expected enum values. Intervals are clipped to each
exact daily window, not to the later checkpoint.

| Day | Non-degraded opening-time | At least one opening degraded | All five degraded simultaneously | Longest per-opening degraded interval |
|---|---|---|---|---|
| 1 | 70.23% | 974.2 min | 33.8 min | 468.7 min |
| 2 | 71.36% | 1,198.6 min | 10.1 min | 803.7 min |
| 3 | 74.45% | 986.1 min | 55.1 min | 350.2 min |
| 4 | 66.50% | 1,206.6 min | 140.3 min | 299.3 min |
| Four-day aggregate | 70.63% | 4,365.5 min | 239.3 min | 803.7 min |

The percentages are time-weighted over five openings. Day 1 contains 2,143.6
degraded opening-minutes, Day 2 contains 2,062.2, and Day 3 contains 1,839.9,
and Day 4 contains 2,412.3, each out of 7,200 possible. The four-day total is
8,458.0 degraded opening-minutes out of 28,800. Simultaneous duration is
computed from interval overlap, independently of minute-grouped cohorts. This
measures recorded recommendation availability, not physical safety or report
cadence.

Weather provenance: read-only retrieval of the deployed baseline's explicit
source selectors, followed by Recorder history for the same exact daily
windows; current source units were validated. No identifiers or raw readings
are stored.

| Coverage criterion | Day 1 baseline-source evidence | Day 2 baseline-source evidence | Day 3 baseline-source evidence | Day 4 baseline-source evidence |
|---|---|---|---|---|
| Positive rainfall | Not observed among three numeric records; two unusable records. | Not observed in one numeric record; no unusable records. | Observed in four of six numeric records; no unusable records. | No numeric records; no unusable records. |
| Positive global irradiance | Observed in 856 of 857 numeric records; two unusable records. | Observed in 842 of 843 numeric records; no unusable records. | Observed in 856 of 857 numeric records; no unusable records. | Observed in 819 of 820 numeric records; no unusable records. |
| Outdoor temperature at/above the approved Summer upper bound (27 °C) | Not observed among 201 numeric records; two unusable records. | Observed in 104 of 304 numeric records; no unusable records. | Not observed among 291 numeric records; no unusable records. | Observed in 10 of 255 numeric records; no unusable records. |

All three weather series cover the start of all four days, but state-change
histories do not prove continuous freshness or absence of rain/heat between
reports. These are baseline-selected sources; the integration's redacted
diagnostics do not independently expose source identity. Day 1 establishes
positive irradiance; Day 2 establishes exterior heat and positive irradiance;
Day 3 establishes positive rainfall and irradiance, but not heat. Its
rain/safety/close alignment remains temporal rather than retained historical
reason attribution. Day 4 establishes exterior heat and positive irradiance,
but contains no numeric rain record. The 60-minute room boundary is unchanged
in the deployed entry and rejected for subsequent operation.

## Baseline comparison and closure

The baseline compact helper covers the complete four-day window and contains
71 structurally valid records, including 70 recorded whole-dwelling changes.
The candidate recommendation histories also cover the complete window, and all
five candidate openings were simultaneously non-degraded for 1,394.6 minutes.
The existing accepted P01-T08 replays remain valid model-level comparisons.

A direct historical per-opening behaviour match cannot be computed validly:
the baseline stores persistent resolved window/blind codes, while the candidate
Recorder series stores the public recommendation enum. Candidate `hold` means
that no new transition is requested; the resolved stable target exists only in
current diagnostics and was not retained historically. Treating `hold` as a
resolved baseline hold would therefore compare different semantics. The
missing resolved-target history cannot be reconstructed retroactively, so no
behaviour-match percentage is asserted.

All structural, integrity, ready-target, fail-safe, error/action, release, and
weather-coverage gates pass. P01-T10 remains blocked because its approved live
comparison scope is unresolved: the owner must either accept the operational
four-day evidence together with the existing replays, or require a new shadow
with resolved-target instrumentation. In either case, the selected 125-minute
room age still requires supported-options deployment and a live gate before
P01-T10 can complete.

Shadow start UTC: 2026-08-25T08:26:50Z

Shadow end UTC: 2026-08-29T08:26:50Z
