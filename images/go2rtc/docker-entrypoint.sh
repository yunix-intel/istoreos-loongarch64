#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /config
if [ ! -f /config/go2rtc.yaml ]; then
    cp /usr/local/share/go2rtc.yaml /config/go2rtc.yaml 2>/dev/null || true
fi
chown -R go2rtc:go2rtc /config
exec runuser -u go2rtc -- /usr/local/bin/go2rtc -config /config/go2rtc.yaml
