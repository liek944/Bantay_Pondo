#!/usr/bin/env bash
# ==============================================================================
# Bantay Pondo — Let's Encrypt SSL Bootstrap Script for Single-EC2 Deployment
# ==============================================================================
set -euo pipefail

DOMAINS=("bantaypondo.ph" "www.bantaypondo.ph")
PRIMARY_DOMAIN="${DOMAINS[0]}"
EMAIL="${SSL_EMAIL:-admin@bantaypondo.ph}"
STAGING="${SSL_STAGING:-0}" # Set to 1 for testing against Let's Encrypt staging
DATA_PATH="./infra"

echo "=== Initializing Let's Encrypt SSL certificates for ${DOMAINS[*]} ==="

# Ensure directory structures exist
mkdir -p "${DATA_PATH}/certbot/conf/live/${PRIMARY_DOMAIN}"
mkdir -p "${DATA_PATH}/certbot/www"

LIVE_CERT_PATH="${DATA_PATH}/certbot/conf/live/${PRIMARY_DOMAIN}"

# Step 1: Create self-signed dummy certificate if none exists so Nginx can start
if [ ! -f "${LIVE_CERT_PATH}/fullchain.pem" ]; then
    echo "--> No existing certificate found. Generating dummy certificate for ${PRIMARY_DOMAIN}..."
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "${LIVE_CERT_PATH}/privkey.pem" \
        -out "${LIVE_CERT_PATH}/fullchain.pem" \
        -subj "/CN=localhost"
    echo "--> Dummy certificate created."
fi

# Step 2: Start Nginx to serve ACME challenge
echo "--> Starting Nginx service..."
docker compose -f infra/docker-compose.prod.yml up -d nginx

# Step 3: Request real Let's Encrypt certificates
echo "--> Requesting certificates from Let's Encrypt..."
DOMAIN_ARGS=""
for DOMAIN in "${DOMAINS[@]}"; do
    DOMAIN_ARGS="${DOMAIN_ARGS} -d ${DOMAIN}"
done

STAGING_ARG=""
if [ "${STAGING}" != "0" ]; then
    STAGING_ARG="--staging"
fi

docker compose -f infra/docker-compose.prod.yml run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
    ${STAGING_ARG} \
    ${DOMAIN_ARGS} \
    --email ${EMAIL} \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot

# Step 4: Reload Nginx with real certificates
echo "--> Reloading Nginx with production SSL certificates..."
docker compose -f infra/docker-compose.prod.yml exec nginx nginx -s reload

echo "=== SSL bootstrap completed successfully! ==="
