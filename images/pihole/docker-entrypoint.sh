#!/bin/sh
set -e

if [ ! -f /etc/pihole/gravity.db ]; then
    echo "[pihole] initializing gravity.db"
    sqlite3 /etc/pihole/gravity.db < /usr/share/pihole/gravity.db.sql
    chown pihole:pihole /etc/pihole/gravity.db || true
fi

exec /usr/bin/pihole-FTL -f
