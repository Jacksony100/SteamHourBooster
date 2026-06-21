# DeckPilot - SaaS 2.0 Implementation Plan

## Goals

Build a new product shell beside the legacy Flask app:

- `apps/web`: Next.js 15 App Router, TypeScript, TailwindCSS, shadcn-style UI primitives, Framer Motion.
- `apps/api`: FastAPI, PostgreSQL, SQLAlchemy, Alembic, secure cookie auth.
- `apps/worker`: Redis-backed worker for transparent session lifecycle jobs.
- `packages/shared`: shared product constants and TypeScript contracts.
- `docker`: Dockerfiles and compose-ready runtime.

## Safety boundaries

This product is a transparent account/session manager for user-owned Steam accounts only.

The implementation must not include platform-rule circumvention, account-risk evasion, Steam Guard circumvention, network-routing evasion, fingerprinting, hidden automation, mass account workflows, or attempts to sidestep Steam platform safeguards.

## Architecture phases

1. Preserve the current Flask refactor under `legacy/flask`.
2. Create FastAPI domain modules: auth, users, steam accounts, sessions, games, billing, admin, audit, integrations.
3. Add SQLAlchemy models and Alembic migrations for users, accounts, selected games, session records, billing plans/subscriptions, ban cache, and audit logs.
4. Implement cookie auth with password hashing, CSRF tokens, rate limits, ownership checks, encrypted credentials, and audit events.
5. Implement Steam integration behind service abstractions with test/mock mode enabled by default.
6. Implement worker lifecycle hooks for start/stop transparent sessions, with graceful shutdown and no unsafe platform-circumvention behavior.
7. Build the premium web app with dashboard, accounts, sessions, billing, admin, settings, command palette, skeletons, empty states, toasts, theme switcher, and language-ready strings.
8. Add Docker Compose for local development: web, api, worker, postgres, redis.
9. Add tests and GitHub Actions for lint, typecheck, tests, and build.

## Acceptance focus

- `docker compose up --build` starts the SaaS 2.0 stack.
- Web opens and can register/login.
- Seed admin user is available from env.
- Add Steam account works in mocked/test mode.
- API docs are available at `/docs`.
- Tests cover auth, ownership, admin guard, subscription guard, and mocked session service.
- No unsafe platform-circumvention logic exists.
