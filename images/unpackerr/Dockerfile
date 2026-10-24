FROM openeuler/openeuler:24.03 AS unrar
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        gcc-c++ make curl tar xz && \
    dnf clean all && rm -rf /var/cache/dnf
RUN curl -fsSL -o /tmp/unrar.tar.gz https://www.rarlab.com/rar/unrarsrc-7.1.10.tar.gz && \
    tar xzf /tmp/unrar.tar.gz -C /tmp && cd /tmp/unrar && \
    make -j"$(nproc)" && install -m 0755 unrar /usr/local/bin/unrar


FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata bash shadow util-linux procps-ng p7zip && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1123 unpackerr && \
    useradd -u 1123 -g 1123 -M -d /config -s /sbin/nologin unpackerr && \
    mkdir -p /config /downloads /etc/unpackerr && \
    chown unpackerr:unpackerr /config /downloads
COPY --from=unrar /usr/local/bin/unrar /usr/local/bin/unrar
COPY unpackerr /usr/local/bin/unpackerr
COPY unpackerr.conf.example /etc/unpackerr/unpackerr.conf.example
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/unpackerr /usr/local/bin/unrar /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai \
    UN_CONFIG_FILE=/config/unpackerr.conf \
    HOME=/config
VOLUME ["/config", "/downloads"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD pgrep -f /usr/local/bin/unpackerr >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
