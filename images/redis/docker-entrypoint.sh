#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /data
chown redis:redis /data

conf=/usr/local/etc/redis/redis.conf
if [ -n "${REDIS_PASSWORD:-}" ]; then
    conf=/tmp/redis.conf
    cp /usr/local/etc/redis/redis.conf "$conf"
    printf '\nrequirepass %s\n' "$REDIS_PASSWORD" >>"$conf"
    chown redis:redis "$conf"
    chmod 0600 "$conf"
fi

if [ "$#" -eq 0 ]; then
    set -- redis-server "$conf"
fi

exec runuser -u redis -- "$@"
