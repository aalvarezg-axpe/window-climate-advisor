# Window Climate Advisor

Custom integration for Home Assistant that recommends how to use windows,
tilt positions, blinds, shutters, and solar protection from room conditions,
outdoor weather, forecasts, façade orientation, opening geometry, and thermal
comfort policy.

The project is in **local advisor/shadow development**. The accepted Python
engine and its Home Assistant informational entities are implemented locally;
deployment and the observed shadow period are still pending. It does not
control physical actuators. The deployed automation `v4.17_pre` remains the
operational baseline and rollback.

The product source of truth is [`docs/GOAL.md`](docs/GOAL.md). Active work is
tracked in
[`docs/phases/01-domain-optimizer/PLAN.md`](docs/phases/01-domain-optimizer/PLAN.md),
and repository-wide rules are in [`AGENTS.md`](AGENTS.md).

## Intended architecture

The distributable code lives under
`custom_components/window_climate_advisor`. Home Assistant entrypoints are
thin adapters around a typed, I/O-free domain engine. Configuration uses a UI
config flow plus room and opening subentries; no user-authored YAML is
required.

Current solar load is projected per opening from global radiation,
`sun.sun`, façade orientation, and overhang geometry. Missing source or sun
position data degrades the recommendation instead of inventing a favourable
value.

The initial entity surface is informational:

- recommendation per opening;
- recommended blind position when a cover is configured;
- safety-to-open status;
- active comfort profile and last-evaluation timestamp;
- redacted downloadable diagnostics with reason codes and source quality.

There are no services, notifications, helpers, YAML automations, or actuator
platforms in the integration.

## Install the shadow candidate with HACS

Prerequisites: Home Assistant 2026.8.0 or newer and HACS already configured.

1. In HACS, open the menu and select **Custom repositories**.
2. Add `https://github.com/aalvarezg-axpe/window-climate-advisor` as type
   **Integration**.
3. Download the explicit prerelease `v0.1.0b1`; enable prerelease tracking for
   this repository if HACS does not initially show it.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**, search for
   **Window Climate Advisor**, and complete its UI flows.

This installs an informational shadow advisor beside `v4.17_pre`; it does not
replace that automation or create notifications or physical actions. Follow
the backup, verification, and rollback procedure in
[`docs/operations/deployment.md`](docs/operations/deployment.md).

## Local development

The canonical checkout is:

```text
C:\Users\aalvarezg\Documents\Home Assistant\window-climate-advisor
```

The local Codex home provides the Sol/xhigh root manager, the persistent
Luna/max executor, and the three Ponytail skills. Repository-local
agent-profile folders are not used. See
[`docs/operations/development.md`](docs/operations/development.md).

## Local checks

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
`HOME_ASSISTANT_URL` and `HOME_ASSISTANT_ACCESS_TOKEN`. HACS is the selected
file-installation route and needs no additional `.env` variables.

## Safety and publication

The owner approved this public GitHub repository only as a custom HACS
installation channel. No public license or default HACS catalog submission has
been selected. Do not enable physical actions until the separate safety gate is
explicitly approved.
