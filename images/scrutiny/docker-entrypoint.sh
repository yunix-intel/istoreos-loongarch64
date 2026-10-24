#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /opt/scrutiny/config
chown -R scrutiny:scrutiny /opt/scrutiny/config

export SCRUTINY_WEB_LISTEN_HOST="${SCRUTINY_WEB_LISTEN_HOST:-0.0.0.0}"
export SCRUTINY_WEB_LISTEN_PORT="${SCRUTINY_WEB_LISTEN_PORT:-8080}"
export SCRUTINY_WEB_SRC_FRONTEND_PATH="${SCRUTINY_WEB_SRC_FRONTEND_PATH:-/opt/scrutiny/web}"
export SCRUTINY_WEB_DATABASE_LOCATION="${SCRUTINY_WEB_DATABASE_LOCATION:-/opt/scrutiny/config/scrutiny.db}"
export COLLECTOR_API_ENDPOINT="${COLLECTOR_API_ENDPOINT:-http://127.0.0.1:8080}"
export COLLECTOR_HOST_ID="${COLLECTOR_HOST_ID:-scrutiny}"

pids=()
cleanup() {
    for pid in "${pids[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

runuser -u scrutiny -- /opt/scrutiny/bin/scrutiny-web start &
pids+=($!)

(
    sleep 5
    while true; do
        runuser -u scrutiny -- env \
            COLLECTOR_API_ENDPOINT="$COLLECTOR_API_ENDPOINT" \
            COLLECTOR_HOST_ID="$COLLECTOR_HOST_ID" \
            /opt/scrutiny/bin/scrutiny-collector-metrics run || true
        sleep "${COLLECTOR_INTERVAL:-3600}"
    done
) &
pids+=($!)

wait -n "${pids[@]}"
