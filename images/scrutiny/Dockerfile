FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng \
        smartmontools libstdc++ libgcc && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /opt/scrutiny/bin /opt/scrutiny/web /opt/scrutiny/config
COPY scrutiny /opt/scrutiny/bin/scrutiny
COPY scrutiny-collector-metrics /opt/scrutiny/bin/scrutiny-collector-metrics
COPY web/ /opt/scrutiny/web/
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod 0755 /opt/scrutiny/bin/scrutiny /opt/scrutiny/bin/scrutiny-collector-metrics /entrypoint.sh
ENV PATH=/opt/scrutiny/bin:$PATH \
    TZ=Asia/Shanghai
EXPOSE 8080
VOLUME ["/opt/scrutiny/config"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/api/health >/dev/null || exit 1
ENTRYPOINT ["/entrypoint.sh"]
