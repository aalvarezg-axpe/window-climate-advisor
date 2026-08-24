# Contributing

Read `AGENTS.md`, `docs/GOAL.md`, and the active phase `PLAN.md` before making a
change. `docs/GOAL.md` prevails if instructions conflict.

## Workflow

1. Start a phase from `develop` on `feature/<NN>-<slug>`.
2. Mark one verifiable `PNN-TXX` task `en curso` before editing.
3. Keep the diff inside its declared write set and avoid unrelated formatting.
4. Search for an existing extension point before adding a dependency, file,
   entity, action, abstraction, or configuration field.
5. Add focused tests for behaviour and failure paths, then run the narrow test
   followed by `uv run --frozen python scripts/verify.py`.
6. Review the full diff, status, ignored files, and artifact inventory.
7. Use a Conventional Commit and add `Task: PNN-TXX` to its body or trailer.

Completed phases merge into `develop` with `--no-ff`. Releases use
`release/<version>`, an annotated tag on `main`, and a merge back to `develop`.
Never force-push or commit directly to `main`.

## Boundaries

- Do not commit `.env`, credentials, private coordinates, Home Assistant state
  dumps, backups, or runtime data.
- Do not edit Home Assistant `.storage` files directly.
- Do not put Home Assistant, provider, or I/O types inside the domain engine.
- Do not interpret missing or stale data as favourable conditions.
- Do not introduce physical actuator control. All window and blind outputs are
  recommendations until a separately approved safety phase exists.
- Do not add nested README files, task summaries, placeholder modules, or
  exploratory scripts. Use the canonical documentation paths from `AGENTS.md`.

## Acceptance

Every handoff lists files changed, exact checks and results, assumptions,
risks, deviations, delegation waves, and external mutations. Local tests do
not complete a deployment task: Home Assistant identity, availability,
configuration loading, diagnostics, and rollback must be verified separately.
