# HACS notification-beta deployment and rollback

## Frozen target

- Repository: `https://github.com/aalvarezg-axpe/window-climate-advisor`
- HACS category: Integration / custom repository
- Candidate: GitHub prerelease `v0.2.0b2` from `release/0.2.0`
- Minimum Home Assistant: 2026.8.0
- Integration/operational rollback: live-verified `v0.1.0b5`
- Behavioural baseline only: immutable `v4.17_pre` fixture; no longer deployed

The candidate may call only fixed `notify.send_message` for Mobile App devices
associated through native registries with explicitly configured persons, and
only when each device's tracker is home. It must not register an integration
service, retain a notification backlog, or control a physical device.

## Preflight and backup

1. Run `uv run --frozen python scripts/verify.py` at the candidate commit.
2. Confirm the candidate commit is the head of remote `release/0.2.0` and the
   GitHub prerelease points to that exact commit.
3. Confirm `v0.1.0b5` remains downloadable. Do not restore the retired
   `v4.17_pre` automation as part of this beta deployment.
4. Create or confirm a current full backup before installing the notification
   beta; do not record its private identifier in Git.
5. Record the backup, candidate commit, and observed baseline in
   `docs/status/phase02-notifications.md` without storing private entity state.

## Install

1. In the existing HACS custom repository, select and download `v0.2.0b2`.
   Enable prerelease tracking if HACS hides beta versions.
2. Confirm HACS reports exactly `v0.2.0b2` before continuing.
3. Restart Home Assistant once; do not reload only the integration after a new
   custom-component install.
4. Keep the existing dwelling entry. In its configure flow, add each recipient
   by selecting the intended `person`. The integration follows that person's
   native Mobile App trackers to sibling `notify` entities through registry
   relationships; it never compares names or coordinates. Do not edit YAML or
   `.storage`.

## Verify before accepting the beta

1. Confirm exactly one config entry, the expected dwelling/opening devices and
   entities, stable unique identities, and no duplicates.
2. Confirm recommendation, optional blind-position, safety, active-profile,
   and last-evaluation entities are available or explicitly degraded with a
   reason.
3. Download diagnostics and confirm they contain only a recipient count: no
   person/notify IDs, presence, message content, raw states, token, coordinates,
   names, or household history.
4. Check **Settings → System → Repairs** and the Home Assistant logs for setup,
   reload, migration, notification, or custom-component errors.
5. Reload the config entry once and restart Home Assistant once. Repeat the
   entity, duplicate, availability, Repairs, and log checks.
6. Exercise one bounded delivery matrix: present, away, mixed recipients,
   unavailable target, one accepted stable change, and one real arrival. Record
   only exact counts and redacted outcomes. Confirm unchanged evaluations,
   startup restoration, repeated `home`, and unavailable-to-`home` recovery do
   not duplicate an arrival message and that away-time changes are not replayed.
7. Confirm failed delivery leaves recommendation/safety entities available,
   no owned persistent notification/backlog exists, the integration registers
   no service, and no window, blind, HVAC, or other actuator call occurs.
8. Confirm `v0.1.0b5` remains downloadable.

## Roll back

1. Capture redacted diagnostics and errors.
2. While `v0.2.0b2` is loaded, remove recipient subentries through the config
   flow if rolling back only the notification feature.
3. In HACS, redownload `v0.1.0b5` and restart Home Assistant once. For complete
   removal, remove the config entry and HACS download instead.
4. Confirm recommendations and safety remain available, notifications stop,
   and Repairs/logs are clean.
5. Restore the pre-beta backup only if normal rollback does not return Home
   Assistant to the verified baseline.

`v0.1.0b5` is the last live-verified integration and operational fallback.
`v4.17_pre` remains only as an immutable characterization fixture.
