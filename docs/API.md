# API Documentation

FastAPI serves interactive OpenAPI documentation at:

- Local Docker: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Operational endpoints:

- `GET /healthz`
- `GET /readyz`
- `GET /health/live`
- `GET /health/ready`

## Main route groups

- `/api/v1/auth`: register, login, logout, current user, CSRF token, password reset, email verification, active web sessions, data export, account deletion.
- `/api/v1/dashboard`: overview metrics and recent activity.
- `/api/v1/steam-accounts`: add, list, login/logout, delete, ban info.
- `/api/v1/games`: fetch owned games, search/filter, save selection.
- `/api/v1/sessions`: idempotent start/stop transparent activity sessions, events, compatibility logs.
- `/api/v1/billing`: plans, current subscription, payment history, checkout, verified webhooks.
- `/api/v1/admin`: overview, paginated users, user detail, subscription grant/extend/cancel, force-stop sessions, role/ban controls, payments, subscription changes, audit logs.
- `/api/v1/system/mode`: environment, billing provider, demo/official Steam mode, and whether official Steam linking is configured.

Public web trust pages:

- `/terms`
- `/privacy`
- `/security`
- `/status`

## Steam integration modes

- `STEAM_INTEGRATION_MODE=demo`: account/session behavior is simulated and clearly labeled. Steam passwords are not required.
- `STEAM_INTEGRATION_MODE=official`: password-based linking is disabled. If official Steam/OpenID/Web API linking is not configured, account, game, ban, and session actions fail closed with a controlled unavailable response.

## Admin routes

- `GET /api/v1/admin/overview`
- `GET /api/v1/admin/users?query=&filter=&page=&page_size=`
- `GET /api/v1/admin/users/{user_id}`
- `PATCH /api/v1/admin/users/{user_id}`
- `PATCH /api/v1/admin/users/{user_id}/subscription`
- `POST /api/v1/admin/users/{user_id}/force-logout-sessions`
- `GET /api/v1/admin/audit`
- `GET /api/v1/admin/payments`
- `GET /api/v1/admin/subscription-changes`

## Account security routes

- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`
- `POST /api/v1/auth/email-verification/request`
- `POST /api/v1/auth/email-verification/confirm`
- `GET /api/v1/auth/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`
- `GET /api/v1/auth/export`
- `DELETE /api/v1/auth/account`

Password reset and email verification responses never expose raw stored token hashes or credentials. Production deployments should connect these token issuers to a real transactional email provider before public launch.

## Security model

- Session is stored in an HTTP-only cookie.
- Session cookies are backed by revocable `user_sessions` rows.
- CSRF token is stored in a readable cookie and must be sent in `X-CSRF-Token` for unsafe authenticated methods.
- Passwords are hashed with passlib/bcrypt.
- Demo mode does not require Steam passwords. Any legacy/test compatibility credentials are encrypted through Fernet with validated `ENCRYPTION_KEY` and are rejected in production password-based flows.
- Ownership is checked in account, games, ban, and session endpoints.
- Admin actions write audit logs.
