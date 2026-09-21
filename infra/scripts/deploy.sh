#!/usr/bin/env bash
# ==============================================================================
# Bantay Pondo — Single-EC2 Production Deployment Script
# ==============================================================================
set -euo pipefail

COMPOSE_FILE="infra/docker-compose.prod.yml"
ENV_FILE=".env.prod"

echo "=== Bantay Pondo Production Deployment ==="

# Check environment file
if [ ! -f "${ENV_FILE}" ]; then
    echo "ERROR: Environment file ${ENV_FILE} does not exist!"
    echo "Please copy .env.prod.example to ${ENV_FILE} and configure required secrets."
    exit 1
fi

echo "--> Pulling base images..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull db redis certbot prometheus || true

echo "--> Building application images..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" build api

echo "--> Ensuring database and redis services are healthy..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d db redis

# Wait for DB to be healthy
echo "--> Waiting for PostgreSQL+PostGIS to be ready..."
until docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec db pg_isready; do
    echo "Waiting for postgres..."
    sleep 2
done

echo "--> Running Alembic database migrations..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" run --rm api alembic upgrade head

echo "--> Launching API, Nginx reverse proxy, Certbot, and Prometheus..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --remove-orphans

echo "--> Verifying service health..."
sleep 5
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

echo "--> Testing liveness and readiness probes..."
curl -f http://localhost/healthz || { echo "Healthz check failed!"; exit 1; }
curl -f http://localhost/readyz || { echo "Readyz check failed!"; exit 1; }

echo "=== Deployment completed successfully! ==="
