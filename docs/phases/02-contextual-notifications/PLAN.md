# Phase 02 — Contextual recommendation notifications

- Status: draft / not active
- Drafted: 2026-08-30
- Planned branch: `feature/02-contextual-notifications`
- Product authority: `docs/GOAL.md`
- Activation gate: Phase 01 is accepted and merged into `develop`; the owner
  explicitly activates notification delivery

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
- Each person maps to an explicitly selected notification action that is
  validated against Home Assistant at setup and runtime. Action names are not
  inferred from person/device names and are not hard-coded in source.
- Away-time transition messages are neither delivered nor queued. Arrival
  causes a fresh evaluation; only current, actionable advice is eligible.
- Missing/degraded recommendation data never becomes favourable advice and is
  not delivered as an actionable recommendation.

## Draft tasks

Task IDs and intent are reserved by this draft. Status remains `futura` until
the activation gate is met and the root freezes exact implementation write sets.

| ID | Task and acceptance | Status | Owner | Planned write set | Dependencies / provenance |
|---|---|---|---|---|---|
| P02-T01 | Add a typed recipient contract that maps one configured `person` entity to one explicitly selected Home Assistant notification action. Accept config/options-flow selection, duplicate and missing-target validation, privacy-safe diagnostics, reload/migration coverage, and a production-boundary test against the registered action surface. Do not infer names or accept an unvalidated arbitrary service string. | futura | root manager | config/options flow, coordinator recipient model, translations, diagnostics, tests, ADR/GOAL/plan | Requires Phase 01 closure and a short implementation-time check of the supported Home Assistant notification action discovery surface. Mobile-app actions are expected consumers, not a hard-coded dependency. |
| P02-T02 | Deliver at most one consolidated message per accepted grouped window/blind transition, and only to configured recipients whose `person` state is `home` at delivery time. Accept present/away/mixed-recipient tests, deterministic room/opening ordering, no delivery for unchanged or degraded results, isolated delivery failure, and zero actuator calls. | futura | root manager; delivery implementation may be delegated after contract freeze | notification application policy, thin Home Assistant delivery adapter, coordinator hook, translations, focused tests | Reuses the P01-T17 resolved-target contract and the existing restart-safe stable-change candidate; it adds no second change-state entity or notification queue. |
| P02-T03 | On a configured recipient's real transition into `home`, run a fresh evaluation and send only that arriving recipient a consolidated summary that is still actionable. Accept no stale backlog replay, one delivery per away-to-home transition, restart-safe deduplication, no message when feedback proves targets already satisfied, and explicit wording for manual blinds whose applied position cannot be observed. | futura | root manager; delivery implementation may be delegated after contract freeze | presence subscriptions, arrival policy/state, coordinator scheduling, focused tests | Uses native person state/zone semantics. Arrival is a separate context trigger, not a fabricated recommendation transition. |
| P02-T04 | Validate notification behaviour in Home Assistant before release. Accept setup/unload/reload/restart, unavailable person/action and send-failure recovery, present/away/mixed/arrival scenarios, Recorder-safe privacy evidence, exact notification counts, no duplicates, no owned persistent backlog, and zero physical services/actions. | futura | root manager | integration tests, deployment/status/runbook docs, Home Assistant external verification, release metadata only after local gates pass | Deployment remains reversible and follows Git/HACS. Failure of notification delivery must not affect recommendation availability or safety evaluation. |

## Planned acceptance

Each task runs a focused suite first and then the repository canonical command:

```powershell
uv run --frozen python scripts/verify.py
```

Exact focused commands and write sets are frozen only when the phase activates;
the draft must not invent test modules or implementation structure prematurely.

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
