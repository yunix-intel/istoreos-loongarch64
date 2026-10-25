#!/usr/bin/env bash
set -Eeuo pipefail

# A bind mount hides the image's /data subdirectories, so recreate them with
# the runtime UID before dropping privileges. install -d is idempotent.
install -d -o 1119 -g 1119 /data/logs /data/temp /data/resource /data/storage
chown 1119:1119 /data

if [ "$#" -gt 0 ]; then
    exec runuser -u joplin -- "$@"
fi

exec runuser -u joplin -- /opt/node24/bin/node /opt/joplin/packages/server/dist/index.js
