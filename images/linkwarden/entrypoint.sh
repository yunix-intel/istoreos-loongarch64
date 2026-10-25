#!/bin/bash
# Linkwarden all-in-one entrypoint: migrate, then run Next.js + worker.
set -euo pipefail

LINKWARDEN_UID="${LINKWARDEN_UID:-1118}"
LINKWARDEN_GID="${LINKWARDEN_GID:-1118}"
PORT="${PORT:-3000}"
DATA_ROOT="/data/data"

log() { echo "[entrypoint] $*"; }

if [ -z "${DATABASE_URL:-}" ]; then
    echo "[entrypoint] ERROR: DATABASE_URL is required" >&2
    exit 1
fi
if [ -z "${NEXTAUTH_URL:-}" ]; then
    echo "[entrypoint] ERROR: NEXTAUTH_URL is required, e.g." >&2
    echo "  docker run -e NEXTAUTH_URL=http://<host>:3000/api/v1/auth ..." >&2
    exit 1
fi
export NEXTAUTH_URL="${NEXTAUTH_URL%/}"
export NEXTAUTH_URL_INTERNAL="${NEXTAUTH_URL_INTERNAL:-http://127.0.0.1:${PORT}}"

# No bundled Chromium. With no browser endpoint configured, preservation is
# disabled so bookmark CRUD still works instead of a crash-looping worker.
if [ -z "${PLAYWRIGHT_WS_URL:-}" ] && \
   [ -z "${PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH:-}" ] && \
   [ -z "${DISABLE_BROWSER:-}" ] && \
   [ -z "${DISABLE_PRESERVATION:-}" ]; then
    export DISABLE_BROWSER=true
    log "No browser configured; setting DISABLE_BROWSER=true (bookmark CRUD only)"
fi
export STORAGE_FOLDER="${STORAGE_FOLDER:-data}"
export NODE_ENV="${NODE_ENV:-production}"
export HOME="${HOME:-/data}"

mkdir -p "$DATA_ROOT"
chown "$LINKWARDEN_UID:$LINKWARDEN_GID" "$DATA_ROOT"
chown -R "$LINKWARDEN_UID:$LINKWARDEN_GID" "$DATA_ROOT"

SECRET_FILE="$DATA_ROOT/.nextauth_secret"
if [ -n "${NEXTAUTH_SECRET:-}" ]; then
    log "Using NEXTAUTH_SECRET from the environment"
elif [ -s "$SECRET_FILE" ]; then
    NEXTAUTH_SECRET="$(cat "$SECRET_FILE")"
    log "Loaded NEXTAUTH_SECRET from $SECRET_FILE"
else
    NEXTAUTH_SECRET="$(head -c 48 /dev/urandom | base64 | tr -d '\n')"
    umask 077
    printf '%s' "$NEXTAUTH_SECRET" > "$SECRET_FILE"
    umask 022
    log "Generated persistent NEXTAUTH_SECRET in $SECRET_FILE"
fi
export NEXTAUTH_SECRET
if [ -f "$SECRET_FILE" ]; then
    chown "$LINKWARDEN_UID:$LINKWARDEN_GID" "$SECRET_FILE"
    chmod 0600 "$SECRET_FILE"
fi

run_as_linkwarden() {
    setpriv --reuid="$LINKWARDEN_UID" --regid="$LINKWARDEN_GID" \
        --clear-groups -- "$@"
}

log "Applying database migrations"
PRISMA_MIGRATIONS_DIR=/data/packages/prisma/migrations \
    run_as_linkwarden node /data/scripts/prisma-migrate.mjs

log "Starting web on 0.0.0.0:${PORT}"
cd /data/apps/web
run_as_linkwarden node /data/node_modules/next/dist/bin/next start &
WEB_PID=$!

log "Starting worker"
cd /data/apps/worker
run_as_linkwarden node /data/node_modules/tsx/dist/cli.mjs worker.ts &
WORKER_PID=$!

shutdown() {
    trap - TERM INT
    log "Stopping web and worker"
    kill -TERM "$WEB_PID" "$WORKER_PID" 2>/dev/null || true
    wait "$WEB_PID" "$WORKER_PID" 2>/dev/null || true
    exit 0
}
trap shutdown TERM INT

set +e
wait -n "$WEB_PID" "$WORKER_PID"
STATUS=$?
set -e
log "A process exited with status $STATUS; stopping the other"
kill -TERM "$WEB_PID" "$WORKER_PID" 2>/dev/null || true
wait "$WEB_PID" "$WORKER_PID" 2>/dev/null || true
exit "$STATUS"
