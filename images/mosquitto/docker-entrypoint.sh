#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /mosquitto/data /mosquitto/log
chown mosquitto:mosquitto /mosquitto/data /mosquitto/log

if [ "$#" -eq 0 ]; then
    set -- /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
fi

exec runuser -u mosquitto -- "$@"
