#!/bin/sh
set -e

mkdir -p /var/lib/registry /auth
chown -R registry:registry /var/lib/registry /auth

if [ "${REGISTRY_ALLOW_ANONYMOUS:-false}" = "true" ]; then
    unset REGISTRY_AUTH REGISTRY_AUTH_HTPASSWD_PATH REGISTRY_AUTH_HTPASSWD_REALM
else
    if [ -z "$REGISTRY_AUTH_HTPASSWD_PATH" ]; then
        REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd
        export REGISTRY_AUTH_HTPASSWD_PATH
    fi
    if [ ! -s "$REGISTRY_AUTH_HTPASSWD_PATH" ]; then
        password="${REGISTRY_PASSWORD:-$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | cut -c1-24)}"
        htpasswd -Bbn "${REGISTRY_USER:-admin}" "$password" > "$REGISTRY_AUTH_HTPASSWD_PATH"
        printf '%s\n' "$password" > /auth/password
        chmod 0600 "$REGISTRY_AUTH_HTPASSWD_PATH" /auth/password
        echo "registry: generated basic-auth user '${REGISTRY_USER:-admin}', password is in /auth/password"
    fi
    REGISTRY_AUTH=htpasswd
    REGISTRY_AUTH_HTPASSWD_REALM="${REGISTRY_AUTH_HTPASSWD_REALM:-Registry Realm}"
    export REGISTRY_AUTH REGISTRY_AUTH_HTPASSWD_REALM
fi
chown -R registry:registry /auth

if [ -z "$REGISTRY_HTTP_SECRET" ]; then
    if [ ! -s /auth/http-secret ]; then
        head -c 32 /dev/urandom | base64 | tr -d '/+=' > /auth/http-secret
        chmod 0600 /auth/http-secret
    fi
    REGISTRY_HTTP_SECRET=$(cat /auth/http-secret)
    export REGISTRY_HTTP_SECRET
    chown registry:registry /auth/http-secret
fi

if [ "$(id -u)" = "0" ]; then
    exec runuser -u registry -- /usr/local/bin/registry serve /etc/registry/config.yml
fi
exec /usr/local/bin/registry serve /etc/registry/config.yml
