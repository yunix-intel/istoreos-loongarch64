#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p "$HERMES_WEBUI_STATE_DIR" "$HERMES_HOME" "${HERMES_WEBUI_DEFAULT_WORKSPACE:-/workspace}"
chown -R hermes:hermes "$HERMES_HOME" /workspace

gateway_pid=""
webui_pid=""

cleanup() {
    local exit_code=$?
    for pid in "$webui_pid" "$gateway_pid"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
    exit "$exit_code"
}
trap cleanup INT TERM EXIT

runuser -u hermes -- hermes gateway run &
gateway_pid=$!

(
    cd "${HERMES_WEBUI_AGENT_DIR:-/workspace}"
    exec runuser -u hermes -- python3 "$HERMES_WEBUI_DIR/server.py"
) &
webui_pid=$!

wait -n "$gateway_pid" "$webui_pid"
