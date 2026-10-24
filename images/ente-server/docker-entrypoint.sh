#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /data
chown -R ente:ente /data

MUSEUM_YAML=/data/museum.yaml
if [ ! -f "$MUSEUM_YAML" ]; then
    ENC="$(head -c 32 /dev/urandom | base64 | tr -d '\n')"
    HASH="$(head -c 64 /dev/urandom | base64 | tr -d '\n')"
    JWT="$(head -c 32 /dev/urandom | base64 | tr '+/' '-_' | tr -d '\n')"
    cat > "$MUSEUM_YAML" <<EOF
db:
    host: ${ENTE_DB_HOST:-postgres}
    port: ${ENTE_DB_PORT:-5432}
    name: ${ENTE_DB_NAME:-ente_db}
    user: ${ENTE_DB_USER:-pguser}
    password: ${ENTE_DB_PASSWORD:-change-me}

s3:
    are_local_buckets: true
    use_path_style_urls: true
    b2-eu-cen:
        key: ${ENTE_S3_KEY:-minio}
        secret: ${ENTE_S3_SECRET:-change-me}
        endpoint: ${ENTE_S3_ENDPOINT:-minio:3200}
        region: ${ENTE_S3_REGION:-eu-central-2}
        bucket: b2-eu-cen
    wasabi-eu-central-2-v3:
        key: ${ENTE_S3_KEY:-minio}
        secret: ${ENTE_S3_SECRET:-change-me}
        endpoint: ${ENTE_S3_ENDPOINT:-minio:3200}
        region: ${ENTE_S3_REGION:-eu-central-2}
        bucket: wasabi-eu-central-2-v3
        compliance: false
    scw-eu-fr-v3:
        key: ${ENTE_S3_KEY:-minio}
        secret: ${ENTE_S3_SECRET:-change-me}
        endpoint: ${ENTE_S3_ENDPOINT:-minio:3200}
        region: ${ENTE_S3_REGION:-eu-central-2}
        bucket: scw-eu-fr-v3

key:
    encryption: ${ENC}
    hash: ${HASH}
jwt:
    secret: ${JWT}
EOF
    chmod 600 "$MUSEUM_YAML"
fi

ln -sf "$MUSEUM_YAML" /etc/ente/museum.yaml
chown -R ente:ente /data /etc/ente

cd /etc/ente
exec runuser -u ente -- env \
    ENVIRONMENT="${ENVIRONMENT:-local}" \
    GIT_COMMIT="${GIT_COMMIT:-unknown}" \
    ./museum
