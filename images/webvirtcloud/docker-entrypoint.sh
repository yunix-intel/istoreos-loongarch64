#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/srv/webvirtcloud
DATA_DIR=$APP_DIR/data

mkdir -p "$DATA_DIR" /var/www/.ssh /var/lib/nginx /var/log/nginx
chown -R www-data:www-data "$DATA_DIR" /var/www/.ssh /var/lib/nginx /var/log/nginx

if [ ! -f "$APP_DIR/webvirtcloud/settings.py" ]; then
    cp "$APP_DIR/webvirtcloud/settings.py.template" "$APP_DIR/webvirtcloud/settings.py"
fi

if [ -z "${SECRET_KEY:-}" ]; then
    if [ ! -s "$DATA_DIR/secret_key" ]; then
        "$APP_DIR/venv/bin/python3" -c 'import secrets; print(secrets.token_urlsafe(50))' > "$DATA_DIR/secret_key"
        chmod 600 "$DATA_DIR/secret_key"
    fi
    SECRET_KEY="$(cat "$DATA_DIR/secret_key")"
    export SECRET_KEY
fi

if [ -n "${WS_PUBLIC_PORT:-}" ]; then
    sed -i "s|^WS_PUBLIC_PORT = .*|WS_PUBLIC_PORT = $WS_PUBLIC_PORT|" "$APP_DIR/webvirtcloud/settings.py"
fi
if [ -n "${WS_PUBLIC_HOST:-}" ]; then
    sed -i "s|^WS_PUBLIC_HOST = .*|WS_PUBLIC_HOST = \"$WS_PUBLIC_HOST\"|" "$APP_DIR/webvirtcloud/settings.py"
fi
if [ -n "${WS_PUBLIC_PATH:-}" ]; then
    sed -i "s|^WS_PUBLIC_PATH = .*|WS_PUBLIC_PATH = \"$WS_PUBLIC_PATH\"|" "$APP_DIR/webvirtcloud/settings.py"
fi

if [ ! -f "$DATA_DIR/db.sqlite3" ] && [ -f "$APP_DIR/db.sqlite3" ] && [ ! -L "$APP_DIR/db.sqlite3" ]; then
    mv "$APP_DIR/db.sqlite3" "$DATA_DIR/db.sqlite3"
fi
touch "$DATA_DIR/db.sqlite3"
ln -sf "$DATA_DIR/db.sqlite3" "$APP_DIR/db.sqlite3"
chown -R www-data:www-data "$DATA_DIR"
chown www-data:www-data "$APP_DIR/webvirtcloud/settings.py"

"$APP_DIR/venv/bin/python3" "$APP_DIR/manage.py" migrate --noinput

pids=()
cleanup() {
    for pid in "${pids[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

runuser -u www-data -- "$APP_DIR/venv/bin/gunicorn" webvirtcloud.wsgi:application \
    -c "$APP_DIR/gunicorn.conf.py" &
pids+=($!)

runuser -u www-data -- "$APP_DIR/venv/bin/python3" "$APP_DIR/console/novncd" &
pids+=($!)

nginx -g 'daemon off;' &
pids+=($!)

wait -n "${pids[@]}"
