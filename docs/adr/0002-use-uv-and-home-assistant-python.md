# ADR 0002 — Use uv and track Home Assistant's supported Python

- Status: accepted and implemented
- Date: 2026-08-24

## Context

The local workstation currently exposes Python 3.11 and `uv`, but not GNU Make.
The deployed Home Assistant 2026.8.2 instance and current developer
documentation require Python 3.14.2 or newer for the development environment.
Building against the workstation's default interpreter would therefore create
an unrepresentative environment.

The predecessor `hyperlocal-weather` repository already demonstrates a locked
`uv` workflow and canonical `make` targets, but its Python 3.11 service runtime
must not be copied to a Home Assistant 2026 integration.

## Decision

- Manage Python and dependencies with `uv`.
- Pin the project interpreter to Python 3.14.2 for the deployed Home Assistant
  2026.8.2 target.
- Commit dependency metadata and `uv.lock` together.
- Expose all routine checks through
  `uv run --frozen python scripts/verify.py`; do not require GNU Make.
- Run Home Assistant pytest inside local WSL 2 when invoked from Windows;
  native Windows lacks Core's required POSIX `fcntl` module.
- Separate fast domain tests from Home Assistant integration tests.
- Do not add production dependencies unless the standard library and Home
  Assistant APIs are insufficient and an ADR or phase task records the need.

Reference: <https://developers.home-assistant.io/docs/development_environment/>

## Consequences

- Phase 00 must provision the compatible interpreter through `uv` and install
  or replace the canonical command runner before code scaffolding.
- The project does not reuse the workstation's default Python 3.11 interpreter.
- The lock and Python pin become acceptance artifacts.
- CI and local development run the same canonical gates.
