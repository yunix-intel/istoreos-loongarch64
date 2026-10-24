#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /data /config /cache
chown -R backrest:backrest /data /config /cache

exec runuser -u backrest -- env \
    BACKREST_DATA=/data \
    BACKREST_CONFIG=/config/config.json \
    BACKREST_PORT="${BACKREST_PORT:-0.0.0.0:9898}" \
    BACKREST_RESTIC_COMMAND=/usr/local/bin/restic \
    XDG_CACHE_HOME=/cache \
    TMPDIR=/tmp \
    /usr/local/bin/backrest
