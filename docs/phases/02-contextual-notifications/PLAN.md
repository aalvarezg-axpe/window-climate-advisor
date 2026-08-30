# Phase 02 — Contextual recommendation notifications

- Status: active
- Drafted: 2026-08-30
- Started: 2026-08-30
- Branch: `feature/02-contextual-notifications`
- Product authority: `docs/GOAL.md`
- Activation gate: met on 2026-08-30; Phase 01 is accepted and merged into
  `develop`, and the owner directed continued development of the registered
  presence-aware notification scope

## Objective

Deliver useful recommendation summaries only to configured occupants who are
currently home, and give an arriving occupant a fresh, still-relevant summary
instead of replaying changes that happened while everybody was away.

## Frozen decisions

- This phase delivers notifications only; it never controls a window, blind,
  shutter, awning, HVAC system, or other physical actuator.
- The existing stable-change candidate is the sole ordinary delivery trigger.
  Repeated evaluations with unchanged resolved targets do not notify.
- Presence comes from configured `person` entities and native `home`
  transitions, not coordinates, device IDs, or deprecated device triggers.
- Each person maps to an explicitly selected native `notify` entity. Home
  Assistant 2026.8 exposes those targets through entity state and the fixed
  `notify.send_message` action; configuration stores neither arbitrary action
  strings nor names inferred from a person or device.
- Recipients are repeatable config subentries. Duplicate persons and duplicate
  notification targets are rejected. Existing schema-v4 entries need no data
  migration because an absent recipient subentry means delivery is disabled.
- Away-time transition messages are neither delivered nor queued. Arrival
  causes a fresh evaluation; only current, actionable advice is eligible.
- Missing/degraded recommendation data never becomes favourable advice and is
  not delivered as an actionable recommendation.

## Frozen tasks

Ponytail keeps one native person-to-notify-entity mapping, the existing grouped
candidate, and native state transitions. No queue, helper, recipient registry,
service-name parser, new entity, dependency, or persisted presence ledger is
introduced unless a frozen acceptance test proves the native boundary is
insufficient.

| ID | Task and acceptance | Status | Owner | Planned write set | Dependencies / provenance |
|---|---|---|---|---|---|
| P02-T01 | Add a typed recipient contract that maps one configured `person` entity to one explicitly selected native `notify` entity. Accept recipient-subentry creation/reconfigure selection, duplicate and missing-target validation, privacy-safe diagnostics, reload and unchanged-v4 coverage, and a production-boundary test against the registered `notify.send_message` surface. Do not infer names or accept a service string. | terminada | root manager | `const.py`, `config_flow.py`, `application/notifications.py`, `diagnostics.py`, translations, config-flow/init/diagnostics/application tests, `docs/GOAL.md`, ADR and this plan | Native recipient subentries validate entity domains, current/registered targets, duplicate people/targets, and the fixed action surface while preserving schema v4. Diagnostics expose only a count. Focused 22/22 and canonical 155/155 pass at 97.00%; consolidated correctness and Ponytail reviews found no defect or removable layer. |
| P02-T02 | Deliver at most one consolidated message per accepted grouped window/blind transition, and only to configured recipients whose `person` state is `home` at delivery time. Accept present/away/mixed-recipient tests, deterministic room/opening ordering, no delivery for unchanged or degraded results, isolated delivery failure, and zero actuator calls. | terminada | root manager retained after executor permission mismatch | `application/notifications.py`, `adapters/notifications.py`, `coordinator.py`, translations, focused application/adapter/coordinator tests, ADR and this plan | The coordinator consumes only the existing grouped candidate; one translated, deterministically ordered summary reaches each available home recipient through fixed `notify.send_message`. Away/unchanged/unavailable cases send nothing, failures are isolated/redacted, and invalid recipient data cannot degrade climate evaluation. Focused 10/10 and canonical 159/159 pass at 96.66%. |
| P02-T03 | On a configured recipient's real transition into `home`, run a fresh evaluation and send only that arriving recipient a consolidated summary that is still actionable. Accept no stale backlog replay, one delivery per away-to-home transition, restart-safe deduplication, no message when feedback proves targets already satisfied, and explicit wording for manual blinds whose applied position cannot be observed. | terminada | root manager retained after executor permission mismatch | `application/notifications.py`, `adapters/notifications.py`, `coordinator.py`, focused application/notification-adapter/coordinator/init tests, ADR and this plan | Native non-home-to-`home` edges trigger one fresh evaluation and target only the arriving configured person; startup, repeated-home and unavailable recovery do not. Observed satisfied targets are omitted, manual positions remain explicit, and the arriving person is excluded from any simultaneous ordinary candidate. Focused 20/20 and canonical 164/164 pass at 95.85%. |
| P02-T04 | Validate notification behaviour in Home Assistant before release. Accept setup/unload/reload/restart, unavailable person/notify target and send-failure recovery, present/away/mixed/arrival scenarios, Recorder-safe privacy evidence, exact notification counts, no duplicates, no owned persistent backlog, and zero physical services/actions. | en curso | root manager | integration tests, manifest/changelog/version, deployment/status/runbook docs, this plan, Git/HACS release state and Home Assistant external verification | Prepare `v0.2.0b1` as the first notification beta, retain live-verified `v0.1.0b5` as the integration fallback and `v4.17_pre` as the operational rollback. Recipient person-to-notify mappings require explicit owner selection and will not be inferred. |

## Exact local acceptance commands

Each task runs its focused suite first and then the repository canonical command:

| Task | Focused command |
|---|---|
| P02-T01 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/application/test_notifications.py tests/integration/test_config_flow.py tests/integration/test_init.py tests/integration/test_diagnostics.py -q'` |
| P02-T02 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/application/test_notifications.py tests/integration/test_notification_delivery.py tests/integration/test_coordinator.py -q'` |
| P02-T03 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/unit/application/test_notifications.py tests/integration/test_notification_delivery.py tests/integration/test_coordinator.py tests/integration/test_init.py -q'` |
| P02-T04 | `wsl --cd "$PWD" -- bash -lc 'UV_PROJECT_ENVIRONMENT="$HOME/.cache/window-climate-advisor/venv" "$HOME/.local/bin/uv" run --frozen python -m pytest --no-cov tests/integration -q'` |

```powershell
uv run --frozen python scripts/verify.py
```

## Stop conditions

- Stop if delivery would require coordinates, an inferred action name, a raw
  unvalidated service string, or a deprecated device trigger.
- Stop if an arrival path would replay historical messages instead of evaluating
  the current recommendation.
- Stop if notification failure can alter optimizer, safety, availability, or
  actuator state.
- Stop for owner review before adding a recipient abstraction, queue, helper,
  entity, dependency, or platform not required by the frozen consumers.

## Phase acceptance

Phase 02 may close only when all P02 tasks are terminated with evidence, the
canonical gate and Ponytail gates pass, a reversible Home Assistant deployment
proves the configured presence/delivery matrix, and no physical action or stale
away-time notification occurs.

## Modification log

| Date | Task | Files/change | Verification |
|---|---|---|---|
| 2026-08-30 | P02-T01–P02-T04 | Reserved the owner-requested next-version presence-aware delivery contract as an inactive draft. Split recipient configuration, ordinary stable-change delivery, fresh arrival advice, and deployed verification into bounded tasks. | Contract review confirms native `person` presence, explicit validated notification actions, no name inference, no away-time queue, no physical action, and no Phase 01 implementation change. |
| 2026-08-30 | P02-T01 | Activated the phase after Phase 01 acceptance/merge and froze the minimum implementation around recipient subentries, native person state, native notify entities, the fixed `notify.send_message` action, the existing grouped candidate, and arrival edges without a queue or presence ledger. Updated the living product contract and exact task write sets/commands. | Read-only local Core 2026.8 source and live capability checks confirm the native notify entity/action boundary with available person and notify targets. Existing schema-v4 entries remain valid with zero recipients; no Home Assistant state changed and no private identifier or raw state was recorded. |
| 2026-08-30 | P02-T01 | Added the pure typed recipient mapping, native repeatable recipient subentry flow, explicit entity/action existence checks, duplicate rejection, unchanged-v4 lifecycle coverage, translations, count-only diagnostics, and ADR 0010. No delivery call, service string, queue, helper, entity, dependency, migration, or physical action was added. | Focused gate: 22 passed. Canonical gate: 155 passed at 97.00% with Ruff, format, strict mypy, artifact/secret, migration, reload, translation, privacy, and diff checks green. Ponytail review: `Lean already. Ship.` |
| 2026-08-30 | P02-T02 | Started the authorized `luna_executor` wave at clean commit `1bc6097`, with an isolated write set and external/docs/Git prohibitions. The executor verified the expected Luna/max identity but received live `danger-full-access` instead of its global `workspace-write` profile and stopped before editing; root retained the task rather than accepting a silent permission mismatch. | No executor artifact or repository change exists. This is a tooling/profile exception, not a product blocker; the root continues the same frozen minimum under its existing session permissions. |
| 2026-08-30 | P02-T02 | Root added the native notification adapter and one coordinator hook. It filters presence and target availability at delivery time, reuses existing entity translations, sorts one grouped room/opening summary, calls only fixed `notify.send_message`, and isolates each `HomeAssistantError`. The consolidated review excluded recipient-only corruption from the climate duplicate-link gate and removed an unnecessary log index. | Focused gate: 10 passed. Canonical gate: 159 passed at 96.66% with Ruff, format, strict mypy, artifact/secret, replay, translation, failure-isolation, and zero-physical-call checks green. The first focused attempt failed before collection because unit and integration modules shared `test_notifications.py`; the living plan and integration filename were corrected, then both gates passed. Final Ponytail review: `Lean already. Ship.` |
| 2026-08-30 | P02-T03 | Started the arrival-context slice after accepting P02-T02. Root retained the isolated implementation because the prior executor launch did not receive its required workspace-only permission profile. | Frozen minimum: only a native non-home-to-`home` edge, one fresh evaluation, only the arriving configured recipient, no startup/restoration delivery, no queue, and no actuator call. |
| 2026-08-30 | P02-T03 | Added transient arrival-edge capture, fresh actionable-advice construction, targeted native delivery, simultaneous ordinary-message exclusion, feedback-based suppression, and explicit manual-blind wording. Kept the implementation lazy outside arrival events and removed redundant validation from its internal transfer value during the Ponytail review. | Focused gate: 20 passed. Canonical gate: 164 passed at 95.85% with Ruff, format, strict mypy, artifact/secret, replay, restart/recovery, privacy, and zero-physical-call checks green. The first event test incorrectly waited on Home Assistant's debouncer and left a timer; it was corrected to isolate the native edge and invoke the fresh evaluation explicitly. Final Ponytail review: `Lean already. Ship.` |
| 2026-08-30 | P02-T04 | Started the release/deployment gate after accepting all local notification slices. Froze `v0.2.0b1`, the reversible fallbacks, and the boundary that recipient mappings must be selected explicitly rather than inferred from private names or devices. | No Home Assistant or Git release state changed at task start. Local setup/reload/restart, delivery-matrix, privacy, failure-isolation, count, no-backlog, and zero-actuator evidence will be consolidated before deployment. |
| 2026-08-30 | P02-T04 | Prepared the numbered notification beta locally: bumped the manifest/test contract, separated release notes, updated the HACS installation/rollback runbook and README, and created the redacted Phase 02 status record. The existing entry schema remains v4 and `v0.1.0b5` remains the integration fallback. | Integration gate: 50 passed. Canonical gate: 164 passed at 95.85% with Ruff, format, strict mypy, artifact/secret, lifecycle, delivery matrix, replay, privacy, and zero-actuator checks green. No Home Assistant, tag, release, or recipient mapping changed during this step. |
