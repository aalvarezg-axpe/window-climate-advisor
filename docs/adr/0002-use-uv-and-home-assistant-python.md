# ADR 0002 — Use uv and track Home Assistant's supported Python

- Status: accepted, provisioning pending
- Date: 2026-08-24

## Context

The local workstation currently exposes Python 3.11 and `uv`, but not GNU Make.
Current Home Assistant developer documentation requires Python 3.14.2 or newer
for a manual Core development environment. Building against the workstation's
default interpreter would therefore create an unrepresentative environment.

The predecessor `hyperlocal-weather` repository already demonstrates a locked
`uv` workflow and canonical `make` targets, but its Python 3.11 service runtime
must not be copied to a Home Assistant 2026 integration.

## Decision

- Manage Python and dependencies with `uv`.
- Pin the project interpreter to the version supported by the target Home
  Assistant release, beginning with Python 3.14.2 unless the installed target
  reports a newer requirement before bootstrap.
- Commit dependency metadata and `uv.lock` together.
- Expose all routine checks through one cross-platform project command selected
  in P00-T02.
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
