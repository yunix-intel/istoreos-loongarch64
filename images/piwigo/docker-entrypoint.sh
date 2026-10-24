#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/var/www/piwigo
cd "$APP_DIR"

mkdir -p local/config _data galleries upload
chown -R nginx:nginx local _data galleries upload

DB_HOST="${PIWIGO_DB_HOST:-mariadb}"
DB_NAME="${PIWIGO_DB_NAME:-piwigo}"
DB_USER="${PIWIGO_DB_USER:-piwigo}"
DB_PASS="${PIWIGO_DB_PASSWORD:-piwigo}"
ADMIN_USER="${PIWIGO_ADMIN_USER:-admin}"
ADMIN_PASS="${PIWIGO_ADMIN_PASSWORD:-admin-change-me}"
ADMIN_MAIL="${PIWIGO_ADMIN_EMAIL:-admin@example.com}"

echo "Waiting for database ${DB_HOST}/${DB_NAME} ..."
for _ in $(seq 1 60); do
    if php -r '
        try {
            new PDO("mysql:host=" . getenv("PIWIGO_DB_HOST") . ";dbname=" . getenv("PIWIGO_DB_NAME"),
                getenv("PIWIGO_DB_USER"), getenv("PIWIGO_DB_PASSWORD"), [PDO::ATTR_TIMEOUT => 2]);
            exit(0);
        } catch (Throwable $e) { exit(1); }
    '; then
        break
    fi
    sleep 2
done

mkdir -p /run/php-fpm
chown nginx:nginx /run/php-fpm
php-fpm -F &
pids=($!)
nginx -g 'daemon off;' &
pids+=($!)

if [ ! -f "$APP_DIR/local/config/database.inc.php" ]; then
    echo "Piwigo not installed yet; running first-run installer ..."
    sleep 3
    curl -fsS -X POST "http://127.0.0.1/install.php" \
        --data-urlencode "install=1" \
        --data-urlencode "language=en" \
        --data-urlencode "prefix=piwigo_" \
        --data-urlencode "dbhost=$DB_HOST" \
        --data-urlencode "dbuser=$DB_USER" \
        --data-urlencode "dbpasswd=$DB_PASS" \
        --data-urlencode "dbname=$DB_NAME" \
        --data-urlencode "admin_name=$ADMIN_USER" \
        --data-urlencode "admin_pass1=$ADMIN_PASS" \
        --data-urlencode "admin_pass2=$ADMIN_PASS" \
        --data-urlencode "admin_mail=$ADMIN_MAIL" \
        -o /tmp/piwigo-install.html >/dev/null 2>&1 || true
    if [ -f "$APP_DIR/local/config/database.inc.php" ]; then
        echo "Piwigo installer completed."
    else
        echo "Piwigo installer did not complete; open /install.php in the browser." >&2
    fi
fi

cleanup() {
    for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

wait -n "${pids[@]}"
