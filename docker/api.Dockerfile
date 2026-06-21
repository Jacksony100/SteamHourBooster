FROM python:3.12-slim

WORKDIR /srv/api
ENV PYTHONPATH=/srv/api

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api .

EXPOSE 8000
