FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng smartmontools && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1102 scrutiny && \
    useradd -u 1102 -g 1102 -M -d /opt/scrutiny -s /bin/bash scrutiny && \
    mkdir -p /opt/scrutiny/bin /opt/scrutiny/web /opt/scrutiny/config && \
    chown -R scrutiny:scrutiny /opt/scrutiny
COPY scrutiny-web /opt/scrutiny/bin/scrutiny-web
COPY scrutiny-collector-metrics /opt/scrutiny/bin/scrutiny-collector-metrics
COPY web/ /opt/scrutiny/web/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /opt/scrutiny/bin/scrutiny-* /usr/local/bin/docker-entrypoint.sh && \
    chown -R scrutiny:scrutiny /opt/scrutiny
ENV PATH=/opt/scrutiny/bin:$PATH \
    TZ=Asia/Shanghai \
    SCRUTINY_WEB_LISTEN_HOST=0.0.0.0 \
    SCRUTINY_WEB_LISTEN_PORT=8080 \
    SCRUTINY_WEB_SRC_FRONTEND_PATH=/opt/scrutiny/web \
    SCRUTINY_WEB_DATABASE_LOCATION=/opt/scrutiny/config/scrutiny.db \
    COLLECTOR_API_ENDPOINT=http://127.0.0.1:8080 \
    COLLECTOR_HOST_ID=scrutiny \
    COLLECTOR_INTERVAL=3600
EXPOSE 8080
VOLUME ["/opt/scrutiny/config"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/api/health >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
