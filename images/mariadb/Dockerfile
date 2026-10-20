FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        mariadb-server mariadb util-linux ca-certificates tzdata && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/lib/mysql /run/mysqld /var/log/mariadb && \
    ln -sf /dev/stderr /var/log/mariadb/mariadb.log && \
    chown -R mysql:mysql /var/lib/mysql /run/mysqld /var/log/mariadb
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY client.cnf /etc/my.cnf.d/container-client.cnf
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
EXPOSE 3306
VOLUME ["/var/lib/mysql"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mariadb-admin --socket=/run/mysqld/mysqld.sock -u root ping >/dev/null' || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
