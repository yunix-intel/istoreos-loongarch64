FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        postgresql-server postgresql-contrib util-linux ca-certificates tzdata && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/lib/postgresql/data /var/run/postgresql && \
    chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
ENV PGDATA=/var/lib/postgresql/data
EXPOSE 5432
VOLUME ["/var/lib/postgresql/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
