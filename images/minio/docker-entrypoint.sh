#!/usr/bin/env bash
set -Eeuo pipefail

if [ -z "${MINIO_ROOT_USER:-}" ] || [ -z "${MINIO_ROOT_PASSWORD:-}" ]; then
    echo >&2 "error: MINIO_ROOT_USER and MINIO_ROOT_PASSWORD are required"
    exit 1
fi

mkdir -p /data
chown minio:minio /data

if [ "$#" -eq 0 ]; then
    set -- minio server /data \
        --address "${MINIO_ADDRESS:-:9000}" \
        --console-address "${MINIO_CONSOLE_ADDRESS:-:9001}"
fi

exec runuser -u minio -- "$@"
