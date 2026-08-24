# Phase 00 — Repository and development bootstrap

- Status: complete
- Started: 2026-08-24
- Completed: 2026-08-24
- Branch target: `feature/00-bootstrap`
- Product authority: `docs/GOAL.md`

## Objective

Create a reproducible, secret-safe, locally developed repository with explicit
architecture, manager-executor rules, compatible Python tooling, canonical
verification, and a frozen migration contract before implementing the Home
Assistant integration.

## Frozen decisions

- Repository: `C:\Users\aalvarezg\Documents\Home Assistant\window-climate-advisor`.
- Integration domain: `window_climate_advisor`.
- Architecture: one modular custom integration with a pure domain core.
- Configuration: Home Assistant UI config flow, reconfigure/options flows, and
  room/opening subentries.
- Execution roles: global manager `gpt-5.6-sol/xhigh` and global persistent
  `luna_executor` `gpt-5.6-luna/max`; no repository-local profile copies. The
  global Ponytail trio supplies the complexity gates.
- Package/dependency management: `uv`, with a Python version compatible with
  the target Home Assistant release.
- Safety: recommendation and shadow mode only; no actuator path.
- Rollback: deployed v4.17_pre automation remains intact.

## Tasks

| ID | Task and acceptance | Status | Owner | Write set | Evidence |
|---|---|---|---|---|---|
| P00-T01 | Create the local Git repository, governance/product/ADR/runbook documents, ignored `.env` contract, and transfer the existing `.env` without exposing values. Accept with document checks, `git diff --check`, ignored-secret verification, and matching source/destination hash. | terminada | root manager | root docs/config only; no product code | Local repository initialized on `main`; document and diff checks passed; `.env` is ignored and its source/destination SHA-256 match. |
| P00-T02 | Discover the deployed Home Assistant version, provision its supported Python through `uv`, select one cross-platform canonical command runner, and create dependency metadata, lock, and complete quality targets. Accept exact version evidence, frozen sync, and all empty-repository tooling gates. | terminada | root manager | toolchain/root config | API target 2026.8.2; CPython 3.14.2; locked 158-package graph; frozen sync passed. The canonical Windows command runs static gates locally and HA pytest in local WSL 2 because Core requires POSIX `fcntl`; the complete gate passes. |
| P00-T03 | Freeze the minimal v1 config-entry, subentry, entity, and config-flow contract, then scaffold only the installable integration and test artifacts consumed by that contract, without business logic. Accept manifest/config-flow loading, setup/unload/reload, translations, strict typing, and artifact inventory. | terminada | delegated wave + root review | declared integration/test paths and root-owned contract review | ADR 0003 freezes one dwelling entry plus room/opening subentries and the future informational entity surface. Minimal manifest, flows, lifecycle, and complete `en`/`es` translations pass 11 HA tests with 100% branch coverage, Ruff, format, strict mypy, diff, artifact, and secret checks. |
| P00-T04 | Audit safe routes to Home Assistant `config/custom_components` and freeze the authorization/rollback gate. If no file route exists, assign its resolution to the first deployment task instead of blocking local-only phases. Accept sanitized channel evidence, mutually exclusive environment contracts, and no external mutation. | terminada | root manager | operations/deployment/env contract | API reaches HA 2026.8.2, but no route variable or file-capable channel exists. The supported mounted-path, SSH/SFTP, and approved Git/HACS contracts are documented; P01-T10 cannot enter `en curso` until one route and its exact rollback commands are frozen. |
| P00-T05 | Inventory the v4.17_pre automation, tests, simulations, models, and accepted deployed evidence without modifying or copying them. Accept source hashes, provenance, behavioural scenario mapping, and an explicit fixture-import manifest. | terminada | delegated wave + root review | migration docs only; predecessor read-only | Luna produced the inventory; root recomputed 20 SHA-256 values with zero missing/mismatched paths, confirmed no private-pattern hits, and accepted the P00-T09 manifest. |
| P00-T06 | Freeze the Phase 01 coupled-optimizer and shadow-parity plan. Accept the imported v4.18_pre dispositions, minimized task graph, exact write sets and commands, gates, stop conditions, and absence of physical-action scope. | terminada | root manager | `docs/phases/01-domain-optimizer/PLAN.md` plus live-reference corrections | All nine F04 requirements map to ten frozen P01 tasks with exact writes, local commands, waves, gates, and stop conditions. Deterministic enumeration remains dependency-free; actual deployment routing is a hard pre-start gate on root-only P01-T10, not a blocker for local domain work. |
| P00-T07 | Correct the bootstrap location to the local workstation, restore the global `luna_executor` profile and Ponytail skills, require the Sol/xhigh root manager, and remove the accidental remote checkout after verified transfer. Accept with matching file manifests, skill/profile hashes, local config validation, repository gates, ignored-secret verification, and confirmed remote removal. | terminada | root manager | local repository docs; local Codex config/profiles/skills; accidental remote checkout | Local copy verified; Sol/xhigh and Luna/max TOML valid; Ponytail trio and Luna hashes match the remote sources; `.env` ignored and unchanged; tracked-secret/diff checks passed; accidental remote repository removed. |
| P00-T08 | Make `AGENTS.md`, `docs/GOAL.md`, and phase plans explicit living references; reconcile the Phase 00 task graph; review and import every planned v4.18_pre requirement with recorded disposition. Accept with source-to-target traceability, document consistency checks, `git diff --check`, and ignored-secret verification. | terminada | root manager | canonical governance/product/phase documents only | All nine predecessor F04 tasks map to ten unique P01 tasks; live-reference rules and bootstrap corrections recorded; document, diff, and ignored-secret checks passed. |
| P00-T09 | Import the P00-T05 manifest as versioned executable fixtures and characterization tests after the minimal scaffold exists. Accept copied-file hashes where applicable, fixture provenance, mapping to v4.17 tests/scenarios, canonical verification, and no modification of predecessor artifacts. | terminada | delegated wave + root review | fixtures, characterization tests, migration docs | Exact v4.17_pre/v4.16_pre copies match A01/A02 SHA-256. Seven structural characterization cases cover hashes, YAML/Jinja, independent aliases, and no `cover.*` service action; the complete gate passes 18 tests at 100% branch coverage. P01-T01 inventories behavioural cases and P01-T02–P01-T07 test them with real consumers. |
| P00-T10 | Resolve the phase-closing Ponytail audit without changing behaviour. Accept removal of package markers pytest does not consume, simplification of the single-purpose action-key walker, the focused characterization test, and the canonical gate. | terminada | root manager | `tests/__init__.py`, `tests/integration/__init__.py`, `tests/characterization/test_migration_fixtures.py`, this plan | Removed two unused package markers and one single-caller generic parameter. Focused characterization remains 7/7; the canonical gate remains 18/18 at 100% branch coverage. |

## Phase acceptance

Phase 00 is complete only when:

- P00-T01–P00-T10 are terminated with recorded evidence;
- the complete canonical verification gate is green;
- `.env` is ignored and no secret appears in tracked content or Git history;
- global agent roles and Ponytail skills have been verified from the active
  local installation;
- integration scaffolding loads through Home Assistant test fixtures;
- the deployment-route audit, supported contracts, and hard P01-T10
  authorization/rollback stop condition are documented;
- predecessor v4.17 files remain unchanged and available as rollback evidence;
- Phase 01 is frozen without physical-action scope.

P00-T02 and P00-T05 may proceed independently; P00-T03, P00-T09, and P00-T06
then follow in that order. Actual deployment-route resolution is intentionally
deferred to P01-T10 because it is not a dependency of local domain work.

## Modification log

| Date | Task | Files/change | Verification |
|---|---|---|---|
| 2026-08-24 | P00-T01 | Created the initial governance, product goal, ADRs, development runbook, environment contract, bootstrap plan, and copied the predecessor `.env` without deleting the source. | Local document/diff checks passed; `.env` ignored; source/destination SHA-256 match. |
| 2026-08-24 | P00-T07 | Moved the canonical development repository to the local workstation, restored global Luna and Ponytail assets, enabled local agent defaults/project trust, corrected all location/role documentation, and removed the accidental remote checkout. | Initial remote-to-local manifest matched; four restored asset hashes matched; `config.toml` and Luna TOML parsed with Sol/xhigh and Luna/max; local document/diff/secret/env checks passed; remote path no longer exists. |
| 2026-08-24 | P00-T08 | Declared canonical references live, corrected task statuses/dependencies and fixture sequencing, and created the draft Phase 01 optimizer/shadow plan with explicit v4.18_pre dispositions. | F04 source/mapping counts 9/9; ten unique P01 tasks; Markdown table check passed; `git diff --check` passed; `.env` remains ignored, untracked, and absent from history. |
| 2026-08-24 | P00-T02 | Detected Home Assistant 2026.8.2 through its authenticated API; updated local `uv`, pinned/provisioned Python 3.14.2, added `pyproject.toml`, `uv.lock`, and the cross-platform verification runner, and updated development guidance/ADR. | `uv lock --check`: 158 packages; `uv sync --frozen --group dev`: 152 installed; Python 3.14.2, HA 2026.8.2, test plugin 0.13.356; `uv run --frozen python scripts/verify.py`: artifact/secret, Ruff and strict mypy checks passed, pytest explicitly skipped until P00-T03. |
| 2026-08-24 | P00-T05 | Delegated one isolated Luna/max wave to create `docs/migration/v4_17_inventory.md`; root reviewed its complete diff, provenance, scenario matrix, deployment sanitization, and minimal P00-T09 import manifest. | Recomputed 20 source SHA-256 hashes: zero missing/mismatched; zero private-pattern hits; `git diff --check` passed; predecessor was read-only and no fixtures were copied. |
| 2026-08-24 | P00-T04 | Re-audited available deployment channels without mutation or disclosure of private endpoints. | Zero populated route variables; HA host ports 22/445 closed; no match with the known Codex SSH host or local SSH configuration. REST access alone cannot install custom-component files, so the task remains blocked pending an owner-selected route. |
| 2026-08-24 | P00-T02 | Corrected the canonical runner after the first real Home Assistant pytest invocation exposed Core's native-Windows `fcntl` incompatibility; provisioned the same locked Python environment in local WSL 2 and documented the route. | `uv run --frozen python scripts/verify.py`: Windows artifact/secret, Ruff, format, and strict mypy gates passed; WSL Python 3.14.2 collected and passed 11 HA tests. |
| 2026-08-24 | P00-T03 | Froze ADR 0003 and accepted the behaviour-free custom integration scaffold. The delegated executor produced an initial partial diff but did not provide a bounded handoff; root retained the correction pass because further delegation cost exceeded the task. Ponytail review removed an unused `sun` dependency, Core-only `strings.json`, redundant validation, and speculative entrypoints/platforms. | Full artifact inventory contains only the manifest, constants, flow, lifecycle, two translations, and consumed tests; `uv run --frozen python scripts/verify.py` passed 11 tests with 100% branch coverage. |
| 2026-08-24 | P00-T09 | Luna imported exact A01/A02 fixtures and one structural characterization module; root reviewed all copied artifacts, minimized the deferred behavioural mapping to the actual P01 consumers, and kept the predecessor read-only. | Source/destination SHA-256 pairs match; focused characterization passed 7 tests; `uv run --frozen python scripts/verify.py` passed 18 tests with 100% branch coverage plus artifact/secret, Ruff, format, mypy, and diff gates. |
| 2026-08-24 | P00-T04/P00-T06 | Corrected an inefficient phase dependency: lack of a deployment file channel must block P01-T10, not local domain development. Preserved the exact authorization, backup, validation, rollback, and deployed-verification gates while freezing Phase 01. | Existing route audit remains valid; three mutually exclusive route contracts are documented; P01-T10 has an explicit pre-start stop condition and no external mutation occurred. |
| 2026-08-24 | P00-T10 | Ran the phase-closing Ponytail audit and applied its two accepted simplifications through a traced root task. Closed Phase 00 after reviewing the complete tree and all acceptance evidence. | Focused characterization: 7 passed; canonical gate: 18 passed, 100% branch coverage; Ruff, format, strict mypy, artifact/secret, and diff checks passed. |
