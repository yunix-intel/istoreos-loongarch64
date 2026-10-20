FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False redis util-linux ca-certificates tzdata && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /data && chown redis:redis /data
COPY redis.conf /usr/local/etc/redis/redis.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
EXPOSE 6379
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD sh -c 'if [ -n "$REDIS_PASSWORD" ]; then redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ping; else redis-cli ping; fi' || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
