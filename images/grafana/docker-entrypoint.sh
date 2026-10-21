#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /var/lib/grafana/plugins /var/log/grafana \
    /etc/grafana/provisioning/datasources /etc/grafana/provisioning/dashboards \
    /etc/grafana/provisioning/notifiers /etc/grafana/provisioning/plugins \
    /etc/grafana/provisioning/alerting
chown grafana:grafana /var/lib/grafana /var/log/grafana

if [ "$#" -eq 0 ]; then
    set -- server --homepath=/usr/share/grafana --config=/etc/grafana/grafana.ini
fi

exec runuser -u grafana -- /usr/share/grafana/bin/grafana "$@"
