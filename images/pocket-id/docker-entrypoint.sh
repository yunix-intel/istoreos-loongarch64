#!/bin/sh
set -e

mkdir -p /data/uploads
chown -R pocketid:pocketid /data

if [ -z "$ENCRYPTION_KEY" ]; then
    if [ ! -s /data/encryption-key ]; then
        head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > /data/encryption-key
        chmod 0600 /data/encryption-key
        chown pocketid:pocketid /data/encryption-key
        echo "pocket-id: generated encryption key at /data/encryption-key"
    fi
    ENCRYPTION_KEY=$(cat /data/encryption-key)
    export ENCRYPTION_KEY
fi

if [ "$(id -u)" = "0" ]; then
    exec runuser -u pocketid -- /usr/local/bin/pocket-id
fi
exec /usr/local/bin/pocket-id
