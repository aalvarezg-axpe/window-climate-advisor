# Window Climate Advisor

Custom integration for Home Assistant that will recommend how to use windows,
tilt positions, blinds, shutters, and solar protection from room conditions,
outdoor weather, forecasts, façade orientation, opening geometry, and thermal
comfort policy.

The project starts in **bootstrap and shadow-only mode**. It does not control
physical actuators. The deployed automation `v4.17_pre` remains the operational
baseline and rollback while the Python engine is characterized and compared.

The product source of truth is [`docs/GOAL.md`](docs/GOAL.md). Active work is
tracked in [`docs/phases/00-bootstrap/PLAN.md`](docs/phases/00-bootstrap/PLAN.md),
and repository-wide rules are in [`AGENTS.md`](AGENTS.md).

## Intended architecture

The distributable code will live under
`custom_components/window_climate_advisor`. Home Assistant entrypoints will be
thin adapters around a typed, I/O-free domain engine. Configuration will use a
UI config flow plus room and opening subentries; no user-authored YAML will be
required.

The initial entity surface will be informational:

- recommendation per opening;
- recommended blind position;
- safety and availability status;
- thermal balance, airflow, solar load, and confidence diagnostics;
- global strategy and reason codes.

## Local development

The canonical checkout is:

```text
C:\Users\aalvarezg\Documents\Home Assistant\window-climate-advisor
```

The local Codex home provides the Sol/xhigh root manager, the persistent
Luna/max executor, and the three Ponytail skills. Repository-local
agent-profile folders are not used. See
[`docs/operations/development.md`](docs/operations/development.md).

## Bootstrap checks

```powershell
uv sync --frozen --group dev
uv run --frozen python scripts/verify.py
```

The verification script is the canonical cross-platform gate. It runs artifact
and secret checks, Ruff, strict mypy, and the Home Assistant pytest suite with
branch coverage. On the Windows workstation,
the same command runs the Home Assistant tests in local WSL because Core
requires POSIX modules such as `fcntl`.

## Environment

Copy `.env.example` to the ignored `.env`. Live Home Assistant API checks need
`HOME_ASSISTANT_URL` and `HOME_ASSISTANT_ACCESS_TOKEN`. A separate safe route
for installing files into Home Assistant's `config/custom_components` directory
must be selected before deployed integration testing.

## Safety and publication

No license or public distribution channel has been selected. Do not publish the
repository or enable physical actions until the corresponding decisions and
safety gates are explicitly approved.
