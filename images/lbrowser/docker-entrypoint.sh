#!/bin/sh
set -eu

if [ "${1:-}" = "serve" ]; then
    node /usr/local/lib/lbrowser/cdp-proxy.mjs &
    exec /opt/apps/lbrowser/lbrowser \
        --headless=new \
        --no-sandbox \
        --disable-dev-shm-usage \
        --remote-allow-origins='*' \
        --remote-debugging-address=127.0.0.1 \
        --remote-debugging-port="${CDP_UPSTREAM_PORT:-9223}" \
        --user-data-dir="${LBROWSER_USER_DATA_DIR:-/tmp/lbrowser-profile}" \
        about:blank
fi

exec "$@"
