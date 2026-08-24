# Phase 01 — Coupled optimizer and shadow parity

- Status: draft / future
- Planned branch: `feature/01-domain-optimizer`
- Product authority: `docs/GOAL.md`
- Behavioural baseline: deployed v4.17_pre automation and versioned fixtures
- Requirements provenance: predecessor v4.18_pre tasks F04-01–F04-09
- Activation gate: P00-T06 freezes this plan after P00-T02, P00-T03, P00-T05,
  and P00-T09 have terminated

## Objective

Replace the remaining thermal heuristics with a deterministic, testable joint
window/blind optimizer, preserve absolute weather-safety priority, integrate it
as a recommendation-only Home Assistant advisor, and prove its behaviour in
shadow mode while v4.17_pre remains operational and available for rollback.

## Inherited decisions

- No physical-action path is permitted.
- v4.17_pre is the immutable behavioural baseline and operational rollback.
- The unimplemented v4.18_pre plan supplies requirements, not code or a new
  YAML automation artifact.
- Domain logic remains independent of Home Assistant and I/O.
- Evaluate the finite window/blind action space by deterministic enumeration
  before considering a solver or optimization dependency.
- Weather safety overrides thermal benefit. Missing, stale, or uncertain safety
  inputs never become favourable defaults.
- Seasonal settings belong to typed integration configuration/options. Create
  separate Home Assistant helpers only if a demonstrated external consumer
  requires them.
- Shadow mode publishes informational entities and redacted diagnostics but
  does not own notifications or control actuators.

## Draft tasks

P00-T06 may minimize wording and freeze exact commands, write sets, and wave
boundaries, but it must preserve these task IDs and predecessor dispositions.

| ID | Task and acceptance | Status | Owner | Write set | Dependencies / provenance |
|---|---|---|---|---|---|
| P01-T01 | Inventory and characterize every v4.17_pre heuristic that decides legacy `P/G/I/V`, `F/H`, or modifies energy outside the physical model. Accept a versioned matrix of inputs, priority, output, fixtures, and intended keep/replace disposition that clearly separates weather safety from thermal policy. | futura | delegated wave + root review | migration docs and baseline fixtures | P00-T05/P00-T09; predecessor F04-01. |
| P01-T02 | Model and calibrate how blind opening changes solar transmission and effective ventilation/discharge for closed, tilt, and open window states. Accept explicit units, measured-versus-assumed provenance, physical bounds, monotonicity, and 0–100% sensitivity tests. | futura | delegated wave + root review | domain model, calibration docs, unit tests | P01-T01; predecessor F04-02. |
| P01-T03 | Define typed Summer, Shoulder-season, and Winter comfort profiles with lower/upper bounds, preconditioning target, hysteresis, automatic selection, and manual override. Accept schema validation, historical calibration evidence, and deterministic boundary tests without creating standalone helpers by default. | futura | delegated wave + root review | domain/config contracts and tests | P01-T01; predecessor F04-03. |
| P01-T04 | Implement a deterministic per-opening optimizer that jointly evaluates `closed/tilt/open` and blind opening `0–100%` against the seasonal objective. Accept documented objective and constraints, current/forecast horizons, uncertainty handling, movement penalty, stable tie-breaking, and exhaustive-enumeration tests. | futura | delegated wave + root review | pure domain/application code and tests | P01-T02/P01-T03; predecessor F04-04. |
| P01-T05 | Remove `terraza_caliente` as an independent cause of preventive window closure or blind lowering. Accept no thermal-policy dependency on the flag while measured radiation, wind/rain safety, and real façade/overhang geometry remain covered. | futura | delegated wave + root review | domain policy, migration mapping, tests | P01-T04; predecessor F04-05. |
| P01-T06 | Derive window/blind recommendations and any retained legacy reason mapping from optimizer output, deleting obsolete discrete thermal branches. Accept absolute rain/wind priority, explicit degraded-data results, recommendation-only outputs, and no unexplained v4.17 behaviour change. | futura | delegated wave + root review | domain/application policy and tests | P01-T04/P01-T05; predecessor F04-06. |
| P01-T07 | Add cost/benefit hysteresis and output stability for near-equivalent optima. Accept no recommendation churn from small power/percentage changes, the accepted 15-minute blind stability policy, at most one grouped notification candidate per evaluation, and notifications disabled in shadow mode. | futura | delegated wave + root review | state machine/application tests | P01-T06; predecessor F04-07. |
| P01-T08 | Validate representative multi-day Summer, Shoulder-season, and Winter replays, including summer outside temperature at 25 °C, night precooling, winter solar gain above 24 °C, no wind, partial solar exposure, stale inputs, and adverse forecasts. Accept comparison with v4.17_pre for comfort, net energy, stability, safety, and recommendation/notification counts plus sensitivity analysis for assumed parameters. | futura | delegated wave + root review | replay fixtures, simulation tests, evidence | P01-T07; predecessor F04-08. |
| P01-T09 | Integrate the accepted engine into the Home Assistant scaffold in advisor/shadow mode, replacing the planned v4.18 YAML artifact. Accept config-entry lifecycle, stable entity identity, availability/degradation, redacted diagnostics, versioned regression fixtures, canonical verification, and unchanged v4.17_pre evidence. | futura | delegated wave + root review | integration/application adapters, entities, tests, migration docs | P01-T08; local successor to predecessor F04-09. |
| P01-T10 | Deploy the integration reversibly beside the still-operational v4.17_pre baseline and run the agreed shadow comparison. Accept exact target/backup/rollback evidence, valid Home Assistant configuration, one available config entry, expected entities without duplicates, clean reload/restart behaviour, no controlled notifications or actuators, and an approved comparison report before any cutover proposal. | futura | root manager | deployment, operations evidence, Home Assistant | P00-T04/P01-T09; operational remainder of predecessor F04-09. |

## Draft phase acceptance

Phase 01 may be closed only when:

- P01-T01–P01-T10 are terminated with evidence and exact frozen acceptance
  commands;
- every predecessor F04-01–F04-09 requirement has the recorded disposition in
  `docs/GOAL.md` and no unreviewed heuristic remains;
- the canonical gate, focused physical-property tests, replay suite,
  `ponytail-review`, and phase-closing `ponytail-audit` are green;
- v4.17_pre and its accepted fixtures remain unchanged and usable for rollback;
- Home Assistant shadow verification is complete for the agreed comparison
  period without duplicate entities, configuration errors, controlled
  notifications, or physical actions;
- any intentional behavioural difference is documented and explicitly
  accepted rather than hidden as parity.

## Modification log

| Date | Task | Files/change | Verification |
|---|---|---|---|
| 2026-08-24 | P00-T08 | Created this draft by reviewing and adapting predecessor v4.18_pre tasks F04-01–F04-09 to the custom-integration architecture. | Source-to-target mapping recorded in `docs/GOAL.md`; freeze and executable commands remain assigned to P00-T06. |
