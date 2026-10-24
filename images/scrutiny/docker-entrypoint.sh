#!/bin/sh
set -e
mkdir -p /opt/scrutiny/config
if [ "$1" = "collector" ]; then
  shift
  exec scrutiny-collector-metrics run "$@"
fi
if [ -f /opt/scrutiny/config/scrutiny.yaml ]; then
  exec scrutiny start --config /opt/scrutiny/config/scrutiny.yaml
fi
exec scrutiny start
