FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        memcached util-linux ca-certificates tzdata && \
    dnf clean all && rm -rf /var/cache/dnf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
EXPOSE 11211
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD bash -c 'exec 3<>/dev/tcp/127.0.0.1/${MEMCACHED_PORT:-11211}' || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
