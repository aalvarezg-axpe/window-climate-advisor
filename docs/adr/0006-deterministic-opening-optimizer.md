# ADR 0006 — Deterministic opening optimizer

- Status: accepted for P01-T04
- Date: 2026-08-24
- Sources: catalog C009/C010/C013/C015 and F04-04

## Decision

Enumerate the small action space for each opening: `closed/open` plus `tilt`
when supported, crossed with blind opening from 0 to 100% in an integer step
that divides 100. A non-closed window requires a blind opening above 0%; the
initial 10% step therefore produces 21 or 31 feasible candidates. The observed
current action is still scored separately when it is non-closed/0%, so the
advisor can recommend correcting a real incoherent state without allowing it
to win a tie. When an opening has no configured blind, only 100% is feasible;
the optimizer must not invent unavailable solar protection. Do not add a
numerical solver or optimization dependency.

P02-T16 applies the same minimum candidate restriction during Summer when the
production solar geometry reports zero direct irradiance on the opening: only
a 100% raised blind is feasible. The diffuse façade component remains in every
window-state thermal load, so this does not erase ambient solar heat from the
room balance. It only prevents diffuse light, movement cost, or persisted
recommendation state from being treated as a Summer reason to obstruct a
manual blind. Direct sun restores the existing complete 0–100% blind candidate
set. Winter retains that candidate set without direct sun so the historical
night-insulation state remains feasible.

The fully raised Summer target is a feasibility constraint, not an optional
cost improvement. The stability layer therefore does not apply its ordinary
minimum-benefit veto to that blind transition, but still requires the existing
15-minute continuous direction confirmation. This prevents movement-cost and
diffuse-load scoring from retaining an infeasible 10% state indefinitely
without weakening anti-churn timing.

For each current or forecast horizon, derive intent from the selected profile
and explicit season. Shoulder season remains symmetric: heat below the lower
bound or preconditioning target minus hysteresis, cool above the upper bound or
target plus hysteresis, otherwise neutral. Summer keeps cooling while indoor
temperature is above the lower bound plus hysteresis, then maps the heating
side to neutral; Winter keeps heating but maps the cooling side to neutral.
Candidate thermal cost is `-load` for heating, `load` for cooling, and
`abs(load)` for neutrality; lower is better. When a valid forecast exists, use
the worse of the current and forecast costs under the same season.

This P01-T18 amendment prevents deliberate Summer gain from hotter outdoor air
or sun once cooling is unnecessary, and deliberate Winter loss to colder air
once heating is unnecessary. Neutrality minimizes signed-load magnitude; it
does not prescribe a window or blind position. Shoulder behaviour, physical
model bounds, and downstream absolute weather safety are unchanged.

P02-T12 corrects where Summer cooling becomes unnecessary. A production-shaped
low-sun interval proved that stopping at the preconditioning target could
retain tilt while full opening offered materially greater free cooling and the
room was still above its lower comfort edge. Summer therefore cools down to
`lower + hysteresis`; the exact edge is neutral to avoid overcooling and churn.
No Winter, Shoulder, physical-model, penalty, stability, or safety rule changes.

P02-T15 exposes one bounded cause for a Summer optimum below full opening.
The explanation follows the same selected profile and current thermal terms:
lower comfort boundary, outdoor air not cooler, façade radiation outweighing
ventilation cooling, or insufficient benefit after the existing stability
costs. A retained non-open target waiting for its opening delay reports that
confirmation explicitly. These codes explain the result; they do not add a
new score, threshold, input, or control path.

The total score in watt-equivalent comparison units is:

```text
worst horizon thermal cost
+ window state-distance × window movement penalty
+ blind travel fraction × full-travel penalty
+ missing-forecast penalty when the candidate changes current state
```

Movement and missing-forecast penalties are required caller inputs with no
claimed calibrated defaults. They must be finite and non-negative. Sensitivity
tests demonstrate their effect before replay selects operational values.

Tie-breaking is deterministic: lowest total, then unchanged combined state,
then least window distance, then least blind travel, then the fixed
`closed/tilt/open` rank and lower blind percentage. The result includes the
winning action, component loads/costs, and number of evaluated candidates for
diagnostics and exhaustive tests.

## Exclusions

- Weather safety, missing safety observations, reason codes, and degradation
  remain P01-T06 and can override the optimizer absolutely.
- Hysteresis across evaluations and notification candidates remain P01-T07.
- No candidate is a command; all outputs are recommendations.
