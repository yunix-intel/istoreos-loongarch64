FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata bash curl procps-ng shadow && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1114 woodpecker && \
    useradd -u 1114 -g 1114 -M -d /var/lib/woodpecker -s /sbin/nologin woodpecker && \
    mkdir -p /etc/woodpecker /var/lib/woodpecker && \
    chown -R woodpecker:woodpecker /etc/woodpecker /var/lib/woodpecker
COPY woodpecker-agent /usr/local/bin/woodpecker-agent
RUN chmod 0755 /usr/local/bin/woodpecker-agent
ENV TZ=Asia/Shanghai \
    WOODPECKER_IN_CONTAINER=true \
    WOODPECKER_BACKEND=docker \
    WOODPECKER_SERVER=woodpecker-server:9000 \
    HOME=/var/lib/woodpecker
EXPOSE 3000
USER woodpecker
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:3000/healthz >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/woodpecker-agent"]
