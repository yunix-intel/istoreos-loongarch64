#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /config
chown -R autobrr:autobrr /config
exec runuser -u autobrr -- env HOME=/config XDG_CONFIG_HOME=/config XDG_DATA_HOME=/config \
    /usr/local/bin/autobrr --config /config
