#!/bin/sh
set -eu

# wg-easy stores its SQLite database and wg0.conf here.
mkdir -p /etc/wireguard

# libsql's Node wrapper loads ./index.node when this is set. The loong64
# binding is vendored into the image because @libsql has no loong64 build.
export LIBSQL_JS_DEV=1

if [ ! -f /app/server/node_modules/libsql/index.node ]; then
    echo "wg-easy: missing libsql loong64 binding (index.node)" >&2
    exit 1
fi

exec node server/index.mjs
