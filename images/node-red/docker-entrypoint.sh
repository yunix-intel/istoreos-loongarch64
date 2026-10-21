#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /data
chown nodered:nodered /data

if [ ! -f /data/settings.js ]; then
    cp /opt/node22/lib/node_modules/node-red/settings.js /data/settings.js
    chown nodered:nodered /data/settings.js
fi

if [ "$#" -eq 0 ]; then
    set -- node-red --userDir /data --settings /data/settings.js
fi

exec runuser -u nodered -- "$@"
