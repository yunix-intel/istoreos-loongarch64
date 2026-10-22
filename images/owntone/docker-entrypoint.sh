#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /srv/music /var/cache/owntone /var/log/owntone
chown -R owntone:owntone /srv/music /var/cache/owntone /var/log/owntone
touch /var/log/owntone.log
chown owntone:owntone /var/log/owntone.log
mkdir -p /run/dbus /run/avahi-daemon
dbus-daemon --system --fork
avahi-daemon --daemonize --no-chroot

exec runuser -u owntone -- /usr/sbin/owntone -f -c /etc/owntone.conf --mdns-no-rsp --mdns-no-daap --mdns-no-cname --mdns-no-web "$@"
