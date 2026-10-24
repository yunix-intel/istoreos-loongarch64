FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng openssh-clients && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1108 backrest && \
    useradd -u 1108 -g 1108 -M -d /data -s /bin/bash backrest && \
    mkdir -p /data /config /cache && chown -R backrest:backrest /data /config /cache
COPY backrest /usr/local/bin/backrest
COPY restic /usr/local/bin/restic
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/backrest /usr/local/bin/restic /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai \
    BACKREST_DATA=/data \
    BACKREST_CONFIG=/config/config.json \
    BACKREST_PORT=0.0.0.0:9898 \
    BACKREST_RESTIC_COMMAND=/usr/local/bin/restic \
    XDG_CACHE_HOME=/cache \
    TMPDIR=/tmp
EXPOSE 9898
VOLUME ["/data", "/config", "/cache"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9898/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
