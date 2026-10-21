#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /homebridge
chown -R homebridge:homebridge /homebridge

if [ ! -f /homebridge/config.json ]; then
    cp /usr/local/share/homebridge/config.json /homebridge/config.json
    chown homebridge:homebridge /homebridge/config.json
fi

if [ "$#" -eq 0 ]; then
    set -- homebridge -U /homebridge
fi

exec runuser -u homebridge -- "$@"
