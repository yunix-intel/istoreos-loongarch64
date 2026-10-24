FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng smartmontools && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1102 smartctl && \
    useradd -u 1102 -g 1102 -M -d /var/lib/smartctl -s /sbin/nologin smartctl
COPY smartctl_exporter /usr/local/bin/smartctl_exporter
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/smartctl_exporter /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai
EXPOSE 9633
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9633/metrics >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
