# Repository instructions

## Authority and required reading

The root manager reads this file, `docs/GOAL.md`, and the active phase `PLAN.md`
in full before planning or editing. A persistent executor reads the same chain
once at the beginning of a work wave and reuses it until one of those sources
changes or its session is replaced.

`docs/GOAL.md` owns product scope, architecture invariants, safety gates,
GitFlow, and phase completion criteria. The active phase plan owns task status,
write sets, acceptance commands, evidence, and deviations. If they conflict,
`docs/GOAL.md` prevails.

`AGENTS.md`, `docs/GOAL.md`, and every phase `PLAN.md` are living operational
references, not write-once bootstrap artifacts. When work exposes an
inefficiency, contradiction, stale assumption, or missing accepted
requirement, the root manager updates the affected references in the same
task and records the correction in the active phase log. Executors report the
needed correction and wait for the root when a protected document is outside
their write set. Documentation maintenance must not silently broaden product
scope or weaken safety, privacy, rollback, or acceptance gates.

## Architecture invariants

- Build a modular Python monolith distributed as the Home Assistant custom
  integration `window_climate_advisor`.
- Keep thermal, solar, geometry, ventilation, hysteresis, and recommendation
  logic independent of Home Assistant. Domain modules must not import
  `homeassistant`, perform I/O, call services, or read entity state.
- Keep Home Assistant entrypoints thin. They translate config entries, entity
  states, forecasts, and lifecycle events into typed application/domain data.
- Provider payloads and Home Assistant state objects do not cross adapter
  boundaries. Missing, unknown, unavailable, malformed, or stale observations
  remain explicit and are never treated as safe or favourable conditions.
- Store operational timestamps as timezone-aware UTC values. Convert to the
  Home Assistant display timezone only at presentation boundaries.
- Configure the integration through config flows, reconfigure/options flows,
  and typed selectors. Do not require users to edit YAML.
- Persist configuration through config entries/subentries and runtime state
  through supported Home Assistant APIs. Never edit `.storage` directly.
- Expose recommendations and diagnostics through native entities. Do not
  control windows, blinds, shutters, awnings, HVAC, or any physical actuator
  until `docs/GOAL.md` contains a separately approved safety phase.
- Notification delivery uses configured `person` entities and resolves their
  associated Mobile App trackers to sibling `notify` entities through Home
  Assistant's entity/device registries. Deliver only to linked trackers that
  are currently `home`. Never derive an action name from a person, device, or
  entity name; never replay a stale away-time queue when somebody arrives.
- Preserve `v4.17_pre` as an immutable behavioural fixture. It is no longer
  deployed after the accepted migration; the last live-verified integration
  `v0.1.0b5` is the operational rollback for notification betas.

## Planning and traceability

- Phase tasks use immutable identifiers `PNN-TXX`; `NN` is the phase and `XX`
  is the sequence inside it.
- Every change belongs to an actionable, verifiable row in the active phase
  plan and is marked `en curso` before implementation.
- Mark a task `terminada` only after its exact acceptance commands pass. Record
  command, result, files, assumptions, and deviations in the phase log.
- Record out-of-scope work as `bloqueada`, `pendiente`, or `futura`; do not
  implement it partially or implicitly.
- Use `bloqueada` only for a concrete dependency that the repository cannot
  resolve locally. Tool installation, implementation, and other executable
  local work remain `pendiente` until started.
- A future phase plan may remain a clearly labelled draft. Preserve task IDs
  and provenance when freezing or moving its rows; activation still requires
  the gate declared by the active phase.
- A production deployment and its Home Assistant verification are separate
  tasks from local implementation. Local success is not an operational
  delivery.

## Canonical commands

During bootstrap, use `git diff --check` and `git status --short --ignored`.
P00-T02 must add one cross-platform canonical verification command before any
production code is accepted. It will cover formatting, lint, strict type
checking, unit tests, Home Assistant integration tests, coverage, and artifact
checks. Python dependencies will be managed by `uv`; update the lock whenever
dependency metadata changes.

Run the narrow test first and then the applicable canonical gate. Do not invoke
repository-wide formatters unless the active task assigns that write set.

## Manager-executor delegation

The repository uses the two global roles configured in the local Codex home;
repository-local `.agents` and `.codex` directories do not own or override
their profiles:

- Root manager: `gpt-5.6-sol`, reasoning `xhigh`. Its effective permissions
  come from the active local session and must be verified rather than assumed.
- Default implementation role: `luna_executor`, pinned globally to
  `gpt-5.6-luna` with reasoning `max`, `workspace-write`, approval policy
  `never`, with apps and MCP servers disabled.

At the start of a delegated wave, verify the named role, effective model,
reasoning effort, and live permissions. Report a fallback or mismatch instead
of silently substituting a generic worker. The global profile is an execution
preference, not a security boundary; the parent session may impose different
effective permissions.

The owner has authorized this manager-executor pattern for repository work:

1. The root freezes a coherent wave of compatible atomic tasks.
2. By default it starts one persistent `luna_executor` without inherited
   manager conversation, lets it read the canonical documents once, and sends
   ordered tasks to the same session sequentially.
3. The execution capsule contains only operational deltas: base commit, dirty
   state, ordered task IDs, allowed and forbidden files, frozen decisions,
   acceptance commands, and stop conditions.
4. Additional concurrent waves are justified only when latency materially
   matters and write sets are disjoint. Leave one agent slot for the root.
5. Executors do not use web, apps, MCP, deployment systems, Home Assistant, or
   other external services. They report a required external operation once.
6. The root performs one independent consolidated review of the complete wave
   diff and relevant call paths. It groups accepted defects into one correction
   pass for the same executor and reruns the affected gates.

The root retains shared contracts, public schemas, config-entry migrations,
security and privacy boundaries, secrets, deployment, Home Assistant mutation,
Git integration, and final acceptance. It also retains work when delegation
tooling is unavailable, the write set cannot be isolated, or delegation cost
exceeds the task; record the concrete exception in the phase plan.

Each execution capsule defines an observable progress checkpoint. If an
executor produces neither a requested status nor an allowed artifact across two
consecutive manager checkpoints and one direct status request, the root
interrupts the wave and records the exception instead of waiting repeatedly.
After the same persistent session stalls this way in two consecutive waves,
the root retains subsequent work until that session is replaced or the owner
directs another attempt. A slow successful gate is progress; silence with no
artifact is not.

An executor handoff may report only `listo para revisión`, `parcial`, or
`bloqueado`. Only the root decides whether a task or phase is complete.

## Ponytail gates

The global `ponytail`, `ponytail-review`, and `ponytail-audit` skills are part
of the repository workflow:

- The root applies Ponytail at `full` intensity once while minimizing and
  freezing each work wave.
- The executor implements that frozen minimum scope.
- The root folds one `ponytail-review` into the consolidated wave review and
  groups accepted simplifications into the normal correction pass.
- The root runs `ponytail-audit` once before closing a phase.

Ponytail governs unnecessary complexity only. It never removes or weakens
trust-boundary validation, data-loss prevention, safety gates, accessibility,
required tests, config migrations, deployment verification, or rollback.

## Minimum-change and artifact policy

Before creating a file, module, class, dependency, selector, service action, or
entity, trace the real consumer and search for an existing extension point.
Stop at the smallest safe implementation. Do not add speculative abstractions,
compatibility layers, registries, wrappers, base classes, configuration, or
entities for hypothetical consumers.

- Every tracked file must appear in the active write set and have a durable
  purpose, owning module, and concrete consumer or canonical command.
- Keep a helper beside its only consumer; extract it when real reuse or an
  architecture boundary requires it.
- Production modules must be reachable from a Home Assistant entrypoint or a
  tested integration flow.
- Commit scripts only for recurring development, verification, migration, or
  deployment workflows. Register them in `Makefile` or project scripts and
  document them in `docs/operations/`.
- Keep one root `README.md`. Use `PLAN.md` for coordination, `docs/adr/` for
  durable decisions, `docs/operations/` for repeatable runbooks, and
  `docs/status/` only for phase evidence.
- Do not leave placeholders, copied fixtures without provenance, commented-out
  code, debug output, temporary aliases, or unconsumed exports.

## Quality and delivery

- Fully type owned Python code and keep domain tests independent of Home
  Assistant.
- Test behaviour, failure modes, stale/unavailable inputs, DST/UTC boundaries,
  config migrations, entity identity, setup/unload/reload, and external
  contracts affected by a change.
- For every advertised runtime input, include one production-boundary test that
  proves the normalized value reaches the actual domain request. A source
  availability flag, successful provider call, or domain-only unit test is not
  evidence that the live evaluator consumed it.
- Before starting a behavioural shadow, verify that Recorder can retain the
  resolved target and reason needed by its acceptance comparison. Public
  recommendation state is the stable resolved target, not a transient
  `hold`/change indicator; if the surface cannot retain the required evidence,
  stop before deployment and correct the contract.
- Target at least 90% branch coverage for owned code and near-complete useful
  coverage for safety, availability, state transitions, and config flows.
- Do not hide failures with broad exception handlers, silent fallbacks, skipped
  tests, snapshot-only assertions, or mocks that bypass the production path.
- Review `git status`, the complete diff, ignored-secret status, and every added
  artifact before handoff.
- Report files changed, exact commands and results, assumptions, risks,
  deviations, delegated waves, correction passes, and visible approval-review
  events. Do not create a tracked usage report.

## GitFlow

- `main` contains accepted releases; `develop` is the integration branch.
- Develop a phase on `feature/<NN>-<slug>` from `develop`.
- Use Conventional Commits and include `Task: PNN-TXX` in the body or trailer.
- Merge completed phases into `develop` with `--no-ff` after all gates pass.
- Create `release/<version>` only for a release candidate; merge it to `main`,
  create an annotated tag, and merge it back to `develop`.
- A HACS shadow candidate may use a `v<version>bN` GitHub prerelease from its
  `release/<version>` branch. It is not an accepted release: stable annotated
  tags still originate from `main` only after the shadow gate passes.
- Do not commit directly to `main`, force-push, rewrite shared history, or
  change branches unless the active plan assigns that action.

## Secrets, privacy, and external systems

- Never commit `.env`, tokens, endpoints containing credentials, exact private
  coordinates, Home Assistant backups, entity dumps, traces containing private
  state, or runtime data.
- Never print secret values. Diagnostic output may show only variable names,
  presence, redacted fingerprints, or non-sensitive validation results.
- Batch external mutations and verify the exact target before changing Home
  Assistant or a deployment. Executors never perform those mutations.
- Keep blind and window actions in recommendation-only mode. A future actuator
  phase requires explicit owner approval, defined fail-safe behaviour, position
  feedback, obstruction/weather safety, rollback, and deployed verification.

## Protected areas

`AGENTS.md`, `docs/GOAL.md`, root configuration, manifests, config-entry schema,
deployment definitions, phase status, and real `.env` values are root-owned
unless a task explicitly grants their write access. Previous automation
versions and their tests are immutable migration evidence.
