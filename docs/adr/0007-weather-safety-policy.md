# ADR 0007 — Weather safety policy

- Status: accepted for P01-T06
- Date: 2026-08-24
- Sources: catalog C001–C007, C017–C019 and predecessor A01/A05

## Decision

Wrap the optimizer result in a pure weather-safety policy. Safety may preserve
or restrict the candidate `open → tilt → closed`; it may never make it more
open. The output is a typed resolved recommendation (`open`, `tilt`, `close`,
or `degraded`), recommended window/blind state, safety boolean, and reason code.
An unchanged target retains its physical state; `hold` is not a public policy
result. It contains no service name, entity ID, or action callback.

Required observations are rain rate, gust, and at least one current/mean wind
direction. `None` represents missing/unavailable/malformed input; a stale flag
represents an otherwise numeric but expired snapshot. Either condition returns
`degraded`, recommends a closed window state, and reports unsafe-to-open. The
legacy assumption that missing direction is frontal is not retained because it
hid data loss.

Retain the v4.17 safety envelope:

- any gust at or above 45 km/h closes;
- façade exposure uses the nearer current/mean direction, a 15° conservative
  margin, and continuous full-open 10–20 / tilt 35–45 km/h limits;
- light rain is at most 1.2 mm/h and can allow tilt only below 18 km/h when the
  configured real overhang geometry protects the tilt opening;
- rain projection uses the safety gust `1.20 × gust + 2 km/h`, vertical rain
  speed 15 km/h, 0.20 m tilt opening, and 0.15 m vertical margin;
- heavy/unprotected rain closes. Even full geometric protection limits a new
  thermal opening recommendation to tilt, matching the legacy rain branch.

The `rain_protected` config flag enables geometric evaluation; it does not by
itself declare the opening safe. The optimizer's blind percentage is preserved
as information because closing a window for weather does not establish a blind
thermal optimum.

## Exclusions

- The policy does not evaluate forecast staleness, seasonal comfort, or thermal
  objective; those inputs are already typed upstream.
- Cross-evaluation stability and deduplication remain P01-T07.
- No physical action or notification delivery is permitted.
