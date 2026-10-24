FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux libgcc && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1117 readeck && \
    useradd -u 1117 -g 1117 -M -d /data -s /sbin/nologin readeck && \
    mkdir -p /data && chown readeck:readeck /data
COPY readeck /usr/local/bin/readeck
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/readeck /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai \
    READECK_SERVER_HOST=0.0.0.0 \
    READECK_SERVER_PORT=8000 \
    HOME=/data
WORKDIR /data
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsSL http://127.0.0.1:8000/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
