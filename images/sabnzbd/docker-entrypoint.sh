#!/bin/sh
set -e

mkdir -p /config /downloads
chown -R sabnzbd:sabnzbd /config /downloads

if [ "$(id -u)" = "0" ]; then
    exec runuser -u sabnzbd -- /opt/venv/bin/python3 /app/SABnzbd.py \
        --config-file /config/sabnzbd.ini --server 0.0.0.0:8080 --browser 0
fi
exec /opt/venv/bin/python3 /app/SABnzbd.py \
    --config-file /config/sabnzbd.ini --server 0.0.0.0:8080 --browser 0
