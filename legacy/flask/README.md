# Steam Hour Booster

Legacy Flask project refactored into a safer modular backend.

This repository is now structured as a Flask application package. The current goal is to keep the existing product routes working while separating auth, accounts, games, billing, admin, database, and security concerns.

## Safety scope

This project must only be used as a transparent account/session manager for Steam accounts owned by the user.

Do not build or add:

- anti-detect behavior;
- ban bypass or ban evasion;
- Steam Guard bypass;
- proxy/fingerprint evasion;
- mass spam automation;
- hidden activity controls.

## Project structure

```text
steam_hour_booster/
  app.py
  config.py
  db.py
  extensions.py
  security/
  auth/
  accounts/
  games/
  billing/
  admin/
  templates/
  static/
migrations/
tests/
docs/
main.py
```

## Configuration

Copy the example environment file and fill in real values:

```bash
cp .env.example .env
```

Generate an encryption key:

```bash
python generate_key.py
```

Use the printed value as `ENCRYPTION_KEY`.

Required environment variables:

- `SECRET_KEY`: stable Flask session secret.
- `DATABASE_URL`: SQLite URL, for example `sqlite:///steam_accounts.db`.
- `STEAM_API_KEY`: Steam Web API key.
- `ENCRYPTION_KEY`: Fernet key for Steam credential encryption.
- `COINBASE_API_KEY`: optional Coinbase Commerce key.
- `COINBASE_WEBHOOK_SECRET`: reserved for webhook verification.
- `APP_BASE_URL`: public app URL.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The lightweight migration manager runs SQL files from `migrations/` during app startup.

## Tests

```bash
python -m pytest
```

Current tests cover:

- registration;
- login;
- subscription guard;
- add account;
- user cannot access another user's account;
- admin guard.

## Premium UI

The Flask templates now share a dark-first SaaS design system in `steam_hour_booster/static/css/app.css`.

Updated screens:

- `/login`: premium auth screen with brand and trust blocks.
- `/register`: onboarding with password and safety guidance.
- `/no_subscription`: pricing cards, CTA, and comparison table.
- `/buy_subscription`: Week, Month, 3 Months, 6 Months, and Lifetime checkout cards.
- `/`: dashboard shell with sidebar, topbar, metrics, account grid, selected account panel, active sessions, ban status, activity log, modals, toasts, and skeleton states.
- `/admin`: admin stats, filters, users table, subscription controls, ban/admin toggles, last seen/IP.

Frontend assets:

- `steam_hour_booster/static/css/app.css`: design system, layout, cards, forms, badges, tables, modals, toasts, responsive rules.
- `steam_hour_booster/static/js/app.js`: shared helpers, API wrapper, modal/toast/confirm handling, error boundary.
- `steam_hour_booster/static/js/i18n.js`: theme and language persistence via `localStorage`.
- `steam_hour_booster/static/js/accounts.js`: dashboard account actions using the existing backend endpoints.
- `steam_hour_booster/static/js/admin.js`: admin table stats and local filters.

## Security notes

- App user passwords are hashed with Werkzeug password hashing.
- Steam account credentials are encrypted via `steam_hour_booster.security.encryption_service`.
- TLS verification is not disabled.
- Secrets are not logged.
- `SECRET_KEY` is loaded from configuration instead of being regenerated at every start.
- CSRF support exists behind `CSRF_ENABLED=1`, but the legacy frontend still needs token wiring before enforcement can be enabled by default.
