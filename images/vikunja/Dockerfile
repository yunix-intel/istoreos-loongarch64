FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1104 vikunja && \
    useradd -u 1104 -g 1104 -M -d /app/vikunja -s /bin/bash vikunja && \
    mkdir -p /app/vikunja/files /db && \
    chown -R vikunja:vikunja /app/vikunja /db
COPY vikunja /app/vikunja/vikunja
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /app/vikunja/vikunja /usr/local/bin/docker-entrypoint.sh && \
    chown -R vikunja:vikunja /app/vikunja
ENV TZ=Asia/Shanghai \
    VIKUNJA_SERVICE_ROOTPATH=/app/vikunja/ \
    VIKUNJA_DATABASE_TYPE=sqlite \
    VIKUNJA_DATABASE_PATH=/db/vikunja.db \
    VIKUNJA_SERVICE_INTERFACE=0.0.0.0:3456 \
    VIKUNJA_SERVICE_PUBLICURL=http://localhost:3456/
EXPOSE 3456
VOLUME ["/app/vikunja/files", "/db"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:3456/health >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
