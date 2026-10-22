FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux \
        java-21-openjdk-headless fontconfig fontforge ImageMagick librsvg2 \
        python3 python3-tabulate woff2 && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1001 penpot && useradd -u 1001 -g 1001 -M -d /opt/penpot -s /bin/false penpot && \
    mkdir -p /opt/penpot/backend /opt/data/assets && \
    chown -R penpot:penpot /opt/penpot /opt/data
COPY app/ /opt/penpot/backend/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh && chown -R penpot:penpot /opt/penpot/backend
ENV PENPOT_PUBLIC_URI=http://localhost:9001 \
    PENPOT_HTTP_SERVER_PORT=6060 \
    PENPOT_OBJECTS_STORAGE_BACKEND=fs \
    PENPOT_OBJECTS_STORAGE_FS_DIRECTORY=/opt/data/assets
WORKDIR /opt/penpot/backend
EXPOSE 6060
VOLUME ["/opt/data/assets"]
USER penpot
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
