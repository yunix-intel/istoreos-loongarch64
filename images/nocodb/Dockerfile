FROM node:24.22.1-loong64 AS build
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        gcc-c++ make python3 && \
    npm install -g --ignore-scripts nocodb@0.301.3 && \
    cd /opt/node24/lib/node_modules/nocodb/node_modules/sqlite3 && \
    npx node-gyp rebuild && \
    npm cache clean --force && rm -rf /root/.npm

FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl shadow util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1000 -M -d /data -s /sbin/nologin nocodb && \
    mkdir -p /data && chown -R nocodb:nocodb /data
COPY --from=node:24.22.1-loong64 /opt/node24/bin /opt/node24/bin
COPY --from=node:24.22.1-loong64 /opt/node24/lib /opt/node24/lib
COPY --from=build /opt/node24/lib/node_modules/nocodb /opt/node24/lib/node_modules/nocodb
COPY docker-main.js /opt/node24/lib/node_modules/nocodb/docker-main.js
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
ENV PATH=/opt/node24/bin:$PATH \
    NODE_ENV=production \
    PORT=8080 \
    NC_TOOL_DIR=/data \
    NC_DB="sqlite3://?d=/data/noco.db" \
    NC_DISABLE_TELE=true
EXPOSE 8080
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:8080/api/v1/health >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
