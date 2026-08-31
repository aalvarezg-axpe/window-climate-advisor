# Window Climate Advisor

Custom integration for Home Assistant that recommends how to use windows,
tilt positions, blinds, shutters, and solar protection from room conditions,
outdoor weather, forecasts, façade orientation, opening geometry, and thermal
comfort policy.

The project is in **Phase 02 contextual-notification validation**. Candidate
`v0.2.0b10` stores only recipient persons, discovers their associated Home
Assistant Mobile App devices through native registries, sends stable-change
summaries only to those devices currently home, and gives fresh advice when a
configured occupant arrives. Live-verified `v0.1.0b5` remains the integration
fallback and operational rollback. Neither build controls physical actuators;
the retired `v4.17_pre` automation remains only as an immutable behavioural
fixture.

Notification summaries use separate window and blind bullet sections. Rooms
with one opening appear once by room name; rooms with several openings retain
only the shortest configured suffix needed to distinguish them, such as
`Cocina SO` and `Cocina NO` without overhang qualifiers. Weather-forced changes
include their evaluated safety reason. In Summer, every thermal target below
full opening identifies the actual limiting cause: comfort floor, outdoor air,
façade radiation, stability margin, or an active confirmation period. Coupled
optimizer window/blind changes are published together, and ordinary stable
changes within one fixed 10-minute window are combined instead of notifying
room by room.

The product source of truth is [`docs/GOAL.md`](docs/GOAL.md). Active work is
tracked in
[`docs/phases/02-contextual-notifications/PLAN.md`](docs/phases/02-contextual-notifications/PLAN.md),
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

Daily weather maxima select the automatic comfort profile. The live adapter
does not claim a thermal forecast horizon: Home Assistant's standard weather
forecast has no future irradiance field, and no configured source provides one.
The optimizer therefore applies its explicit missing-horizon penalty instead
of inventing future solar load or indoor temperature.

Seasonal intent is explicit at the optimizer boundary. Summer uses available
free cooling until the room reaches its lower comfort boundary plus hysteresis,
then becomes neutral rather than deliberately heating a cool room. Winter may
heat but is neutral when cooling would otherwise be requested. Shoulder season
retains the symmetric heat/cool/neutral objective. Weather safety remains
absolute.

Rain is evaluated per façade rather than as a dwelling-wide close. With no
meaningful projected gust, or on a leeward façade, rain does not override the
thermal target; exposed façades retain the intensity, gust, overhang and
protected-tilt checks. Gusts of 45 km/h or more still close every façade, and
missing/stale rain, gust or direction remains explicitly degraded.

The thermal score is a comparative first-order model, not a calibrated
building simulation. It combines projected solar gain, glazing conduction, and
single-sided ventilation in watts for every feasible window/blind candidate.
Blind opening scales effective free area linearly as the accepted bounded
estimate; the integration does not claim measured room response or airflow.
Diffuse façade radiation remains in that thermal balance, but during Summer a
lowered blind is considered only while direct projected sun reaches the opening
after orientation and overhang shade. Winter retains its night-insulation
candidate space.

The initial entity surface is informational:

- resolved `open`/`tilt`/`close` recommendation per opening, or explicit
  degradation, with one bounded Recorder-visible reason attribute;
- recommended blind position for each physical blind, including manual ones;
- safety-to-open status;
- active comfort profile and last-evaluation timestamp;
- redacted downloadable diagnostics with reason codes and source quality.

The integration owns no service, helper, YAML automation, or actuator platform.
It may call only Home Assistant's fixed `notify.send_message` action for native
Mobile App entities associated with explicitly configured persons; it stores
neither target nor arbitrary action name and queues nothing while occupants are
away.

## Install the notification beta with HACS

Prerequisites: Home Assistant 2026.8.0 or newer and HACS already configured.

1. In HACS, open the menu and select **Custom repositories**.
2. Add `https://github.com/aalvarezg-axpe/window-climate-advisor` as type
   **Integration**.
3. Download the explicit prerelease `v0.2.0b10`; enable prerelease tracking for
   this repository if HACS does not initially show it.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**, search for
   **Window Climate Advisor**, complete its UI flows, and add recipient
   subentries by selecting each `person`. Associated Mobile App devices are
   discovered automatically and only devices currently home are notified.

This installs a recommendation and contextual-notification advisor without
restoring the retired `v4.17_pre` automation or performing physical actions.
Follow the backup, verification, and rollback procedure in
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
