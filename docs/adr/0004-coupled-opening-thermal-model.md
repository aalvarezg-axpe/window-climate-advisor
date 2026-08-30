# ADR 0004 — Coupled opening and blind thermal model

- Status: accepted for P01-T02 and P01-T19
- Date: 2026-08-24
- Last amended: 2026-08-30
- Sources: catalog C008, C012, C014 and predecessor A03/A04/A09/A10

## Context

The optimizer needs auditable candidate loads for a closed, tilted, or open
window and a blind recommendation from 0% (closed) to 100% (raised). The
predecessor has no measured blind airflow curve. It does provide a conservative
unilateral airflow expression, a 12% tilt fraction, glazing coefficients, and a
provisional 0.15 solar residual for a closed blind.

P01-T19 re-evaluated the blind term after shadow observation. Full-scale
experiments show that shading devices disturb airflow and that useful
corrections depend on the device and flow regime, rather than on uncovered
percentage alone:

- [Tsangrassoulis et al. (1997)](https://doi.org/10.1016/S0038-092X(97)00073-X)
  tested 28 partly covered opening configurations and treated combined airflow
  and radiation as an experimental problem;
- [Argiriou et al. (2002)](https://doi.org/10.1016/S0360-5442(01)00058-5)
  derived shading-device correction coefficients as functions of Archimedes
  number for single-sided ventilation;
- [Lee et al. (2015)](https://doi.org/10.1016/j.enbuild.2015.08.018) measured
  exterior-venetian-blind pressure-loss rates from 0.22 to 0.90 and air-speed
  differences of about 50% across tested slat angles.

Those measurements support an obstruction effect but do not calibrate this
dwelling's roller shutters, opening fractions, wind exposure, or single-sided
flow. Transferring one of their coefficients would therefore be invented
precision.

## Decision

Implement four pure, dependency-free domain modules:

- `models.py`: `WindowState`, positive opening dimensions, finite non-negative
  environmental observations, and a 0–100 blind-opening value;
- `geometry.py`: opening area/fraction and linear blind solar transmission;
- `ventilation.py`: effective free area and the existing unilateral wind/stack
  airflow expression;
- `thermal.py`: solar, glazing conduction, and ventilation components whose sum
  is the candidate room heat load in watts (positive heats, negative cools).

For state opening fraction `f`, blind opening `b` in 0–1, and closed-blind
solar residual `r`:

```text
blind solar factor = r + b × (1 - r)
free area = width × height × f × b
solar transmission = ((1 - f) × SHGC + f) × blind solar factor
conduction = U × area × (1 - f) × (Tout - Tin)
ventilation = rho × cp × airflow × (Tout - Tin)
```

`f` is 0 for closed, 0.12 for tilt, and 1 for open. Airflow uses:

```text
Q = free_area / 2 × sqrt(max(0.001 × U²,
                                 0.0035 × height × |Tout - Tin|))
U = max(wind, 0.35 × gust) / 3.6
```

The defaults are historical/provisional assumptions: tilt 0.12, blind solar
residual 0.15, glazing SHGC 0.55, U-value 1.40 W/(m²·K), air density
1.2041 kg/m³, and heat capacity 1005 J/(kg·K). Tests vary blind position and
the provisional residual. No value is described as measured.

For P01-T19 the `b` multiplier is retained unchanged only as a first-order
uncovered-area geometry assumption: 0% is the zero-area lower bound and 100%
is the current full-opening upper bound. It is not an empirical airflow curve
or a calibrated discharge coefficient. Adding an exponent, device coefficient,
or new user option without corresponding evidence would make the model less
auditable, not more accurate.

The owner ruled out a dedicated physical calibration campaign as
disproportionate on 2026-08-30 and accepted this bounded relation as the best
defensible unmeasured estimate for the initial product. Missing physical
calibration is therefore not an open delivery gate. A future revision requires
new manufacturer evidence or passive operational observations that identify a
better relation; it does not justify speculative complexity now.

## Bounds and exclusions

- Dimensions must be finite and positive; percentages are finite and within
  0–100; radiation, wind, and gust are finite and non-negative.
- A closed window has zero ventilation. A fully lowered blind conservatively
  contributes zero free ventilation area; 100% raised restores the state's
  full free area.
- Property tests cover every 10% position from 0% through 100% and retain exact
  monotonic bounds. Direct-sun sensitivity also makes the consequence visible:
  under the provisional model, increasing blind opening can either improve or
  worsen net load depending on admitted radiation versus modeled ventilation.
- Recorder cannot calibrate the relation because the shadow entry has manual
  blinds and no observed window contacts/covers: it stores recommendations, not
  actual physical positions. It also has no airflow/tracer measurement or
  calibrated room thermal capacity/internal-gain model with which to isolate
  ventilation from sun, conduction, occupancy, and HVAC.
- A more accurate relation would require at least the shutter type and 0–100
  position geometry plus manufacturer free-area/pressure-loss data, or actual
  position and response observations rich enough to identify it. The initial
  product will not require a physical experiment; until better evidence appears,
  replaying a guessed alternative curve would compare inventions rather than
  evidence.
- P01-T02 consumes façade irradiance already calculated at the boundary. P01-T11
  later implements that missing global-to-façade boundary under ADR 0009; this
  thermal module still does not own sun state, weather safety, seasonal policy,
  hysteresis, or candidate selection.
- These formulas produce comparable candidate loads, not an actuator command
  and not a building-energy simulation presented as calibrated truth.
