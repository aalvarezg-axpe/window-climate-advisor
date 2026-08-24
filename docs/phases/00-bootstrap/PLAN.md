# Phase 00 — Repository and development bootstrap

- Status: active
- Started: 2026-08-24
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
| P00-T02 | Discover the deployed Home Assistant version, provision its supported Python through `uv`, select one cross-platform canonical command runner, and create dependency metadata, lock, and complete quality targets. Accept exact version evidence, frozen sync, and all empty-repository tooling gates. | terminada | root manager | toolchain/root config | API target 2026.8.2; CPython 3.14.2; locked 158-package graph; frozen sync and canonical artifact/Ruff/mypy gate passed. Pytest is explicitly deferred until P00-T03 creates tests. |
| P00-T03 | Freeze the minimal v1 config-entry, subentry, entity, and config-flow contract, then scaffold only the installable integration and test artifacts consumed by that contract, without business logic. Accept manifest/config-flow loading, setup/unload/reload, translations, strict typing, and artifact inventory. | pendiente | delegated wave + root review | declared integration/test paths and root-owned contract review | Depends on P00-T02 and the P00-T05 inventory. |
| P00-T04 | Select and implement one safe deployment route to Home Assistant `config/custom_components`, with backup, exact target validation, config check, restart/reload policy, and rollback. | bloqueada | root manager | operations/deployment/env contract | API URL/token exist, but no file-deployment route has been selected. |
| P00-T05 | Inventory the v4.17_pre automation, tests, simulations, models, and accepted deployed evidence without modifying or copying them. Accept source hashes, provenance, behavioural scenario mapping, and an explicit fixture-import manifest. | terminada | delegated wave + root review | migration docs only; predecessor read-only | Luna produced the inventory; root recomputed 20 SHA-256 values with zero missing/mismatched paths, confirmed no private-pattern hits, and accepted the P00-T09 manifest. |
| P00-T06 | Freeze the Phase 01 coupled-optimizer and shadow-parity plan. Accept the imported v4.18_pre dispositions, minimized task graph, exact write sets and commands, gates, stop conditions, and absence of physical-action scope. | pendiente | root manager | `docs/phases/01-domain-optimizer/PLAN.md` | Draft created by P00-T08; freeze after P00-T03/P00-T09. |
| P00-T07 | Correct the bootstrap location to the local workstation, restore the global `luna_executor` profile and Ponytail skills, require the Sol/xhigh root manager, and remove the accidental remote checkout after verified transfer. Accept with matching file manifests, skill/profile hashes, local config validation, repository gates, ignored-secret verification, and confirmed remote removal. | terminada | root manager | local repository docs; local Codex config/profiles/skills; accidental remote checkout | Local copy verified; Sol/xhigh and Luna/max TOML valid; Ponytail trio and Luna hashes match the remote sources; `.env` ignored and unchanged; tracked-secret/diff checks passed; accidental remote repository removed. |
| P00-T08 | Make `AGENTS.md`, `docs/GOAL.md`, and phase plans explicit living references; reconcile the Phase 00 task graph; review and import every planned v4.18_pre requirement with recorded disposition. Accept with source-to-target traceability, document consistency checks, `git diff --check`, and ignored-secret verification. | terminada | root manager | canonical governance/product/phase documents only | All nine predecessor F04 tasks map to ten unique P01 tasks; live-reference rules and bootstrap corrections recorded; document, diff, and ignored-secret checks passed. |
| P00-T09 | Import the P00-T05 manifest as versioned executable fixtures and characterization tests after the minimal scaffold exists. Accept copied-file hashes where applicable, fixture provenance, mapping to v4.17 tests/scenarios, canonical verification, and no modification of predecessor artifacts. | pendiente | delegated wave + root review | fixtures, characterization tests, migration docs | Depends on P00-T02/P00-T03/P00-T05. |

## Phase acceptance

Phase 00 is complete only when:

- P00-T01–P00-T09 are terminated with recorded evidence;
- the complete canonical verification gate is green;
- `.env` is ignored and no secret appears in tracked content or Git history;
- global agent roles and Ponytail skills have been verified from the active
  local installation;
- integration scaffolding loads through Home Assistant test fixtures;
- a reversible deployed-test route has been selected and documented;
- predecessor v4.17 files remain unchanged and available as rollback evidence;
- Phase 01 is frozen without physical-action scope.

P00-T02 and P00-T05 may proceed independently; P00-T03, P00-T09, and P00-T06
then follow in that order. P00-T04 may be resolved independently but remains
required for phase closure.

## Modification log

| Date | Task | Files/change | Verification |
|---|---|---|---|
| 2026-08-24 | P00-T01 | Created the initial governance, product goal, ADRs, development runbook, environment contract, bootstrap plan, and copied the predecessor `.env` without deleting the source. | Local document/diff checks passed; `.env` ignored; source/destination SHA-256 match. |
| 2026-08-24 | P00-T07 | Moved the canonical development repository to the local workstation, restored global Luna and Ponytail assets, enabled local agent defaults/project trust, corrected all location/role documentation, and removed the accidental remote checkout. | Initial remote-to-local manifest matched; four restored asset hashes matched; `config.toml` and Luna TOML parsed with Sol/xhigh and Luna/max; local document/diff/secret/env checks passed; remote path no longer exists. |
| 2026-08-24 | P00-T08 | Declared canonical references live, corrected task statuses/dependencies and fixture sequencing, and created the draft Phase 01 optimizer/shadow plan with explicit v4.18_pre dispositions. | F04 source/mapping counts 9/9; ten unique P01 tasks; Markdown table check passed; `git diff --check` passed; `.env` remains ignored, untracked, and absent from history. |
| 2026-08-24 | P00-T02 | Detected Home Assistant 2026.8.2 through its authenticated API; updated local `uv`, pinned/provisioned Python 3.14.2, added `pyproject.toml`, `uv.lock`, and the cross-platform verification runner, and updated development guidance/ADR. | `uv lock --check`: 158 packages; `uv sync --frozen --group dev`: 152 installed; Python 3.14.2, HA 2026.8.2, test plugin 0.13.356; `uv run --frozen python scripts/verify.py`: artifact/secret, Ruff and strict mypy checks passed, pytest explicitly skipped until P00-T03. |
| 2026-08-24 | P00-T05 | Delegated one isolated Luna/max wave to create `docs/migration/v4_17_inventory.md`; root reviewed its complete diff, provenance, scenario matrix, deployment sanitization, and minimal P00-T09 import manifest. | Recomputed 20 source SHA-256 hashes: zero missing/mismatched; zero private-pattern hits; `git diff --check` passed; predecessor was read-only and no fixtures were copied. |
