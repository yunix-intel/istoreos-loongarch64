FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata shadow sqlite bash curl sudo bind-utils \
        libidn2 libunistring readline ncurses-libs \
        libcap openssl-libs libcurl dbus-libs sqlite-libs systemd-libs && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -r -s /sbin/nologin pihole && \
    mkdir -p /etc/pihole /var/log/pihole /run/pihole /var/www/html/admin /usr/share/pihole /opt/pihole /etc/.pihole
COPY pihole-FTL /usr/bin/pihole-FTL
COPY gravity.db.sql /usr/share/pihole/gravity.db.sql
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY web/ /var/www/html/admin/
COPY cli/pihole /usr/local/bin/pihole
COPY cli/gravity.sh /opt/pihole/gravity.sh
COPY cli/scripts/ /opt/pihole/
COPY cli/advanced /etc/.pihole/advanced
COPY pihole-adlist.sh /usr/local/bin/pihole-adlist
RUN chown -R pihole:pihole /etc/pihole /var/log/pihole /run/pihole /var/www/html/admin && \
    chmod 0755 /usr/bin/pihole-FTL /docker-entrypoint.sh /usr/local/bin/pihole /usr/local/bin/pihole-adlist /opt/pihole/gravity.sh
EXPOSE 53/udp 53/tcp 80
VOLUME ["/etc/pihole"]
ENTRYPOINT ["/docker-entrypoint.sh"]
