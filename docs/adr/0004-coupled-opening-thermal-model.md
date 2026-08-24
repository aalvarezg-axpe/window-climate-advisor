# ADR 0004 — Coupled opening and blind thermal model

- Status: accepted for P01-T02
- Date: 2026-08-24
- Sources: catalog C008, C012, C014 and predecessor A03/A04/A09/A10

## Context

The optimizer needs auditable candidate loads for a closed, tilted, or open
window and a blind recommendation from 0% (closed) to 100% (raised). The
predecessor has no measured blind airflow curve. It does provide a conservative
unilateral airflow expression, a 12% tilt fraction, glazing coefficients, and a
provisional 0.15 solar residual for a closed blind.

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

## Bounds and exclusions

- Dimensions must be finite and positive; percentages are finite and within
  0–100; radiation, wind, and gust are finite and non-negative.
- A closed window has zero ventilation. A fully lowered blind conservatively
  contributes zero free ventilation area; 100% raised restores the state's
  full free area.
- P01-T02 consumes façade irradiance already calculated at the boundary. It
  does not implement sun position, overhang shade, weather safety, seasonal
  policy, hysteresis, or candidate selection.
- These formulas produce comparable candidate loads, not an actuator command
  and not a building-energy simulation presented as calibrated truth.
