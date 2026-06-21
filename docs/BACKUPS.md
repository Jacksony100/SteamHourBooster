# Backups & Restore

PostgreSQL is the source of truth. Redis holds only ephemeral rate-limit and
session-runtime state and does not need backup.

## Scheduled logical backup
Run a nightly `pg_dump` against the `postgres` service and retain N days. Example
cron entry on the host (compose stack running):

```bash
# /etc/cron.d/deckpilot-backup  (02:15 daily, keep 14 days)
15 2 * * * root docker compose -f /srv/deckpilot/docker-compose.yml exec -T postgres \
  pg_dump -U deckpilot deckpilot | gzip > /backups/deckpilot-$(date +\%F).sql.gz && \
  find /backups -name 'deckpilot-*.sql.gz' -mtime +14 -delete
```

Encrypt backups at rest (e.g. `gpg --encrypt`) and ship them off-host (S3/GCS).
Never store dumps in the repo.

## Restore
```bash
gunzip -c /backups/deckpilot-YYYY-MM-DD.sql.gz | \
  docker compose exec -T postgres psql -U deckpilot -d deckpilot
docker compose exec api alembic upgrade head   # ensure schema head after restore
```

## Restore rehearsal (do this before launch — currently NOT yet rehearsed)
1. Spin up a throwaway Postgres (`docker run --rm -e POSTGRES_PASSWORD=x -p 5433:5432 postgres:16-alpine`).
2. Restore the latest dump into it.
3. Point a scratch API at it (`DATABASE_URL=...:5433/...`) and run `alembic upgrade head` + smoke checks.
4. Record the date + duration of the drill here.

| Date | Dump tested | Duration | Result |
|---|---|---|---|
| (pending) | | | |

## What is automated vs manual
- **Automated:** none yet in-stack — the cron above is the recommended operator setup.
- **Manual:** restore + rehearsal. Wiring a backup sidecar container is a future task.
