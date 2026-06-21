# --- builder: compile deps into an isolated venv ---
FROM python:3.12-slim AS builder
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY apps/api/requirements.txt /srv/api/requirements.txt
RUN pip install --no-cache-dir -r /srv/api/requirements.txt

# --- runtime: slim, no build tools, non-root user ---
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/srv/api \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /srv
COPY --from=builder /opt/venv /opt/venv
RUN useradd --create-home --uid 10001 appuser
COPY apps/api /srv/api
COPY apps/worker /srv/worker
RUN chown -R appuser:appuser /srv
USER appuser
WORKDIR /srv/worker
