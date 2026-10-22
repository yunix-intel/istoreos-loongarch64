#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p "${NC_TOOL_DIR:-/data}"
chown -R nocodb:nocodb "${NC_TOOL_DIR:-/data}"

exec runuser -u nocodb -- node /opt/node24/lib/node_modules/nocodb/docker-main.js "$@"
