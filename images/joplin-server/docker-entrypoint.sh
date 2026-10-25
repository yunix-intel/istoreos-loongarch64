#!/usr/bin/env bash
set -Eeuo pipefail

# Only the top level of /data is chowned: the data volume may be large and a
# recursive chown would delay every start. Subdirectories (logs/temp/resource/
# storage) are created with UID 1119 in the image; bind mounts should be
# prepared with: chown -R 1119:1119 <dir>
chown 1119:1119 /data

if [ "$#" -gt 0 ]; then
    exec runuser -u joplin -- "$@"
fi

exec runuser -u joplin -- /opt/node24/bin/node /opt/joplin/packages/server/dist/index.js
