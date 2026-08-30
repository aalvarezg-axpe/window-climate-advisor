# Local development and agent roles

## Canonical locations

- Repository: `C:\Users\aalvarezg\Documents\Home Assistant\window-climate-advisor`
- Global Codex configuration: `C:\Users\aalvarezg\.codex\config.toml`
- Global executor profile: `C:\Users\aalvarezg\.codex\agents\luna_executor.toml`
- Global skills: `C:\Users\aalvarezg\.codex\skills\ponytail*`

The project is developed on the local Windows workstation. The remote server
contains the separate `hyperlocal-weather` reference repository only; it is not
a development or deployment location for this project.

## Effective agent roles

The root configuration defines:

- manager: `gpt-5.6-sol`, reasoning `xhigh`;
- default subagent model: `gpt-5.6-luna`, reasoning `max`.

The global `luna_executor` profile further restricts the executor to coding in
the active workspace with `approval_policy = "never"`, no apps, no MCP servers,
no web, and no deployment/external-service operations.

The repository intentionally does not duplicate those root-owned profiles or
skills in `.agents` or `.codex`. At the beginning of a delegated wave, the
manager verifies the effective role and reports any mismatch. Repository
instructions define the workflow; global configuration defines the executable
profiles and skills.

Ponytail is applied at `full` intensity when freezing a work wave;
`ponytail-review` is part of the consolidated root review and
`ponytail-audit` runs once before closing a phase.

## Environment variables

The ignored `.env` currently contains the two variables needed for live API
inspection and configuration verification:

| Variable | Purpose | Secret |
|---|---|---|
| `HOME_ASSISTANT_URL` | Target Home Assistant base URL | private endpoint |
| `HOME_ASSISTANT_ACCESS_TOKEN` | Long-lived API authentication | yes |

These variables are sufficient for pure Python development, tests, and the Home
Assistant REST/WebSocket checks already used by the predecessor project. Never
print either value.

P01-T10 selected the public Git/HACS route at
`https://github.com/aalvarezg-axpe/window-climate-advisor`. HACS owns the write
to Home Assistant's `config/custom_components` directory, so no mounted-path,
SSH, GitHub, or HACS credential belongs in this repository's `.env`.

Room sensors, window contacts, cover entities, geometry, thresholds, schedules,
comfort settings, and notification destinations are product configuration.
They belong in the Home Assistant config/reconfigure/options flows, not `.env`.

## Bootstrap workflow

```powershell
Set-Location 'C:\Users\aalvarezg\Documents\Home Assistant\window-climate-advisor'
uv sync --frozen --group dev
uv run --frozen python scripts/verify.py
```

The repository pins Python 3.14.2 for the deployed Home Assistant 2026.8.2
target. `scripts/verify.py` is the canonical cross-platform runner; GNU Make is
not required. It checks artifacts/secrets, formatting, lint, strict typing, and
the Home Assistant integration tests with branch coverage.

Home Assistant Core 2026.8 does not execute its pytest plugin natively on
Windows because it imports POSIX modules including `fcntl`. The canonical
runner therefore executes static checks in the Windows `uv` environment and
delegates pytest to the local default WSL 2 distribution. WSL uses the same
`uv.lock`, Python 3.14.2, and an environment outside the repository at
`$HOME/.cache/window-climate-advisor/venv`; no remote development host is used.

Phase 00 must then:

1. keep `.python-version`, `pyproject.toml`, and `uv.lock` synchronized;
2. run the canonical gate before accepting production code;
3. add focused tests as each production path is introduced.

## Secret-safe checks

Allowed diagnostics show variable names and whether values are populated. They
may use a short one-way fingerprint to compare two copies without printing the
value. Do not echo, log, archive, commit, or paste `.env` content.

Before handoff:

```powershell
git status --short --ignored
git diff --check
```

Confirm that `.env` appears only as ignored and that no generated Home Assistant
config, token, state dump, trace, or backup is tracked.
