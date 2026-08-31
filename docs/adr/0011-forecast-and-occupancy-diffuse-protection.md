# ADR 0011 — Forecast- and occupancy-aware diffuse protection

- Status: accepted for Phase 02
- Date: 2026-08-31
- Sources: owner heat-protection requirement and P02-T17

## Decision

Keep full blind opening as the Summer default when façade geometry shows no
direct sun. Unlock the existing joint window/blind candidate space only when
current outdoor temperature or today's first daily forecast maximum reaches
the active Summer upper comfort bound. The room must be at or above that upper
bound while the dwelling is occupied; when every selected occupant is known
away, the lower comfort bound permits earlier protection. Below the lower
bound, diffuse radiation alone never justifies lowering a blind.

Store the people who define thermal occupancy as one optional multi-person
field in the dwelling config entry. It is independent of notification-recipient
subentries. The dwelling is unoccupied only when every selected native
`person` has a known non-`home` state. Empty selection, missing entities, and
`unknown` or `unavailable` state all retain the conservative occupied policy.
Selected person changes are normal coordinator inputs.

Today's daily maximum is context, not a thermal forecast horizon. It never
becomes an invented future indoor temperature, solar load, or irradiance. The
current optimizer still scores only observed thermal conditions and exposes a
specific diffuse-heat reason when the accepted blind target is below 100%.

## Consequences

- The active comfort bounds are the only heat thresholds; no option, helper,
  dependency, or new entity is added.
- Direct-sun candidates, Winter night insulation, weather safety, stability,
  blind deadband, and the non-closed/positive-blind invariant are unchanged.
- The optional field requires no config-entry version change. Existing entries
  without it remain valid and conservatively occupied; older integration
  versions ignore it on rollback.
- Away-time recommendations may become more protective, but notification
  event-time and delivery-time presence gates still create neither a pending
  batch nor a message. Arrival evaluates the occupied policy afresh.
- All blind values remain recommendations. This decision does not authorize a
  cover, window, HVAC, or other physical service call.
