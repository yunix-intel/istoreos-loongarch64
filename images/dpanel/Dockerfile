FROM openeuler/openeuler:24.03

ENV TZ=Asia/Shanghai \
    PATH=/app/server:$PATH \
    DOCKER_HOST=unix:///var/run/docker.sock \
    DP_SYSTEM_STORAGE_LOCAL_PATH=/dpanel \
    DP_DB_DATABASE=/dpanel/dpanel.db \
    DP_ACME_CONFIG_HOME=/dpanel/acme \
    DP_RUN_IN_CONTAINER=1 \
    APP_NAME=dpanel \
    APP_SERVER_PORT=8807 \
    APP_VERSION=1.11.1 \
    APP_FAMILY=ce \
    APP_ENV=lite

WORKDIR /app/server
VOLUME ["/dpanel"]

COPY dpanel /app/server/dpanel
COPY config.yaml /app/server/config.yaml

RUN dnf install -y openssh-clients git curl bash tar gzip \
    && dnf clean all \
    && chmod 755 /app/server/dpanel && mkdir -p /dpanel

EXPOSE 8807
ENTRYPOINT ["/app/server/dpanel", "server:start", "-f", "/app/server/config.yaml"]
