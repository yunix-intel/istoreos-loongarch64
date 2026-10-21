FROM node:24.22.1-loong64 AS build
RUN dnf install -y --setopt=install_weak_deps=False gcc-c++ make python3 && \
    npm install -g --unsafe-perm @actual-app/sync-server@26.10.0 && \
    cd /opt/node24/lib/node_modules/@actual-app/sync-server/node_modules/better-sqlite3 && \
    npx node-gyp rebuild && \
    npm cache clean --force && rm -rf /root/.npm

FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        shadow util-linux ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1002 -M -d /data -s /sbin/nologin actual && \
    mkdir -p /data
COPY --from=node:24.22.1-loong64 /opt/node24/bin /opt/node24/bin
COPY --from=node:24.22.1-loong64 /opt/node24/lib /opt/node24/lib
COPY --from=build /opt/node24/lib/node_modules/@actual-app/sync-server /opt/node24/lib/node_modules/@actual-app/sync-server
RUN ln -s ../lib/node_modules/@actual-app/sync-server/build/bin/actual-server.js /opt/node24/bin/actual-server && \
    chown -R actual:actual /data
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
ENV PATH=/opt/node24/bin:$PATH \
    ACTUAL_DATA_DIR=/data \
    ACTUAL_PORT=5006
EXPOSE 5006
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=8 \
    CMD curl -fsS http://127.0.0.1:${ACTUAL_PORT:-5006}/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
