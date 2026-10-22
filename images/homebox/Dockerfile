FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata curl shadow util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1000 -M -d /data -s /sbin/nologin homebox && \
    mkdir -p /app /data && chown -R homebox:homebox /data
COPY homebox /app/homebox
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /app/homebox /usr/local/bin/docker-entrypoint.sh
ENV HBOX_MODE=production \
    HBOX_STORAGE_DATA=/data \
    HBOX_STORAGE_SQLITE_URL="/data/homebox.db?_pragma=busy_timeout=2000&_pragma=journal_mode=WAL&_fk=1"
EXPOSE 7745
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=8 \
    CMD curl -fsS http://127.0.0.1:7745/api/v1/status >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
