FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux coreutils httpd-tools && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1121 registry && \
    useradd -u 1121 -g 1121 -M -d /var/lib/registry -s /sbin/nologin registry && \
    mkdir -p /var/lib/registry /auth && chown registry:registry /var/lib/registry /auth
COPY registry /usr/local/bin/registry
COPY config.yml /etc/registry/config.yml
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/registry /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai
VOLUME ["/var/lib/registry", "/auth"]
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD sh -c 'code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/v2/); [ "$code" = 200 ] || [ "$code" = 401 ]' || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
