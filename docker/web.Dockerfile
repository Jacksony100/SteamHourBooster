FROM node:22-alpine AS deps
ENV NODE_OPTIONS=--dns-result-order=ipv4first
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm config set maxsockets=2 fetch-retries=6 fetch-retry-mintimeout=20000 fetch-retry-maxtimeout=180000 fetch-timeout=600000 && npm ci

FROM node:22-alpine AS builder
ENV NODE_OPTIONS=--dns-result-order=ipv4first
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_OUTPUT_MODE=standalone
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
RUN npm run build

FROM node:22-alpine AS runner
ENV NODE_OPTIONS=--dns-result-order=ipv4first
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Bind the Next standalone server to all interfaces (Docker sets HOSTNAME to the
# container id, which would otherwise make 127.0.0.1 healthchecks fail).
ENV HOSTNAME=0.0.0.0
# Run as the built-in non-root "node" user.
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
