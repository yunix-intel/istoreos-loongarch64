FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata curl shadow util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1000 -M -d /data -s /sbin/nologin minio && \
    mkdir -p /data && chown -R minio:minio /data
COPY minio /usr/bin/minio
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/bin/minio /usr/local/bin/docker-entrypoint.sh
ENV MINIO_UPDATE=off
EXPOSE 9000 9001
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1:9000/minio/health/live >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
