# Migration From Legacy Flask

The Flask implementation has been preserved under `legacy/flask`.

## What moved

- Legacy Flask app package: `legacy/flask/steam_hour_booster`
- Legacy Flask launcher: `legacy/flask/main.py`
- Legacy Flask tests: `legacy/flask/tests`
- Legacy lightweight migrations: `legacy/flask/migrations`
- Legacy screenshots and README: `legacy/flask/screenshots`, `legacy/flask/README.md`

## Migration principles

1. Do not delete legacy code until SaaS 2.0 is validated in Docker Compose.
2. Do not migrate reversible user passwords. Users should reset passwords or be recreated through the new auth flow.
3. Do not migrate Steam credentials without explicit user re-consent.
4. Preserve only non-sensitive records when importing legacy data.
5. Keep the new product focused on transparent sessions, visible logs, manual controls, and no platform-circumvention behavior.

## Suggested data path

1. Export legacy users without password values.
2. Invite users to set a new password in SaaS 2.0.
3. Ask users to reconnect Steam accounts through the new account form.
4. Re-sync games through the Steam API service abstraction.
5. Keep legacy SQLite backups encrypted and time-limited.

## Operational checklist

- Confirm `docker compose up --build` works.
- Confirm admin seed can log in.
- Confirm test mode account add/login/session flow works.
- Review audit logs for admin overrides.
- Confirm no credentials or Steam Guard codes appear in logs.
