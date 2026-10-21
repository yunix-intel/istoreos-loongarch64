#!/usr/bin/env bash
set -Eeuo pipefail

MEMORY="${MEMCACHED_MEMORY:-64}"
PORT="${MEMCACHED_PORT:-11211}"
MAX_CONN="${MEMCACHED_MAX_CONN:-1024}"
THREADS="${MEMCACHED_THREADS:-4}"

if [ "$#" -eq 0 ]; then
    set -- memcached \
        -m "$MEMORY" -p "$PORT" -l 0.0.0.0 \
        -u memcached -c "$MAX_CONN" -t "$THREADS" -o modern
fi

exec "$@"
