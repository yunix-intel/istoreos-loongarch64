#!/bin/bash
# Karakeep all-in-one entrypoint: migrate, then run web + workers without s6.
set -euo pipefail

KARAKEEP_UID="${KARAKEEP_UID:-1116}"
KARAKEEP_GID="${KARAKEEP_GID:-1116}"
DATA_DIR="${DATA_DIR:-/data}"
export DATA_DIR
export NODE_ENV="${NODE_ENV:-production}"
export HOME="${HOME:-/data}"

log() { echo "[entrypoint] $*"; }

if [ -z "${NEXTAUTH_URL:-}" ]; then
    echo "[entrypoint] ERROR: NEXTAUTH_URL is required, e.g." >&2
    echo "  docker run -e NEXTAUTH_URL=http://<host>:3000 ..." >&2
    exit 1
fi
export NEXTAUTH_URL="${NEXTAUTH_URL%/}"
export NEXTAUTH_URL_INTERNAL="${NEXTAUTH_URL_INTERNAL:-http://127.0.0.1:${PORT:-3000}}"

# The volume is mounted as root on first use. Only the data tree needs to be
# writable by the runtime user; do not recurse over an existing large library.
mkdir -p "$DATA_DIR/assets"
chown "$KARAKEEP_UID:$KARAKEEP_GID" "$DATA_DIR"
chown -R "$KARAKEEP_UID:$KARAKEEP_GID" "$DATA_DIR/assets"

SECRET_FILE="$DATA_DIR/.nextauth_secret"
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
    chown "$KARAKEEP_UID:$KARAKEEP_GID" "$SECRET_FILE"
    chmod 0600 "$SECRET_FILE"
fi

run_as_karakeep() {
    setpriv --reuid="$KARAKEEP_UID" --regid="$KARAKEEP_GID" --clear-groups -- "$@"
}

log "Running database migrations"
cd /app/db_migrations
run_as_karakeep node index.js

log "Starting web (port ${PORT:-3000}) and workers"
cd /app/apps/web
run_as_karakeep node server.js &
WEB_PID=$!

cd /app/apps/workers
run_as_karakeep node dist/index.js &
WORKERS_PID=$!

shutdown() {
    trap - TERM INT
    log "Stopping web and workers"
    kill -TERM "$WEB_PID" "$WORKERS_PID" 2>/dev/null || true
    wait "$WEB_PID" "$WORKERS_PID" 2>/dev/null || true
    exit 0
}
trap shutdown TERM INT

# Exit as soon as either process dies, then stop the sibling.
set +e
wait -n "$WEB_PID" "$WORKERS_PID"
STATUS=$?
set -e
log "A process exited with status $STATUS; stopping the other"
kill -TERM "$WEB_PID" "$WORKERS_PID" 2>/dev/null || true
wait "$WEB_PID" "$WORKERS_PID" 2>/dev/null || true
exit "$STATUS"
