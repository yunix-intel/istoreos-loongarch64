FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1114 woodpecker && \
    useradd -u 1114 -g 1114 -M -d /var/lib/woodpecker -s /sbin/nologin woodpecker && \
    mkdir -p /var/lib/woodpecker && chown -R woodpecker:woodpecker /var/lib/woodpecker
COPY woodpecker-server /usr/local/bin/woodpecker-server
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/woodpecker-server /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai \
    WOODPECKER_IN_CONTAINER=true \
    WOODPECKER_SERVER_ADDR=:8000 \
    WOODPECKER_GRPC_ADDR=:9000 \
    XDG_CACHE_HOME=/var/lib/woodpecker \
    XDG_DATA_HOME=/var/lib/woodpecker \
    SQLITE_TMPDIR=/var/lib/woodpecker
EXPOSE 8000 9000
VOLUME ["/var/lib/woodpecker"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8000/api/healthz >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
