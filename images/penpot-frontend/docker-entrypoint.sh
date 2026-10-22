#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG=/var/www/app/js/config.js

if [ -n "${PENPOT_FLAGS:-}" ]; then
    sed -i "s|^//var penpotFlags = .*;|var penpotFlags = \"$PENPOT_FLAGS\";|" "$CONFIG"
fi
if [ -n "${PENPOT_PUBLIC_URI:-}" ]; then
    sed -i '/^var penpotPublicURI = /d' "$CONFIG"
    echo "var penpotPublicURI = \"$PENPOT_PUBLIC_URI\";" >> "$CONFIG"
fi
if [ -n "${PENPOT_OIDC_NAME:-}" ]; then
    sed -i "s|^//var penpotOIDCName = .*;|var penpotOIDCName = \"$PENPOT_OIDC_NAME\";|" "$CONFIG"
fi

envsubst '${PENPOT_BACKEND_URI} ${PENPOT_EXPORTER_URI} ${PENPOT_HTTP_SERVER_MAX_BODY_SIZE}' \
    < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
