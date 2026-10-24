FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1106 headscale && \
    useradd -u 1106 -g 1106 -M -d /var/lib/headscale -s /sbin/nologin headscale && \
    mkdir -p /etc/headscale /var/lib/headscale && \
    chown -R headscale:headscale /var/lib/headscale
COPY headscale /usr/local/bin/headscale
COPY config-example.yaml /etc/headscale/config-example.yaml
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/headscale /usr/local/bin/docker-entrypoint.sh && \
    chown -R headscale:headscale /etc/headscale /var/lib/headscale
ENV TZ=Asia/Shanghai \
    HEADSCALE_SERVER_URL=http://localhost:8080 \
    HEADSCALE_LISTEN_ADDR=0.0.0.0:8080 \
    HEADSCALE_METRICS_LISTEN_ADDR=0.0.0.0:9090
EXPOSE 8080 9090
VOLUME ["/etc/headscale", "/var/lib/headscale"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/health >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
