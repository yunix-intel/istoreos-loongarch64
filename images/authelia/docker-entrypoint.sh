#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG=/config/configuration.yml
USERS=/config/users_database.yml
SECRET_FILE=/config/session.secret
STORAGE_KEY_FILE=/config/storage.key

mkdir -p /config
chown -R authelia:authelia /config

if [ ! -s "$SECRET_FILE" ]; then
    head -c 64 /dev/urandom | base64 | tr -d '\n' > "$SECRET_FILE"
    chmod 600 "$SECRET_FILE"
fi
if [ ! -s "$STORAGE_KEY_FILE" ]; then
    head -c 64 /dev/urandom | base64 | tr -d '\n' > "$STORAGE_KEY_FILE"
    chmod 600 "$STORAGE_KEY_FILE"
fi
AUTHELIA_SESSION_SECRET="$(cat "$SECRET_FILE")"
AUTHELIA_STORAGE_ENCRYPTION_KEY="$(cat "$STORAGE_KEY_FILE")"
export AUTHELIA_SESSION_SECRET AUTHELIA_STORAGE_ENCRYPTION_KEY

if [ ! -f "$USERS" ]; then
    HASH="$(/usr/local/bin/authelia crypto hash generate argon2 \
        --password "${ADMIN_PASSWORD:-change-me}" | awk '/^Digest:/{print $2}')"
    cat > "$USERS" <<EOF
users:
  ${ADMIN_USER:-admin}:
    displayname: ${ADMIN_USER:-admin}
    password: '${HASH}'
    email: ${ADMIN_EMAIL:-admin@example.com}
EOF
fi

if [ ! -f "$CONFIG" ]; then
    envsubst '${AUTHELIA_SESSION_SECRET} ${AUTHELIA_STORAGE_ENCRYPTION_KEY} ${AUTH_DOMAIN} ${AUTH_URL} ${AUTH_DEFAULT_REDIRECT_URL}' \
        < /usr/local/share/authelia/configuration.yml.template > "$CONFIG"
fi

chown -R authelia:authelia /config
chmod 600 "$CONFIG" "$USERS" "$SECRET_FILE" "$STORAGE_KEY_FILE"

runuser -u authelia -- /usr/local/bin/authelia validate-config --config "$CONFIG"
exec runuser -u authelia -- /usr/local/bin/authelia --config "$CONFIG"
