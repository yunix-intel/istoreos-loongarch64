#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /var/www/matomo/config /var/www/matomo/tmp
chown -R nginx:nginx /var/www/matomo/config /var/www/matomo/tmp
mkdir -p /run/php-fpm
chown nginx:nginx /run/php-fpm

php-fpm -F &
pids=($!)
nginx -g 'daemon off;' &
pids+=($!)

cleanup() {
    for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "Matomo is ready. Open /index.php to run the installer." >&2
wait -n "${pids[@]}"
