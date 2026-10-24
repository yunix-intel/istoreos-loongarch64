FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1115 mediamtx && \
    useradd -u 1115 -g 1115 -M -d /nonexistent -s /sbin/nologin mediamtx
COPY mediamtx /usr/local/bin/mediamtx
COPY mediamtx.yml /mediamtx.yml
RUN chmod 0755 /usr/local/bin/mediamtx
USER mediamtx
ENV TZ=Asia/Shanghai
EXPOSE 8554/tcp 1935/tcp 8888/tcp 8889/tcp 8890/udp 8189/udp 9997/tcp 8000/udp 8001/udp
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9997/v3/paths/list >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/mediamtx", "/mediamtx.yml"]
