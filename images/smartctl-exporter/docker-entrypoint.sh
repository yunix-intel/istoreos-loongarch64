#!/usr/bin/env bash
set -Eeuo pipefail
exec /usr/local/bin/smartctl_exporter --smartctl.path=/usr/sbin/smartctl "$@"
