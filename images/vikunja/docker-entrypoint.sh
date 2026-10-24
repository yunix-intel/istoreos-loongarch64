#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /app/vikunja/files /db
chown -R vikunja:vikunja /app/vikunja/files /db

JWT_FILE=/db/jwt.secret
if [ -n "${VIKUNJA_SERVICE_JWTSECRET:-}" ]; then
    JWT="$VIKUNJA_SERVICE_JWTSECRET"
elif [ -s "$JWT_FILE" ]; then
    JWT="$(cat "$JWT_FILE")"
else
    JWT="$(head -c 64 /dev/urandom | base64 | tr -d '\n')"
    printf '%s\n' "$JWT" > "$JWT_FILE"
    chmod 600 "$JWT_FILE"
fi
chown vikunja:vikunja "$JWT_FILE" 2>/dev/null || true

cd /app/vikunja
exec runuser -u vikunja -- env \
    VIKUNJA_SERVICE_ROOTPATH="${VIKUNJA_SERVICE_ROOTPATH:-/app/vikunja/}" \
    VIKUNJA_DATABASE_TYPE="${VIKUNJA_DATABASE_TYPE:-sqlite}" \
    VIKUNJA_DATABASE_PATH="${VIKUNJA_DATABASE_PATH:-/db/vikunja.db}" \
    VIKUNJA_SERVICE_INTERFACE="${VIKUNJA_SERVICE_INTERFACE:-0.0.0.0:3456}" \
    VIKUNJA_SERVICE_SECRET="$JWT" \
    VIKUNJA_SERVICE_PUBLICURL="${VIKUNJA_SERVICE_PUBLICURL:-http://localhost:3456/}" \
    /app/vikunja/vikunja
