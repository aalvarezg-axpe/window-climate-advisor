# ADR 0012 — Local advisor-day boundary

- Status: accepted
- Date: 2026-09-02
- Task: P02-T21

## Context

Manual windows and blinds have no physical feedback, so the advisor carries its
last stable recommendation across restarts. Carrying that assumption forever
also carries yesterday's position and pending notification context into the
next household day. The owner confirmed that a day should instead begin with
windows closed and blinds down, at 08:00 by default.

## Decision

Add one options-flow time value interpreted in Home Assistant's local timezone.
At that time, or on the first evaluation after a missed boundary, use a
persisted local calendar-date marker to reset each opening's assumed stable
state to closed and each physical blind to 0%. Openings without blinds retain
the neutral internal 100% blind value. Clear prior pending hysteresis and the
in-memory ordinary notification batch, then run the normal evaluation.

Native time tracking provides the prompt boundary refresh; the existing
five-minute coordinator update provides restart and missed-callback recovery.
Configured contact and cover observations remain the optimizer's current
physical input. The boundary itself creates no delivery or physical action.

## Consequences

- Reloads within one logical day do not reset the assumptions again.
- Calendar-date comparison remains correct across Europe/Madrid daylight-saving
  transitions without storing a fixed UTC alarm.
- Existing entries without the new option use the accepted 08:00 default;
  submitting the options form stores it explicitly.
- The persisted application-state payload migrates from version 1 to version 2;
  the config-entry schema and entity inventory remain unchanged.
- No helper, queue, entity, dependency, service, YAML automation or actuator is
  added.
