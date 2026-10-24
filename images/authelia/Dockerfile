FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng gettext \
        libstdc++ libgcc sqlite-libs && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1107 authelia && \
    useradd -u 1107 -g 1107 -M -d /config -s /sbin/nologin authelia && \
    mkdir -p /config && chown -R authelia:authelia /config
COPY authelia /usr/local/bin/authelia
COPY configuration.yml.template /usr/local/share/authelia/configuration.yml.template
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/authelia /usr/local/bin/docker-entrypoint.sh
ENV TZ=Asia/Shanghai \
    AUTH_DOMAIN=example.com \
    AUTH_URL=https://auth.example.com \
    AUTH_DEFAULT_REDIRECT_URL=https://app.example.com \
    ADMIN_USER=admin \
    ADMIN_PASSWORD=change-me \
    ADMIN_EMAIL=admin@example.com
EXPOSE 9091
VOLUME ["/config"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9091/api/health >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
