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

Installing a custom integration additionally requires writing files below Home
Assistant's `config/custom_components` directory. The REST API token does not by
itself provide that file channel. Before deployed tests, P00-T04 must select one
of these mutually exclusive contracts:

1. a server-visible mounted config path, represented by
   `WCA_HOME_ASSISTANT_CONFIG_PATH`; or
2. SSH/SFTP using `WCA_HOME_ASSISTANT_SSH_HOST`,
   `WCA_HOME_ASSISTANT_SSH_PORT`, `WCA_HOME_ASSISTANT_SSH_USER`, and
   `WCA_HOME_ASSISTANT_SSH_KEY_PATH`; or
3. an approved Git/HACS installation workflow, which needs repository hosting
   rather than extra Home Assistant credentials.

Prefer a key or mounted path over a password. Do not register all alternatives;
choose one, document its consumer, and keep its private value in `.env` or the
deployment secret store.

Room sensors, window contacts, cover entities, geometry, thresholds, schedules,
comfort settings, and notification destinations are product configuration.
They belong in the Home Assistant config/reconfigure/options flows, not `.env`.

## Bootstrap workflow

```powershell
Set-Location 'C:\Users\aalvarezg\Documents\Home Assistant\window-climate-advisor'
git diff --check
```

Phase 00 must then:

1. provision the Home Assistant-compatible Python interpreter with local `uv`;
2. select a cross-platform canonical command runner or install GNU Make;
3. create and lock the development environment;
4. expand the canonical verification gate before adding production code.

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
