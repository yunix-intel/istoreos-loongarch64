#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/var/www/bookstack
cd "$APP_DIR"

mkdir -p storage/app storage/framework/cache storage/framework/sessions \
    storage/framework/views storage/logs bootstrap/cache public/uploads
chown -R nginx:nginx storage bootstrap/cache public/uploads

KEY_FILE="$APP_DIR/storage/app.key"
if [ -n "${APP_KEY:-}" ]; then
    KEY="$APP_KEY"
elif [ -s "$KEY_FILE" ]; then
    KEY="$(cat "$KEY_FILE")"
else
    KEY="base64:$(head -c 32 /dev/urandom | base64 | tr -d '\n')"
    printf '%s\n' "$KEY" > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
fi
chown nginx:nginx "$KEY_FILE" 2>/dev/null || true

cat > "$APP_DIR/.env" <<EOF
APP_NAME=BookStack
APP_ENV=${APP_ENV:-production}
APP_KEY=${KEY}
APP_DEBUG=${APP_DEBUG:-false}
APP_URL=${APP_URL:-http://localhost}
DB_CONNECTION=mysql
DB_HOST=${DB_HOST:-mariadb}
DB_PORT=${DB_PORT:-3306}
DB_DATABASE=${DB_DATABASE:-bookstack}
DB_USERNAME=${DB_USERNAME:-bookstack}
DB_PASSWORD=${DB_PASSWORD:-bookstack}
CACHE_DRIVER=file
SESSION_DRIVER=file
QUEUE_CONNECTION=sync
STORAGE_TYPE=local
MAIL_DRIVER=${MAIL_DRIVER:-smtp}
MAIL_HOST=${MAIL_HOST:-localhost}
MAIL_PORT=${MAIL_PORT:-587}
MAIL_USERNAME=${MAIL_USERNAME:-null}
MAIL_PASSWORD=${MAIL_PASSWORD:-null}
MAIL_ENCRYPTION=${MAIL_ENCRYPTION:-null}
MAIL_FROM=${MAIL_FROM:-bookstack@example.com}
MAIL_FROM_NAME=${MAIL_FROM_NAME:-BookStack}
EOF
chown nginx:nginx "$APP_DIR/.env"

echo "Waiting for database ${DB_HOST:-mariadb}:${DB_PORT:-3306}/${DB_DATABASE:-bookstack} ..."
for _ in $(seq 1 60); do
    if php -r '
        try {
            new PDO(
                "mysql:host=" . getenv("DB_HOST") . ";port=" . getenv("DB_PORT") . ";dbname=" . getenv("DB_DATABASE"),
                getenv("DB_USERNAME"),
                getenv("DB_PASSWORD"),
                [PDO::ATTR_TIMEOUT => 2]
            );
            exit(0);
        } catch (Throwable $e) { exit(1); }
    '; then
        break
    fi
    sleep 2
done

runuser -u nginx -- php artisan migrate --force
runuser -u nginx -- php artisan config:cache

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

wait -n "${pids[@]}"
