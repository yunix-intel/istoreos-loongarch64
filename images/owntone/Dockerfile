FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux \
        libconfuse libevent json-c libsodium libplist libcurl libgcrypt libunistring \
        sqlite-libs ffmpeg libwebsockets avahi avahi-tools avahi-libs dbus alsa-lib openssl-libs libxml2 zlib && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 995 owntone && useradd -u 998 -g 995 -M -d /var/lib/owntone -s /sbin/nologin owntone && \
    mkdir -p /srv/music /var/cache/owntone /var/log/owntone && \
    chown -R owntone:owntone /srv/music /var/cache/owntone /var/log/owntone
COPY owntone /usr/sbin/owntone
COPY libowntone /usr/lib/owntone
COPY share /usr/share/owntone
COPY owntone.conf /etc/owntone.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/sbin/owntone /usr/local/bin/docker-entrypoint.sh
EXPOSE 3689
VOLUME ["/srv/music", "/var/cache/owntone"]
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:3689/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
