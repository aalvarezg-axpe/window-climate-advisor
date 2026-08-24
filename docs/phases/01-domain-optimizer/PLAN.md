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
| P01-T04 | Implement a deterministic per-opening optimizer that jointly enumerates `closed/tilt/open` and blind opening `0–100%` against the seasonal objective. Accept current/forecast horizons, uncertainty, movement penalty, stable tie-breaking, and exhaustive tests without a solver dependency. | terminada | root manager | `domain/optimizer.py`, minimal additions to `domain/models.py`, `tests/unit/domain/test_optimizer.py`, optimizer ADR | ADR 0006 and the pure optimizer exhaust 22/33 candidates, use worst current/forecast seasonal cost, explicit caller penalties, and deterministic current-first ties. Focused 7/7 and canonical 51/51 pass at 100% branch coverage without a solver/dependency. |
| P01-T05 | Prove that `terraza_caliente` is absent as an independent decision input. This is a negative migration gate, not a new module: measured radiation, weather safety, and real geometry remain. | terminada | root manager | behaviour matrix and existing optimizer tests only; no new production file | C011 is explicitly `replace`; characterization scans all production Python and the plan's `rg` returns no match. Focused 13/13 and canonical gates pass without creating a production artifact. |
| P01-T06 | Derive recommendation and reason outputs from optimizer results, with absolute rain/wind priority and explicit degraded input states. Accept recommendation-only outputs and no unexplained v4.17 change. | terminada | root manager | `domain/policy.py`, `tests/unit/domain/test_policy.py`, behaviour-matrix dispositions, safety ADR | ADR 0007 and the pure policy preserve rain/gust precedence, continuous wind limits, protected tilt geometry, optimizer blind output, and fail closed on missing/stale safety observations. Focused 15/15 and canonical 67/67 pass with 481 statements/140 branches at 100%; no HA import, action, or notification surface. |
| P01-T07 | Add cost/benefit hysteresis and stable transitions. Accept no churn from small changes, the 15-minute blind policy, at most one grouped notification candidate, and notification delivery absent in shadow mode. | terminada | root manager while the persistent executor remains suspended | `domain/state_machine.py`, `application/__init__.py`, `application/state.py`, minimal optimizer result/test additions, state-machine/application tests, behaviour-matrix dispositions | Pure transitions use optimizer avoided cost and caller-supplied minimum/deadband; retain 5/0-minute degradation, 10-minute improvement, and 15-minute blind direction confirmation. Versioned UTC state survives missing evaluations/restart and yields zero or one value-only grouped candidate. Focused 24/24 and canonical 91/91 pass with 680 statements/210 branches at 100%; no delivery surface. |
| P01-T08 | Run representative multi-day Summer, Shoulder-season, and Winter replays. Include exterior at 25 °C in Summer, nocturnal pre-cooling, Winter solar gain above 24 °C, no wind, partial solar exposure, and adverse forecast. Accept v4.17 comparison for comfort, net energy, stability, safety, recommendation/notification counts, and sensitivity of assumed parameters. | pendiente | root manager while the persistent executor remains suspended | `tests/fixtures/replay/`, `tests/replay/`, `docs/status/phase01-replay.md` | P01-T07; all six explicit scenarios and comparison requirements from predecessor F04-08. |
| P01-T09 | Connect the accepted engine to Home Assistant in advisor/shadow mode instead of creating v4.18 YAML. Accept lifecycle, schema migration, stable identities, availability/degradation, redacted diagnostics, and no service/notification action. | pendiente | root contracts + delegated implementation | `application/evaluator.py`, `adapters/`, `sensor.py`, `binary_sensor.py`, `diagnostics.py`, `__init__.py`, manifest/config-flow/schema changes, translations, integration tests and ADR updates | P01-T08; local successor to predecessor F04-09. |
| P01-T10 | Deploy reversibly beside operational v4.17_pre and run the owner-agreed shadow period. Accept exact route/target, backup, rollback, configuration validation, one entry, expected entities without duplicates, clean reload/restart, no owned notifications/actions, and an approved comparison report. | pendiente | root manager | `.env.example` route names if needed, `docs/operations/deployment.md`, `docs/status/phase01-shadow.md`, Home Assistant external state | P00-T04 route audit/P01-T09; operational remainder of predecessor F04-09. |

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
5. P01-T10 is root-only external work. No executor receives Home Assistant or
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
| P01-T10 | `uv run --frozen python scripts/verify.py`; the route-specific backup/copy/config-check/reload/rollback commands must be resolved and recorded before this task enters `en curso`. |

Canonical gate after P01-T01–P01-T09 and before/after P01-T10:

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
| 2026-08-24 | P00-T06 | Froze all imported tasks, exact write sets, sequential executor waves, local focused/canonical commands, route-dependent deployment gate, and stop conditions. Ponytail kept deterministic enumeration, made `terraza_caliente` a negative gate rather than a module, and deferred each legacy assertion to its real consumer. | Nine F04 tasks remain mapped to ten P01 tasks; no actuator/notification delivery scope; Markdown/diff/canonical repository gates pass. |
| 2026-08-24 | P01-T01 | Created a readable matrix and schema-v1 JSON catalog with 27 sourced legacy boundaries. The persistent executor spent the bounded wave reading without producing a handoff, so root retained implementation when further delegation cost exceeded the documentation task. | Focused catalog suite: 5 passed; S02–S14 and `P/G/I/V/F/H` complete; all A01/A03–A10 sources represented; canonical gate passed with 23 tests and 100% owned-code branch coverage. |
| 2026-08-24 | P01-T02 | Froze ADR 0004 and implemented the dependency-free coupled geometry, airflow, and thermal load model. The same persistent executor again produced no status or artifact after two checkpoints and a direct request; root interrupted it, retained the wave, and added the observed-progress rule to `AGENTS.md`. | Focused domain suite: 11 passed; canonical gate: 34 passed, 214 statements/50 branches at 100%; Ruff, format, strict mypy, artifact/secret, and diff checks passed. |
| 2026-08-24 | P01-T03 | Froze ADR 0005 and added typed seasonal profiles, strict automatic/manual selection, cross-field validation, translated UI options, persistence, and reload. Root retained the task under the new observed-progress rule; no new executor attempt was made. | Focused profile/config-flow suite: 18 passed; canonical gate: 44 passed, 324 statements/88 branches at 100%; translations remain structurally complete and no helper entity was added. |
| 2026-08-24 | P01-T04 | Froze ADR 0006 and implemented exhaustive recommendation scoring over current/forecast loads, profile intent, movement, uncertainty, and stable tie-breaking. No solver, dependency, I/O, safety shortcut, or action path was added. | Focused optimizer suite: 7 passed; canonical gate: 51 passed, 374 statements/102 branches at 100%; Ruff, format, strict mypy, artifact/secret, and diff checks passed. |
| 2026-08-24 | P01-T05 | Closed the `terraza_caliente` requirement as a negative migration gate. Added one catalog/production assertion and deliberately created no module, flag, or replacement heuristic. | Focused catalog/optimizer suite: 13 passed; exact production `rg` returned no match; canonical gate passed with full owned-code branch coverage. |
| 2026-08-24 | P01-T06 | Froze ADR 0007 and added typed weather-safety recommendations around optimizer output. Reviewed all predecessor F04-01–F04-09 rows: all remain mapped; made the six F04-08 scenarios explicit, corrected active product status and suspended-executor ownership in the living references, and updated implemented matrix dispositions. | Focused policy suite: 15 passed; canonical gate: 67 passed, 481 statements/140 branches at 100%; Ruff, format, strict mypy, artifact/secret, diff, safety-boundary, and Ponytail reviews passed. |
| 2026-08-24 | P01-T07 | Added pure cost/time stability, optimizer avoided-cost evidence, 5/0/10/15-minute inherited transitions, blind-direction deduplication, versioned UTC state, and one value-only grouped candidate. No helper, recipient, service, callback, queue, or notification delivery was added. | Focused state suite: 24 passed including 30 days × 48 percentage samples; canonical gate: 91 passed, 680 statements/210 branches at 100%; Ruff, format, strict mypy, artifact/secret, diff, and Ponytail reviews passed. |
