#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /data
chown -R homebox:homebox /data

exec runuser -u homebox -- /app/homebox "$@"
