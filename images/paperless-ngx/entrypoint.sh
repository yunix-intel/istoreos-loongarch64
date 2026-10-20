#!/bin/sh
set -eu

export PAPERLESS_REDIS="${PAPERLESS_REDIS:-redis://127.0.0.1:6379/0}"
export PAPERLESS_DATA_DIR="${PAPERLESS_DATA_DIR:-/data}"
export PAPERLESS_MEDIA_ROOT="${PAPERLESS_MEDIA_ROOT:-/data/media}"
export PAPERLESS_CONSUMPTION_DIR="${PAPERLESS_CONSUMPTION_DIR:-/data/consume}"
export PAPERLESS_EXPORT_DIR="${PAPERLESS_EXPORT_DIR:-/data/export}"

mkdir -p "$PAPERLESS_DATA_DIR" "$PAPERLESS_MEDIA_ROOT" \
         "$PAPERLESS_CONSUMPTION_DIR" "$PAPERLESS_EXPORT_DIR"

# Persist a generated SECRET_KEY in the data volume when the operator did not
# provide one, so sessions survive container restarts.
if [ -z "${PAPERLESS_SECRET_KEY:-}" ]; then
    if [ ! -s "$PAPERLESS_DATA_DIR/secret_key" ]; then
        head -c 48 /dev/urandom | base64 | tr -d '\n' > "$PAPERLESS_DATA_DIR/secret_key"
    fi
    PAPERLESS_SECRET_KEY="$(cat "$PAPERLESS_DATA_DIR/secret_key")"
    export PAPERLESS_SECRET_KEY
fi

# Local Redis broker (Celery + channels).
LC_ALL=C.UTF-8 LANG=C.UTF-8 redis-server --bind 127.0.0.1 --port 6379 --save '' --appendonly no &
REDIS_PID=$!

# Wait for the local Redis socket before Django touches the cache.
i=0
while ! redis-cli -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; do
    i=$((i+1))
    [ "$i" -ge 50 ] && break
    sleep 0.2
done

cd /usr/src/paperless/src

python manage.py migrate --noinput
python manage.py manage_superuser || true

# Consume files dropped into PAPERLESS_CONSUMPTION_DIR; the official
# image runs this in the webserver container.
python manage.py document_consumer &

# Scheduled tasks (sanity checker, email, etc.).
celery -A paperless beat --loglevel INFO &

celery -A paperless worker \
    --loglevel INFO \
    --concurrency "${PAPERLESS_CELERY_CONCURRENCY:-2}" &

# daphne is the ASGI server; it also serves websocket consumers.
exec daphne -b 0.0.0.0 -p 8000 paperless.asgi:application
