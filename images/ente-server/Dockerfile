FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1105 ente && \
    useradd -u 1105 -g 1105 -M -d /data -s /sbin/nologin ente && \
    mkdir -p /etc/ente /data && chown -R ente:ente /etc/ente /data
COPY museum /etc/ente/museum
COPY configurations/ /etc/ente/configurations/
COPY migrations/ /etc/ente/migrations/
COPY mail-templates/ /etc/ente/mail-templates/
COPY web-templates/ /etc/ente/web-templates/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /etc/ente/museum /usr/local/bin/docker-entrypoint.sh && \
    chown -R ente:ente /etc/ente
WORKDIR /etc/ente
ENV TZ=Asia/Shanghai \
    ENVIRONMENT=local \
    ENTE_DB_HOST=postgres \
    ENTE_DB_PORT=5432 \
    ENTE_DB_NAME=ente_db \
    ENTE_DB_USER=pguser \
    ENTE_DB_PASSWORD=change-me \
    ENTE_S3_ENDPOINT=minio:3200 \
    ENTE_S3_KEY=minio \
    ENTE_S3_SECRET=change-me \
    ENTE_S3_REGION=eu-central-2 \
    ENTE_S3_BUCKET_PRIMARY=b2-eu-cen
EXPOSE 8080
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/ping >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
