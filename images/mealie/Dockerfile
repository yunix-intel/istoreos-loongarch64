FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl shadow util-linux bash \
        libpq libwebp libjpeg-turbo libxml2 libxslt openldap cyrus-sasl-lib \
        ffmpeg libcurl libstdc++ openssl-libs sqlite-libs bzip2-libs xz-libs \
        zlib readline ncurses-libs libffi gdbm && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 911 -M -d /app -s /bin/bash abc && \
    mkdir -p /app/data && chown -R abc:abc /app
COPY usrlocal/ /usr/local/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh /usr/local/bin/mealie
ENV PATH=/usr/local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEALIE_HOME=/app \
    DATA_DIR=/app/data \
    PRODUCTION=true \
    TZ=Etc/UTC
WORKDIR /app
VOLUME ["/app/data"]
EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:9000/api/app/about >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
