FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1109 go2rtc && \
    useradd -u 1109 -g 1109 -M -d /config -s /sbin/nologin go2rtc && \
    mkdir -p /config && chown -R go2rtc:go2rtc /config
COPY go2rtc /usr/local/bin/go2rtc
COPY go2rtc.yaml /config/go2rtc.yaml
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/go2rtc /usr/local/bin/docker-entrypoint.sh && \
    chown -R go2rtc:go2rtc /config
ENV TZ=Asia/Shanghai
EXPOSE 1984 8554 8555
VOLUME ["/config"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
    CMD curl -fsS http://127.0.0.1:1984/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
