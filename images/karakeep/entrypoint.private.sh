#!/bin/bash
# Private single-container entrypoint for Karakeep + embedded LBrowser.
#
# Start headless LBrowser (127.0.0.1:9223), start the CDP proxy (127.0.0.1:9222),
# then run the distribution's original /entrypoint.sh to migrate and start web +
# workers.  The wrapper stays PID 1 so it can clean up the browser and proxy on
# shutdown; signals are forwarded to /entrypoint.sh, which keeps owning the
# app/worker lifecycle.
set -euo pipefail

log() { echo "[private-entrypoint] $*"; }

BROWSER_BIN=/opt/apps/lbrowser/lbrowser
PROXY_JS=/usr/local/lib/lbrowser/cdp-proxy.mjs
PROFILE_DIR="${LBROWSER_USER_DATA_DIR:-/tmp/lbrowser-profile}"
BROWSER_LOG="${LBROWSER_LOG:-/tmp/lbrowser.log}"
PROXY_LOG="${CDP_PROXY_LOG:-/tmp/cdp-proxy.log}"

CDP_UPSTREAM_HOST="${CDP_UPSTREAM_HOST:-127.0.0.1}"
CDP_UPSTREAM_PORT="${CDP_UPSTREAM_PORT:-9223}"
CDP_LISTEN_HOST="${CDP_LISTEN_HOST:-127.0.0.1}"
CDP_LISTEN_PORT="${CDP_LISTEN_PORT:-9222}"
export CDP_UPSTREAM_HOST CDP_UPSTREAM_PORT CDP_LISTEN_HOST CDP_LISTEN_PORT

BROWSER_PID=""
PROXY_PID=""
APP_PID=""

# Kill a child, giving it a grace period before SIGKILL.
stop_child() {
    local pid="${1:-}"
    local name="${2:-child}"
    [ -n "$pid" ] || return 0
    if ! kill -0 "$pid" 2>/dev/null; then
        wait "$pid" 2>/dev/null || true
        return 0
    fi
    log "Stopping ${name} (pid ${pid})"
    kill -TERM "$pid" 2>/dev/null || true
    for _ in $(seq 1 50); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.1
    done
    if kill -0 "$pid" 2>/dev/null; then
        log "${name} did not exit; sending SIGKILL"
        kill -KILL "$pid" 2>/dev/null || true
    fi
    wait "$pid" 2>/dev/null || true
}

cleanup() {
    local status=$?
    trap - EXIT TERM INT
    if [ -n "$APP_PID" ] && kill -0 "$APP_PID" 2>/dev/null; then
        log "Forwarding shutdown to /entrypoint.sh (pid ${APP_PID})"
        kill -TERM "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
    stop_child "$PROXY_PID" "CDP proxy"
    stop_child "$BROWSER_PID" "LBrowser"
    log "Cleanup done (exit ${status})"
    exit "$status"
}
trap cleanup EXIT
# A requested stop is a clean shutdown: cleanup forwards TERM to the app and
# reaps the browser/proxy, so report success like the distribution entrypoint.
trap 'exit 0' TERM
trap 'exit 130' INT

# $1 = URL to probe, $2 = label, $3 = pid that must stay alive.
wait_for_http() {
    local url="$1" label="$2" pid="$3"
    for _ in $(seq 1 120); do
        if curl -fsS --max-time 1 "$url" >/dev/null 2>&1; then
            log "${label} is ready at ${url}"
            return 0
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            log "${label} exited before becoming ready"
            return 1
        fi
        sleep 0.5
    done
    log "${label} did not become ready at ${url} within 60s"
    return 1
}

if [ ! -x "$BROWSER_BIN" ]; then
    log "ERROR: ${BROWSER_BIN} is missing or not executable"
    exit 1
fi

mkdir -p "$PROFILE_DIR"

log "Starting headless LBrowser on ${CDP_UPSTREAM_HOST}:${CDP_UPSTREAM_PORT}"
"$BROWSER_BIN" \
    --headless=new \
    --remote-debugging-port="$CDP_UPSTREAM_PORT" \
    --remote-debugging-address="$CDP_UPSTREAM_HOST" \
    --remote-allow-origins='*' \
    --no-sandbox \
    --disable-dev-shm-usage \
    --user-data-dir="$PROFILE_DIR" \
    about:blank >"$BROWSER_LOG" 2>&1 &
BROWSER_PID=$!

if ! wait_for_http "http://${CDP_UPSTREAM_HOST}:${CDP_UPSTREAM_PORT}/json/version" "LBrowser" "$BROWSER_PID"; then
    tail -n 50 "$BROWSER_LOG" >&2 || true
    exit 1
fi

log "Starting CDP proxy on ${CDP_LISTEN_HOST}:${CDP_LISTEN_PORT} -> ${CDP_UPSTREAM_HOST}:${CDP_UPSTREAM_PORT}"
node "$PROXY_JS" >"$PROXY_LOG" 2>&1 &
PROXY_PID=$!

if ! wait_for_http "http://${CDP_LISTEN_HOST}:${CDP_LISTEN_PORT}/json/version" "CDP proxy" "$PROXY_PID"; then
    tail -n 50 "$PROXY_LOG" >&2 || true
    exit 1
fi

export BROWSER_WEB_URL="http://127.0.0.1:${CDP_LISTEN_PORT}"
log "BROWSER_WEB_URL=${BROWSER_WEB_URL}"

# Do not exec: PID 1 must stay alive to reap LBrowser and the proxy.  The
# original entrypoint still runs in the foreground and receives the signals.
/entrypoint.sh "$@" &
APP_PID=$!
log "Handed off to /entrypoint.sh (pid ${APP_PID})"

set +e
wait "$APP_PID"
STATUS=$?
set -e
log "/entrypoint.sh exited with status ${STATUS}"
exit "$STATUS"
