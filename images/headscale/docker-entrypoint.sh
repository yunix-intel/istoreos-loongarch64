#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG=/etc/headscale/config.yaml
if [ ! -f "$CONFIG" ]; then
    cp /etc/headscale/config-example.yaml "$CONFIG"
fi

sed -i "s|^server_url:.*|server_url: ${HEADSCALE_SERVER_URL:-http://localhost:8080}|" "$CONFIG"
sed -i "s|^listen_addr:.*|listen_addr: ${HEADSCALE_LISTEN_ADDR:-0.0.0.0:8080}|" "$CONFIG"
sed -i "s|^metrics_listen_addr:.*|metrics_listen_addr: ${HEADSCALE_METRICS_LISTEN_ADDR:-0.0.0.0:9090}|" "$CONFIG"

mkdir -p /var/lib/headscale /var/run/headscale
chown -R headscale:headscale /var/lib/headscale /var/run/headscale /etc/headscale

exec runuser -u headscale -- /usr/local/bin/headscale serve -c "$CONFIG"
