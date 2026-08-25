# HACS shadow deployment and rollback

## Frozen target

- Repository: `https://github.com/aalvarezg-axpe/window-climate-advisor`
- HACS category: Integration / custom repository
- Candidate: GitHub prerelease `v0.1.0b2` from `release/0.1.0`
- Beta bootstrap default branch: `release/0.1.0`; restore `main` after acceptance
- Minimum Home Assistant: 2026.8.0
- Shadow duration: four consecutive calendar days after the verification gate
- Operational baseline and rollback: deployed `v4.17_pre`

The candidate is informational only. It must not own notifications, call a
service, or control a physical device.

## Preflight and backup

1. Run `uv run --frozen python scripts/verify.py` at the candidate commit.
2. Confirm the candidate commit is the head of remote `release/0.1.0`, the
   GitHub prerelease points to that exact commit, and the beta-bootstrap default
   branch exposes the same HACS structure without making `main` releasable.
3. In Home Assistant, confirm `v4.17_pre` is available and unchanged.
4. Confirm the completed full baseline backup named
   `pre-window-climate-advisor-0.1.0b1`; it predates both beta downloads. Create
   a newer backup only if unrelated Home Assistant state changed meanwhile.
5. Record the backup, candidate commit, and observed baseline in
   `docs/status/phase01-shadow.md` without storing private entity state.

## Install

1. In HACS, open **Custom repositories** and add the frozen repository URL as
   type **Integration**.
2. Select and download `v0.1.0b2`. Enable prerelease tracking for this
   repository if HACS hides beta versions.
3. Restart Home Assistant once; do not reload only the integration after a new
   custom-component install.
4. Add **Window Climate Advisor** from
   **Settings → Devices & services → Add integration** and configure one
   dwelling through the UI. Do not edit YAML or `.storage`.

## Verify before starting the shadow clock

1. Confirm exactly one config entry, the expected dwelling/opening devices and
   entities, stable unique identities, and no duplicates.
2. Confirm recommendation, optional blind-position, safety, active-profile,
   and last-evaluation entities are available or explicitly degraded with a
   reason.
3. Download diagnostics and confirm they contain no entity IDs, raw states,
   token, coordinates, names, or household history.
4. Check **Settings → System → Repairs** and the Home Assistant logs for setup,
   reload, migration, or custom-component errors.
5. Reload the config entry once and restart Home Assistant once. Repeat the
   entity, duplicate, availability, Repairs, and log checks.
6. Confirm the integration registered no services, delivered no notification,
   and changed no window, blind, HVAC, or other actuator.
7. Confirm `v4.17_pre` remains available and operational. Only then record the
   shadow start time in UTC and the end after four consecutive calendar days.

## Roll back

1. Stop the shadow observation and capture redacted diagnostics and errors.
2. Remove the Window Climate Advisor config entry from
   **Settings → Devices & services**.
3. In HACS, remove the Window Climate Advisor repository download and restart
   Home Assistant once.
4. Confirm the custom integration and its entities are absent, Repairs/logs are
   clean, and `v4.17_pre` remains available and operational.
5. Restore `pre-window-climate-advisor-0.1.0b1` only if normal removal does not
   return Home Assistant to the verified baseline.

For a later candidate, HACS **Redownload** may select the last verified version;
the first candidate has no earlier integration version, so its rollback is
complete removal while retaining `v4.17_pre`.
