# Standalone API image (compose uses docker/api.Dockerfile; this mirrors it).
# --- builder ---
FROM python:3.12-slim AS builder
WORKDIR /srv/api
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- runtime (non-root) ---
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
CMD ["sh", "-c", "python -m alembic upgrade head && python -m app.seed && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
