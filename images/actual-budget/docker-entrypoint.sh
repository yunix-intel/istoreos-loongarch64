#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p "${ACTUAL_DATA_DIR:-/data}"
chown actual:actual "${ACTUAL_DATA_DIR:-/data}"

if [ "$#" -eq 0 ]; then
    set -- actual-server
fi

exec runuser -u actual -- "$@"
