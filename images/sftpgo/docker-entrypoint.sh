#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /srv/sftpgo/data /srv/sftpgo/backups /var/lib/sftpgo
chown -R sftpgo:sftpgo /srv/sftpgo /var/lib/sftpgo

cd /var/lib/sftpgo
exec runuser -u sftpgo -- env \
    SFTPGO_LOG_FILE_PATH="${SFTPGO_LOG_FILE_PATH:-}" \
    /usr/local/bin/sftpgo serve
