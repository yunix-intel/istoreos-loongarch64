#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p "${DATA_DIR:-/app/data}"
chown -R abc:abc "${DATA_DIR:-/app/data}" /app

exec runuser -u abc -- /usr/local/bin/mealie "$@"
