# Baseline Status (Phase A)

Captured before the beta-close-all work, on branch `fix/beta-close-all-design-steam-assets`.

## Repository state
- The entire DeckPilot 2.0 rewrite (`apps/`, `legacy/`, `docs/`, `docker/`, …) was **untracked** in git — only `main.py` existed in history. A safety-baseline commit now tracks 241 files.
- Build/db artifacts (`apps/web/.next/`, `test.db`, `DeckPilot-*.zip`) were present in the working tree but **not** tracked. `.gitignore` now excludes `*.zip` and `.design-import/` in addition to the existing `.next/`, `*.db`, `node_modules/`.

## Baseline checks (all green before changes)
| Check | Command | Result |
|---|---|---|
| API tests | `cd apps/api && pytest` | **58 passed** |
| Legacy tests | `cd legacy/flask && pytest` | **16 passed** |
| API lint | `cd apps/api && ruff check .` | clean |
| Web typecheck | `cd apps/web && npm run typecheck` | clean |
| Web lint | `cd apps/web && npm run lint` | clean |
| Migrations | `alembic upgrade head` | applies 001→005 cleanly |

## After this pass
| Check | Result |
|---|---|
| API tests | **68 passed** (58 + 10 new: Steam data, security headers) |
| API lint | clean |
| Web typecheck / lint | clean |
| Migrations | applies 001→**006** cleanly |
| Compose config | valid YAML, env merge resolves |

Environment note: the audit/QA was run with Python 3.14 locally; CI targets Python 3.12. Docker image builds were **not** run locally (no daemon); they are covered by the `docker-images` CI job.
