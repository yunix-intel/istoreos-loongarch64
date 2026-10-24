#!/bin/sh
set -e

mkdir -p /data
chown -R readeck:readeck /data

if [ "$(id -u)" = "0" ]; then
    exec runuser -u readeck -- /usr/local/bin/readeck serve -config /data/config.toml
fi
exec /usr/local/bin/readeck serve -config /data/config.toml
