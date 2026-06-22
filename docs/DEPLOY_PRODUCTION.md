# Production deploy — deckpilot.ru (real SSL)

Two facts that shape this:
1. The **backend (FastAPI + Postgres + Redis + worker) cannot run on Vercel** — it needs a
   real host. Vercel only runs the Next.js frontend.
2. `deckpilot.ru` currently points its DNS at **Vercel**.

So pick ONE of the two paths below.

---

## Path A — One VPS, full stack, automatic SSL (recommended)

Everything (web + api + db + redis + worker) on a single Ubuntu server behind **Caddy**,
which obtains and renews a **Let's Encrypt** certificate automatically. No manual
`certbot`, no Vercel needed.

### 1. Server
- Any Ubuntu 22.04+ VPS with a public IP. Open ports **80** and **443** (and 22 for SSH).
- Install Docker + Compose:
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```

### 2. DNS
Point the domain at the VPS (replace the Vercel records):
```
A   deckpilot.ru        -> <VPS_PUBLIC_IP>
A   www.deckpilot.ru    -> <VPS_PUBLIC_IP>   (optional)
```
Wait for it to propagate (`dig deckpilot.ru` shows the VPS IP).

### 3. Configure + run
```bash
git clone <repo> deckpilot && cd deckpilot
cp .env.production.example .env
# Generate secrets and fill .env:
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))"
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
# set DOMAIN=deckpilot.ru, ACME_EMAIL, POSTGRES_PASSWORD, ADMIN_PASSWORD (>=12), DEMO_PASSWORD

docker compose -f docker-compose.prod.yml up -d --build
```
Caddy issues the certificate on first request to `https://deckpilot.ru`. Done.

### 4. Verify
```bash
curl -I https://deckpilot.ru                 # 200, valid cert
docker compose -f docker-compose.prod.yml ps # all healthy
docker compose -f docker-compose.prod.yml logs -f caddy   # cert issuance
```

### Updating
```bash
git pull && docker compose -f docker-compose.prod.yml up -d --build
```
Migrations run automatically on the api container start.

---

## Path B — Frontend on Vercel + backend on a host

- **Frontend:** deploy `apps/web` to your Vercel project (`web`). Vercel auto-issues SSL
  for `deckpilot.ru` once the domain is attached in the project's Domains tab.
- **Backend:** still needs a host (a VPS with Path A's compose minus the `web`/`caddy`
  services, or Railway/Render/Fly) reachable at e.g. `https://api.deckpilot.ru`.
- **Wire them:** in the Vercel project, set a rewrite so `/api/*` proxies to the backend,
  or set `INTERNAL_API_ORIGIN`/`INTERNAL_API_URL` env to the backend and adjust
  `next.config.mjs` (which currently disables `/api` rewrites on Vercel).

Path B is more moving parts; Path A is the simplest route to "real SSL + working app".

---

## Notes
- `ALLOW_DEMO_MODE_IN_PRODUCTION=true` is set because the app ships in transparent **demo**
  Steam mode. To run **real** owner-operated idle sessions, set the official+real flags
  (see `docs/REAL_SESSIONS.md`) — and read the risk section first.
- `BILLING_PROVIDER=mock` disables paid checkout in prod. Set `coinbase` + keys for real.
- Backups: see `docs/BACKUPS.md` (scheduled `pg_dump` + restore rehearsal).
