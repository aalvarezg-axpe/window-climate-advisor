# Phase 01 — Coupled optimizer and shadow parity

- Status: active
- Started: 2026-08-24
- Planned branch: `feature/01-domain-optimizer`
- Product authority: `docs/GOAL.md`
- Behavioural baseline: deployed v4.17_pre automation and versioned fixtures
- Requirements provenance: predecessor v4.18_pre tasks F04-01–F04-09
- Activation gate: P00-T06 and the Phase 00 closing gate have terminated; then
  create `feature/01-domain-optimizer` from the updated `develop`

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

## Frozen tasks

The imported IDs and dispositions are immutable. A task may reduce its write
set after review, but may not add a new platform, dependency, persisted schema,
or physical action implicitly.

| ID | Task and acceptance | Status | Owner | Write set | Dependencies / provenance |
|---|---|---|---|---|---|
| P01-T01 | Inventory and characterize every v4.17_pre heuristic that decides legacy `P/G/I/V`, `F/H`, or modifies energy outside the physical model. Accept a versioned matrix of inputs, priority, output, source scenario, owning future task, and keep/replace disposition; no legacy evaluator. | terminada | delegated wave + root review | `docs/migration/v4_17_behavior_matrix.md`, `tests/fixtures/migration/case_catalog.json`, `tests/characterization/test_case_catalog.py`, this plan's evidence only | Schema v1 catalogs 27 traced cases, all S02–S14 and `P/G/I/V/F/H`; five integrity tests enforce sources, owners, safety/thermal dispositions, and privacy/action boundaries. No legacy evaluator or production code was created. |
| P01-T02 | Model and calibrate how blind opening changes solar transmission and effective ventilation/discharge for closed, tilt, and open window states. Accept explicit units, measured-versus-assumed provenance, physical bounds, monotonicity, and 0–100% sensitivity tests. | terminada | delegated wave + root review | `domain/__init__.py`, `domain/models.py`, `domain/geometry.py`, `domain/ventilation.py`, `domain/thermal.py`, corresponding `tests/unit/domain/`, one calibration ADR | ADR 0004 and five pure modules implement bounded closed/tilt/open geometry, linear blind solar/free-area sensitivity, unilateral airflow, and component thermal loads. Focused 11/11 and canonical 34/34 pass at 100% branch coverage with no HA import or new dependency. |
| P01-T03 | Define typed Summer, Shoulder-season, and Winter comfort profiles with lower/upper bounds, preconditioning target, hysteresis, automatic selection, and manual override. Accept schema validation, calibration provenance, and deterministic boundaries without standalone helpers by default. | terminada | root contract + root implementation | `domain/profiles.py`, `const.py`, `config_flow.py`, `translations/en.json`, `translations/es.json`, profile/config-flow tests, one profile ADR | ADR 0005, typed profiles, deterministic auto/manual selection, and a translated options flow store complete user-supplied bands without fake defaults or helpers. Focused 18/18 and canonical 44/44 pass at 100% branch coverage. |
| P01-T04 | Implement a deterministic per-opening optimizer that jointly enumerates `closed/tilt/open` and blind opening `0–100%` against the seasonal objective. Accept current/forecast horizons, uncertainty, movement penalty, stable tie-breaking, and exhaustive tests without a solver dependency. Any feasible non-closed window recommendation, including the target paired with `hold`, requires blind opening above 0%; an opening without a configured blind is restricted to 100%. An observed non-closed/0% current action remains comparable but cannot win. | terminada | root manager | `domain/optimizer.py`, minimal additions to `domain/models.py`, `tests/unit/domain/test_optimizer.py`, optimizer ADR | ADR 0006 now covers optional blind capability. A no-blind opening exhausts only 2/3 states at 100% and rejects inconsistent current input. Focused 9/9 and canonical 101/101 pass at 100% without a dependency, setting, helper, or entity. |
| P01-T05 | Prove that `terraza_caliente` is absent as an independent decision input. This is a negative migration gate, not a new module: measured radiation, weather safety, and real geometry remain. | terminada | root manager | behaviour matrix and existing optimizer tests only; no new production file | C011 is explicitly `replace`; characterization scans all production Python and the plan's `rg` returns no match. Focused 13/13 and canonical gates pass without creating a production artifact. |
| P01-T06 | Derive recommendation and reason outputs from optimizer results, with absolute rain/wind priority and explicit degraded input states. Accept recommendation-only outputs and no unexplained v4.17 change. | terminada | root manager | `domain/policy.py`, `tests/unit/domain/test_policy.py`, behaviour-matrix dispositions, safety ADR | ADR 0007 and the pure policy preserve rain/gust precedence, continuous wind limits, protected tilt geometry, optimizer blind output, and fail closed on missing/stale safety observations. Focused 15/15 and canonical 67/67 pass with 481 statements/140 branches at 100%; no HA import, action, or notification surface. |
| P01-T07 | Add cost/benefit hysteresis and stable transitions. Accept no churn from small changes, the 15-minute blind policy, at most one grouped notification candidate, and notification delivery absent in shadow mode. A stable `hold` of a non-closed window must still use a positive blind target when the observed blind is at 0%, even if thermal benefit is below the ordinary movement threshold. | terminada | root manager while the persistent executor remains suspended | `domain/state_machine.py`, `application/__init__.py`, `application/state.py`, minimal optimizer result/test additions, state-machine/application tests, behaviour-matrix dispositions | Joint transitions from `closed/0%` wait at least the blind delay and then change window/blind together; an already incoherent observed state normalizes immediately or closes. Focused 27/27 and canonical 100/100 pass at 100%. Replay inspection has no non-closed/0% state and reduces stable transitions from 33 to 30 without churn or extra candidates. |
| P01-T08 | Run representative multi-day Summer, Shoulder-season, and Winter replays. Include exterior at 25 °C in Summer, nocturnal pre-cooling, Winter solar gain above 24 °C indoors, no wind, partial solar exposure, and adverse forecast. Accept v4.17 comparison for comfort, net energy, stability, safety, recommendation/notification counts, and sensitivity of assumed parameters. | terminada | root manager while the persistent executor remains suspended | `tests/fixtures/replay/`, `tests/replay/`, `docs/status/phase01-replay.md`, living requirement update in `docs/GOAL.md` | Owner accepted partial-sun `open/100%` and zero-churn transition differences; rejected adverse `tilt/0%`. Corrected evidence is -32,335.3/-4,896.6 Wh-eq, 30/28 transitions, 30 candidates, zero churn/safety violations, and no non-closed/0% action. Focused 5/5 and canonical 100/100 pass at 100%; P01-T09 is unblocked. |
| P01-T09 | Connect the accepted engine to Home Assistant in advisor/shadow mode instead of creating v4.18 YAML. Accept lifecycle, schema migration, stable identities, availability/degradation, redacted diagnostics, and no service/notification action. | terminada | root manager; retained because the original executor remains suspended | `application/evaluator.py`, `adapters/`, `coordinator.py`, `entity.py`, `sensor.py`, `binary_sensor.py`, `diagnostics.py`, `__init__.py`, `const.py`, manifest/config-flow/schema changes, translations, focused unit/integration tests, ADR 0003/0008, README/changelog and this plan | Sensor/binary-sensor entities, five-minute/event-aware coordinator, supported `Store`, redacted diagnostics, v1→v2 migration, required options, explicit degradation, conservative binary rain, and uncertainty penalty are verified. P01-T11 corrected the discovered solar boundary separately. Canonical 134/134 passes at 96.94%; no service registration, notification delivery, helper, YAML, or actuator platform. |
| P01-T10 | Deploy reversibly beside operational v4.17_pre and run the owner-agreed shadow period. Accept exact route/target, backup, rollback, configuration validation, one entry, expected entities without duplicates, clean reload/restart, no owned notifications/actions, and an approved comparison report. | bloqueada | root manager | `.env.example` route names if needed, `docs/operations/deployment.md`, `docs/status/phase01-shadow.md`, Home Assistant external state | P01-T09/P01-T11 are terminated. The secret-safe 2026-08-25 route audit confirms API URL/token are populated but no mounted-path or SSH file route is registered. Per the stop condition, no deployment artifact or external mutation starts until the owner selects one authorized route. |
| P01-T11 | Close the imported HANDOFF scenarios 1–6 gap: convert current global horizontal irradiance plus `sun.sun` azimuth/elevation into bounded per-opening façade irradiance, including orientation and overhang shade. Accept frontal/lateral/rear, low-sun, no-radiation, and increasing-overhang property tests; missing/stale sun degrades explicitly; do not invent a forecast horizon or restore `terraza_caliente`. | terminada | root manager | `domain/geometry.py`, `adapters/home_assistant.py`, `manifest.json`, focused domain/adapter/manifest tests, ADR 0004/0009, GOAL and this plan | The P01-T09 boundary review found and P01-T11 corrected unprojected global radiation. `sun` is an explicit subscribed manifest dependency; front/side/rear/north-wrap/low-sun/zero-radiation/overhang properties and degraded sun input pass without forecast invention or `terraza_caliente`. Focused 23/23 and canonical 134/134 pass. |

## Frozen work waves

1. P01-T01 is an isolated characterization wave. It may create data and tests,
   but no implementation of the legacy YAML policy.
2. The root retains P01-T02–P01-T08 while the original persistent Luna session
   remains suspended after two consecutive silent waves. A replacement may be
   delegated only under the live `AGENTS.md` checkpoint rule or by owner
   direction; task contracts and commits remain atomic.
3. P01-T08 is a replay/evidence wave and cannot alter accepted domain policy to
   make a scenario pass. A policy correction returns to its owning task.
4. P01-T09 is an integration wave. The root owns config migrations, public
   entity/schema contracts, secrets, and final Home Assistant boundary review.
5. P01-T11 is the isolated correction of the imported solar-geometry gap. It
   may extend pure geometry and the adapter/manifest consumer, but not options,
   services, forecast invention, or physical action.
6. P01-T10 is root-only external work. No executor receives Home Assistant or
   deployment access.

## Exact local acceptance commands

Run each focused command from the repository root on the Windows workstation,
then run the canonical gate. `--no-cov` prevents a focused subset from failing
the repository-wide coverage threshold; the canonical command enforces full
branch coverage afterwards.

| Task | Focused command |
|---|---|
| P01-T01 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/characterization/test_case_catalog.py -q'` |
| P01-T02 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/domain/test_geometry.py tests/unit/domain/test_ventilation.py tests/unit/domain/test_thermal.py -q'` |
| P01-T03 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/domain/test_profiles.py tests/integration/test_config_flow.py -q'` |
| P01-T04 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/domain/test_optimizer.py -q'` |
| P01-T05 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/characterization/test_case_catalog.py tests/unit/domain/test_optimizer.py -q'`; then PowerShell `rg -n "terraza_caliente" custom_components --glob "*.py"; if ($LASTEXITCODE -eq 1) { exit 0 } else { exit 1 }`. |
| P01-T06 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/domain/test_policy.py -q'` |
| P01-T07 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/domain/test_state_machine.py tests/unit/application/test_state.py -q'` |
| P01-T08 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/replay -q'` |
| P01-T09 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/integration -q'` |
| P01-T11 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/domain/test_geometry.py tests/integration/test_adapters.py tests/integration/test_manifest.py -q'` |
| P01-T10 | `uv run --frozen python scripts/verify.py`; the route-specific backup/copy/config-check/reload/rollback commands must be resolved and recorded before this task enters `en curso`. |

Canonical gate after P01-T01–P01-T09/P01-T11 and before/after P01-T10:

```powershell
uv run --frozen python scripts/verify.py
```

## Stop conditions

- Stop and return to the root if a proposed change can call `cover.*`, control a
  window/HVAC actuator, deliver a notification, or turn missing/stale safety
  data into a favourable value.
- Do not start P01-T10 until the owner supplies an authorized mounted path,
  file-capable connection, or repository-install workflow. Freeze the resolved
  target and rollback commands before mutation; never infer them from the API
  URL/token.
- Stop for explicit owner acceptance before preserving or introducing an
  intentional v4.17 behavioural difference. Record the old case, new result,
  safety effect, and rollback consequence.
- Calibration without measured evidence remains labelled as an assumption with
  physical bounds and sensitivity tests. It must not be described as measured.
- The copied v4.17_pre/v4.16_pre fixtures and predecessor repository are
  immutable. A hash mismatch fails the task; do not refresh the expected hash.
- A failed replay identifies its owning domain task. Do not add test-only
  branches, tolerances, or fallback logic in P01-T08.
- No task may broaden its write set, add a dependency, or create a platform,
  helper, service, persistence format, or abstraction without a real consumer
  and a root plan update.

## Phase acceptance

Phase 01 may be closed only when:

- P01-T01–P01-T11 are terminated with evidence and exact frozen acceptance
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
| 2026-08-24 | P00-T06 | Froze all imported tasks, exact write sets, sequential executor waves, local focused/canonical commands, route-dependent deployment gate, and stop conditions. Ponytail kept deterministic enumeration, made `terraza_caliente` a negative gate rather than a module, and deferred each legacy assertion to its real consumer. | Nine F04 tasks remain mapped to ten P01 tasks; no actuator/notification delivery scope; Markdown/diff/canonical repository gates pass. |
| 2026-08-24 | P01-T01 | Created a readable matrix and schema-v1 JSON catalog with 27 sourced legacy boundaries. The persistent executor spent the bounded wave reading without producing a handoff, so root retained implementation when further delegation cost exceeded the documentation task. | Focused catalog suite: 5 passed; S02–S14 and `P/G/I/V/F/H` complete; all A01/A03–A10 sources represented; canonical gate passed with 23 tests and 100% owned-code branch coverage. |
| 2026-08-24 | P01-T02 | Froze ADR 0004 and implemented the dependency-free coupled geometry, airflow, and thermal load model. The same persistent executor again produced no status or artifact after two checkpoints and a direct request; root interrupted it, retained the wave, and added the observed-progress rule to `AGENTS.md`. | Focused domain suite: 11 passed; canonical gate: 34 passed, 214 statements/50 branches at 100%; Ruff, format, strict mypy, artifact/secret, and diff checks passed. |
| 2026-08-24 | P01-T03 | Froze ADR 0005 and added typed seasonal profiles, strict automatic/manual selection, cross-field validation, translated UI options, persistence, and reload. Root retained the task under the new observed-progress rule; no new executor attempt was made. | Focused profile/config-flow suite: 18 passed; canonical gate: 44 passed, 324 statements/88 branches at 100%; translations remain structurally complete and no helper entity was added. |
| 2026-08-24 | P01-T04 | Froze ADR 0006 and implemented exhaustive recommendation scoring over current/forecast loads, profile intent, movement, uncertainty, and stable tie-breaking. No solver, dependency, I/O, safety shortcut, or action path was added. | Focused optimizer suite: 7 passed; canonical gate: 51 passed, 374 statements/102 branches at 100%; Ruff, format, strict mypy, artifact/secret, and diff checks passed. |
| 2026-08-24 | P01-T05 | Closed the `terraza_caliente` requirement as a negative migration gate. Added one catalog/production assertion and deliberately created no module, flag, or replacement heuristic. | Focused catalog/optimizer suite: 13 passed; exact production `rg` returned no match; canonical gate passed with full owned-code branch coverage. |
| 2026-08-24 | P01-T06 | Froze ADR 0007 and added typed weather-safety recommendations around optimizer output. Reviewed all predecessor F04-01–F04-09 rows: all remain mapped; made the six F04-08 scenarios explicit, corrected active product status and suspended-executor ownership in the living references, and updated implemented matrix dispositions. | Focused policy suite: 15 passed; canonical gate: 67 passed, 481 statements/140 branches at 100%; Ruff, format, strict mypy, artifact/secret, diff, safety-boundary, and Ponytail reviews passed. |
| 2026-08-24 | P01-T07 | Added pure cost/time stability, optimizer avoided-cost evidence, 5/0/10/15-minute inherited transitions, blind-direction deduplication, versioned UTC state, and one value-only grouped candidate. No helper, recipient, service, callback, queue, or notification delivery was added. | Focused state suite: 24 passed including 30 days × 48 percentage samples; canonical gate: 91 passed, 680 statements/210 branches at 100%; Ruff, format, strict mypy, artifact/secret, diff, and Ponytail reviews passed. |
| 2026-08-24 | P01-T08 | Added schema-v1 synthetic three-day seasonal replays with Cxxx-sourced static v4.17 actions, common-model comfort/net-energy comparison, transition/candidate/safety metrics, all six F04-08 cases, and two bounded calibration variants. A failed raw-count assertion was triaged without production changes: 33 candidates are 33 stable boundary transitions, not false-alert churn. | Focused replay suite: 5 passed; canonical gate: 96 passed, 680 statements/210 branches at 100%. Local evidence is verified, but the task is blocked pending explicit owner acceptance of the three differences in `docs/status/phase01-replay.md`; P01-T09 remains unstarted. |
| 2026-08-25 | P01-T04 | Reopened the optimizer after owner replay review. Removed `tilt/0%` and `open/0%` from the feasible action space while continuing to score such an observed current state; documented the accepted invariant and added exhaustive/invalid-current regressions. | Focused optimizer suite: 8 passed; canonical gate: 97 passed, 680 statements/210 branches at 100%. The action space is 21/31 and a tied observed `tilt/0%` now selects `tilt/10%`; no new setting, dependency, or action path. |
| 2026-08-25 | P01-T07 | Reopened stability for the `hold` consumer of the blind/window invariant. Let an incoherent non-closed/0% state bypass only the ordinary minimum-benefit suppression, while retaining immediate close, blind deadband, and 15-minute direction confirmation semantics. | Focused state/application suite: 26 passed; canonical gate: 99 passed, 680 statements/210 branches at 100%. Regressions cover `hold` with a positive blind target and a below-threshold coherent close; no notification delivery or actuator path. |
| 2026-08-25 | P01-T07 | P01-T08 inspection found that independently accepted window/blind delays could still expose transient `tilt/0%`. Coordinated a transition from `closed/0%` behind the blind delay and made normalization immediate only when the observed state is already non-closed/0%; retained one grouped candidate. | Focused state/application suite: 27 passed; focused replay: 5 passed; canonical gate: 100 passed, 684 statements/214 branches at 100%. No replay action is non-closed/0%; nominal transitions fall from 33 to 30 with zero churn and candidates still equal transitions. |
| 2026-08-25 | P01-T08 | Recorded the owner's acceptance of differences 1 and 3 and rejection of difference 2; added the cross-layer invariant to `docs/GOAL.md`, froze it in replay assertions, and refreshed nominal/bounded-sensitivity evidence after P01-T04/P01-T07 corrections. | Focused replay: 5 passed; canonical gate: 100 passed, 684 statements/214 branches at 100%. Nominal objective is -32,335.3/-4,896.6 Wh-eq with 30/28 transitions, 30 grouped candidates, zero churn/safety violations, adverse `closed/0%`, and no non-closed/0% action. Consolidated correctness and Ponytail reviews found no defect or removable complexity; P01-T09 is locally unblocked. |
| 2026-08-25 | P01-T04 | P01-T09 exposed that the accepted optional `cover_entity_id` contract had no optimizer capability boundary. Added `has_blind`, restricted no-blind candidates/current state to 100%, and documented the real consumer without changing the normal action space. | Focused optimizer: 9 passed; canonical gate: 101 passed, 687 statements/216 branches at 100%. No solver, dependency, setting, helper, or entity was added. |
| 2026-08-25 | P01-T09 | Froze ADR 0008 and added the pure dwelling evaluator that turns typed opening snapshots into stable informational outputs while pruning removed openings and degrading incomplete configuration explicitly. | Focused application suite: 6 passed; canonical gate: 107 passed at 100%. No Home Assistant state object, service, notification, or action crossed the application boundary. |
| 2026-08-25 | P01-T09 | Migrated unit-ambiguous v1 opening geometry keys to v2 without changing entry/subentry identity, added the accepted required runtime options, and expanded rain selection to numeric or binary sensors. | Focused config/migration suite: 14 passed; canonical gate: 108 passed at 100%. English/Spanish translations and ADR 0003 remain aligned; no hidden tuning default or helper was added. |
| 2026-08-25 | P01-T09 | Added typed Home Assistant state/forecast adapters, conservative binary-rain and wrong-unit handling, one five-minute/debounced coordinator, and per-entry restart-safe state through supported `Store`. Incomplete options keep the entry repairable with explicit degradation. | Focused integration suite: 26 passed; canonical gate: 120 passed, 1,078 statements/342 branches at 96.34%. Ruff, format, strict mypy, diff, secret/artifact, migration, replay, and safety-boundary checks passed. |
| 2026-08-25 | P01-T09 | Activated setup/unload/reload for the frozen sensor/binary-sensor surface, stable entry/subentry entity and device identities, translated enum states, explicit degraded availability, defensive duplicate-link validation, and report-local redacted diagnostics. Storage writes now occur only when restart-safe state changes. Updated stale README/GOAL/ADR contracts and recorded the separately scoped P01-T11 solar-boundary gap discovered during review. | Focused integration suite: 31 passed; canonical gate: 125 passed, 1,261 statements/376 branches at 96.82%. No entity ID/name/raw state appears in diagnostics; reload creates no duplicate registry entity; no service, notification, helper, YAML, diagnostic sensor, or actuator platform exists. |
| 2026-08-25 | P01-T11 | Closed the inventory's unallocated HANDOFF solar scenarios 1–6 gap with the bounded v4.17 global-to-vertical projection, `sun.sun` dependency/subscription, per-opening orientation and overhang shade, and explicit missing/stale sun degradation. ADR 0009 records historical assumptions and exclusions. | Focused geometry/adapter/manifest suite: 23 passed; canonical gate: 134 passed, 1,306 statements/394 branches at 96.94%. Replays remain green; consolidated correctness and Ponytail reviews found no defect or removable dependency/abstraction. No future horizon, `terraza_caliente`, option, helper, diagnostic sensor, service, or actuator was added. |
| 2026-08-25 | P01-T10 | Re-audited only the presence of deployment contract variables without printing values. `HOME_ASSISTANT_URL` and `HOME_ASSISTANT_ACCESS_TOKEN` are populated; the mounted-path variable and all SSH route variables are absent/unpopulated. Kept the task outside implementation and external state untouched. | Blocked at the frozen precondition: no authorized file-capable route to `config/custom_components`. Exactly one mounted-path, SSH-key, or approved Git/HACS route must be selected before the task returns to `pendiente`/`en curso`. |
