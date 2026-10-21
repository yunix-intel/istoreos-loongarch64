#!/usr/bin/env bash
set -Eeuo pipefail

DATA_DIRECTORY="${DATA_DIRECTORY:-/data}"
PASSWORD_FILE="${PASSWORD_FILE:-$DATA_DIRECTORY/.htpasswd}"
export DATA_DIRECTORY PASSWORD_FILE

mkdir -p "$DATA_DIRECTORY"

OPTIONS=()
if [ -n "${DISABLE_AUTHENTICATION:-}" ]; then
    OPTIONS+=(--no-auth)
else
    if [ ! -f "$PASSWORD_FILE" ]; then
        umask 027
        touch "$PASSWORD_FILE"
    fi
    if [ ! -s "$PASSWORD_FILE" ]; then
        echo >&2
        echo >&2 "**WARNING** No user exists; run: docker exec -it <container> create_user"
        echo >&2
    fi
fi

exec /usr/bin/rest-server \
    --path "$DATA_DIRECTORY" \
    --htpasswd-file "$PASSWORD_FILE" \
    "${OPTIONS[@]}" \
    "$@"
