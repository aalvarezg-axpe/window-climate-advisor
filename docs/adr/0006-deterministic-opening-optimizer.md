# ADR 0006 — Deterministic opening optimizer

- Status: accepted for P01-T04
- Date: 2026-08-24
- Sources: catalog C009/C010/C013/C015 and F04-04

## Decision

Enumerate the small action space for each opening: `closed/open` plus `tilt`
when supported, crossed with blind opening from 0 to 100% in an integer step
that divides 100. The initial 10% step produces 22 or 33 candidates. Do not add
a numerical solver or optimization dependency.

For each current or forecast horizon, derive intent from the selected profile:
heat below the lower bound or preconditioning target minus hysteresis, cool
above the upper bound or target plus hysteresis, otherwise hold. Candidate
thermal cost is `-load` for heating, `load` for cooling, and `abs(load)` for
hold; lower is better. When a valid forecast exists, use the worse of current
and forecast cost.

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
