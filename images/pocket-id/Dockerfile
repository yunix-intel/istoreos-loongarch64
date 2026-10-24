FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1122 pocketid && \
    useradd -u 1122 -g 1122 -M -d /data -s /sbin/nologin pocketid && \
    mkdir -p /data && chown pocketid:pocketid /data
COPY pocket-id /usr/local/bin/pocket-id
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/pocket-id /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai \
    APP_ENV=production \
    PORT=1411 \
    APP_URL=http://localhost:1411 \
    DB_CONNECTION_STRING=/data/pocket-id.db \
    UPLOAD_PATH=/data/uploads \
    HOME=/data
VOLUME ["/data"]
EXPOSE 1411
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:1411/healthz >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
