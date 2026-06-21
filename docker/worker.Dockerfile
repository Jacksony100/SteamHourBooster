FROM python:3.12-slim

WORKDIR /srv
ENV PYTHONPATH=/srv/api

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /srv/api/requirements.txt
RUN pip install --no-cache-dir -r /srv/api/requirements.txt

COPY apps/api /srv/api
COPY apps/worker /srv/worker
WORKDIR /srv/worker
