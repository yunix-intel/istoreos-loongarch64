#!/usr/bin/env bash
set -Eeuo pipefail

DATA="${ZIGBEE2MQTT_DATA:-/app/data}"
mkdir -p "$DATA"
chown -R zigbee2mqtt:zigbee2mqtt "$DATA"

if [ ! -f "$DATA/configuration.yaml" ]; then
    cp /app/configuration.example.yaml "$DATA/configuration.yaml"
    chown zigbee2mqtt:zigbee2mqtt "$DATA/configuration.yaml"
fi

# Convenience aliases; Z2M itself reads ZIGBEE2MQTT_CONFIG_*.
if [ -n "${MQTT_SERVER:-}" ] && [ -z "${ZIGBEE2MQTT_CONFIG_MQTT_SERVER:-}" ]; then
    export ZIGBEE2MQTT_CONFIG_MQTT_SERVER="$MQTT_SERVER"
fi
if [ -n "${MQTT_USER:-}" ] && [ -z "${ZIGBEE2MQTT_CONFIG_MQTT_USER:-}" ]; then
    export ZIGBEE2MQTT_CONFIG_MQTT_USER="$MQTT_USER"
fi
if [ -n "${MQTT_PASSWORD:-}" ] && [ -z "${ZIGBEE2MQTT_CONFIG_MQTT_PASSWORD:-}" ]; then
    export ZIGBEE2MQTT_CONFIG_MQTT_PASSWORD="$MQTT_PASSWORD"
fi

cd /app
exec runuser -u zigbee2mqtt -- env ZIGBEE2MQTT_DATA="$DATA" node index.js
