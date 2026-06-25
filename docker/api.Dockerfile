# --- builder: compile deps into an isolated venv (build tools stay out of runtime) ---
FROM python:3.12-slim AS builder
WORKDIR /srv/api
RUN printf 'Acquire::ForceIPv4 "true";
' > /etc/apt/apt.conf.d/99ipv4 && apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- runtime: slim, no build tools, non-root user ---
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/srv/api \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /srv/api
COPY --from=builder /opt/venv /opt/venv
RUN useradd --create-home --uid 10001 appuser
COPY apps/api .
RUN chown -R appuser:appuser /srv/api
USER appuser
EXPOSE 8000
