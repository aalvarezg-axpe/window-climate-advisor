# v4.17_pre behaviour matrix

- Task: `P01-T01`
- Catalog schema: `tests/fixtures/migration/case_catalog.json`, version 1
- Baseline: immutable `v4.17_pre`
- Sources: A01 and A03–A10 from `v4_17_inventory.md`

This matrix inventories the accepted legacy decision boundaries; it is not an
implementation of the YAML automation. Exact machine-readable inputs,
provenance, gaps, and dispositions live in the JSON catalog. Later tasks create
executable assertions only beside the domain or adapter that consumes a case.

## Legacy output vocabulary

| Surface | Code | Legacy meaning | v1 disposition |
|---|---|---|---|
| Window | `A` / `O` | Recommend fully open / tilt. | Replace thermal selection with optimizer output; retain weather limits. |
| Window | `R` | Close for rain or wind. | Keep as absolute weather-safety priority. |
| Window | `F` / `H` | Close to preserve coolness / warmth. | Replace discrete heuristics with optimizer output. |
| Window | `M` | Hold/no recommendation. | Adapt to the typed `hold` or `degraded` result. |
| Blind | `P` / `I` | Lower for solar protection / night insulation. | Replace with the joint 0–100% optimum. |
| Blind | `G` / `V` | Raise for solar gain / ventilation. | Replace with the joint optimum while preserving free airflow. |
| Blind | `M` | Hold/no recommendation. | Adapt to stable typed output. |

Codes are migration vocabulary only. They are not public v1 entity states and
must not become a second policy engine.

## Decision and property inventory

Priority 1 is weather safety, 2 is availability/airflow coherence, 3 is thermal
policy, and 4 is stability/presentation. Safety always wins.

| Case | Inputs or boundary | Legacy output/property | Category / priority | Disposition / owner | Source / scenarios |
|---|---|---|---|---|---|
| C001 | Gust ≥45 km/h | Window `R` | weather safety / 1 | keep / P01-T06 | A01 / S04,S09 |
| C002 | Light rain, low gust, full geometric protection | `O` with thermal need, else `M` | weather safety / 1 | keep / P01-T06 | A01 / S04,S09 |
| C003 | Rain with partial/no sufficient protection | `O` only for protected tilt plus need, else `R` | weather safety / 1 | keep / P01-T06 | A01 / S04,S09 |
| C004 | Worst current/mean wind direction and continuous façade limit | Window `A`, `O`, or `R` | weather safety / 1 | keep / P01-T06 | A05 / S09,S12 |
| C005 | Cold context near upper limit with adverse outside/solar balance | Window `F` | thermal / 3 | replace / P01-T06 | A01 / S06,S07 |
| C006 | Heat context near lower limit, outside ≥0.5 °C colder | Window `H` | thermal / 3 | replace / P01-T06 | A01 / S06,S10 |
| C007 | Window `A` or `O` | Blind `V`, 100% open | airflow/thermal / 2 | adapt / P01-T06 | A03 / S04 |
| C008 | Blind `P`, current/forecast heat and solar | 0–80%, 10-point steps | thermal / 3 | replace / P01-T02 | A03 / S02–S04 |
| C009 | Winter direct sun, ≥150 W/m², room below upper limit | Blind `G`, 100% | thermal / 3 | replace / P01-T04 | A01 / S04,S10 |
| C010 | Winter with sun at/below horizon | Blind `I`, 0% | thermal / 3 | replace / P01-T04 | A01 / S04,S10 |
| C011 | Binary `terraza_caliente` thresholds | Candidate `F` and `P` | thermal / 3 | remove / P01-T05 | A01 / S03 |
| C012 | Increasing room heat or solar load | Blind opening never increases | thermal / 3 | adapt / P01-T02 | A03 / S02,S03 |
| C013 | Worse valid solar/conduction forecast | Forecast cannot open blind further | thermal / 3 | adapt / P01-T04 | A03 / S03,S07 |
| C014 | Historical geometry, cool outside, solar 0 then 1200 W/m² | Solar can reverse opening benefit | thermal / 3 | adapt / P01-T02 | A04 / S06 |
| C015 | Current/forecast delta and missing forecast | Worst horizon; stricter missing-data threshold | data quality / 2 | adapt / P01-T04 | A04 / S07,S08 |
| C016 | New vs existing opening at -150/+50 W boundaries | Retain without rearming | stability / 4 | adapt / P01-T07 | A04 / S07,S12 |
| C017 | Missing, unavailable, malformed, or stale forecast | Exclude forecast and expose degradation | data quality / 2 | adapt / P01-T06 | A04 / S08,S14 |
| C018 | Façade distance 0–105° | Continuous 10–20 / 35–45 km/h limits | weather safety / 1 | keep / P01-T06 | A05 / S09 |
| C019 | 0.5 m vs 1.2 m overhang at 8 km/h façade gust | Tilt-only vs full rain protection | weather safety / 1 | keep / P01-T06 | A05 / S09 |
| C020 | Forecast maxima around 25 °C and history around 21/25 °C | Calentar/Refrescar/Neutral | thermal / 3 | replace / P01-T03 | A06 / S10 |
| C021 | No forecast or history values | Neutral legacy result | data quality / 2 | adapt to explicit degradation / P01-T03 | A06 / S10,S14 |
| C022 | Same/opposite blind action for 0/10/15 min | Stable change only after 15 min | stability / 4 | adapt / P01-T07 | A08 / S05,S12 |
| C023 | 30 days × 48 percentage samples | Percentage drift is diagnostic | stability / 4 | adapt / P01-T07 | A03 / S05,S11,S13 |
| C024 | `A→O` degradation vs `O→A` improvement | Faster unsafe degradation, stable improvement | safety/stability / 1 | keep / P01-T07 | A07 / S11,S12 |
| C025 | 30-minute ordinary period plus separate weather triggers | Bounded recovery without delaying safety | stability / 1 | adapt / P01-T09 | A07 / S11 |
| C026 | Weather recovery or restart with prior physical category | Do not erase memory or repeat same result | stability / 4 | adapt / P01-T07 | A08 / S12,S14 |
| C027 | Multiple room/reason candidates | At most one grouped candidate; none delivered in shadow | stability / 4 | adapt / P01-T07 | A07 / S11,S13 |

## Keep/replace boundary

- Keep: rain/wind precedence, conservative direction selection, continuous
  façade exposure, and real opening/overhang geometry.
- Replace: `F/H/P/G/I/V` thermal selection, fixed seasonal thresholds as final
  defaults, and `terraza_caliente` as an independent cause.
- Adapt: missing/stale data to explicit degradation, legacy stability to typed
  restart-safe state, and consolidated notification behaviour to a candidate
  only. Shadow mode delivers no notification.

## Evidence gaps

- Solar/front/side overhang scenarios 1–6 and restart/event-loss scenarios
  36–42 in the predecessor HANDOFF lack raw executable replay.
- The 0.15 blind residual, thermal coefficients, comfort thresholds, and
  historic geometry are assumptions until measured or sensitivity-tested.
- S13 originates from a different historical automation. It remains
  reference-only until the new shadow contract explicitly accepts it.
- No raw 835-evaluation dataset exists; the model document contains only its
  summary. No synthetic history is presented as measured evidence.
