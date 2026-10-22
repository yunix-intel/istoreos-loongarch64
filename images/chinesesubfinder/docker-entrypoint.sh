#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /config /media
chown -R csf:csf /config /media

cd /config
exec runuser -u csf -- /usr/bin/chinesesubfinder "$@"
