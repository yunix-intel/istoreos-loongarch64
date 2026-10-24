#!/bin/sh
set -e

mkdir -p /config /downloads
chown -R unpackerr:unpackerr /config /downloads

if [ ! -s /config/unpackerr.conf ]; then
    cp /etc/unpackerr/unpackerr.conf.example /config/unpackerr.conf
    chown unpackerr:unpackerr /config/unpackerr.conf
    echo "unpackerr: created /config/unpackerr.conf from example"
fi

if [ "$(id -u)" = "0" ]; then
    exec runuser -u unpackerr -- /usr/local/bin/unpackerr --config /config/unpackerr.conf
fi
exec /usr/local/bin/unpackerr --config /config/unpackerr.conf
