# Vercel Deployment

Deployment date: 2026-06-16

Project:

- Vercel project: `web`
- Project ID: `prj_EhBtxkGdRrgce26GO8iOrib5A8pN`
- Team/Org ID: `team_qC0z6kh0cFSZNzh5xdDHYHX0`

Production URLs:

- `https://deckpilot.ru`
- `https://web-jade-mu-90.vercel.app`
- `https://web-jacksony692-6493s-projects.vercel.app`
- Deployment URL: `https://web-ml6wtttjh-jacksony692-6493s-projects.vercel.app`

Deployment:

- ID: `dpl_4yBwKn8xPhNstpNQes6rDtDqFSfv`
- Status: `READY`
- Target: `production`

Verification:

- Public GET to `https://deckpilot.ru` returned `200`.
- Public GET to `https://web-jade-mu-90.vercel.app` returned `200`.
- HTML title is `DeckPilot`.
- Vercel SSO deployment protection was disabled for this project so the production URL is publicly reachable.

Current limitation:

This is the Next.js frontend deployment. The FastAPI API, PostgreSQL, Redis, and worker still need to be deployed on a server/container platform or exposed behind a production API URL.

When the API is deployed, set these Vercel environment variables:

```env
NEXT_PUBLIC_API_BASE_PATH=/api/v1
INTERNAL_API_ORIGIN=https://api.your-domain.example
INTERNAL_API_URL=https://api.your-domain.example/api/v1
```
