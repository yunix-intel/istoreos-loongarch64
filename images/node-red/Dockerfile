FROM node:22.23.3-loong64 AS build
RUN npm install -g --unsafe-perm --omit=dev node-red@5.0.8 && \
    npm cache clean --force && rm -rf /root/.npm

FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        shadow util-linux ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1001 -M -d /data -s /sbin/nologin nodered && \
    mkdir -p /data
COPY --from=node:22.23.3-loong64 /opt/node22/bin /opt/node22/bin
COPY --from=node:22.23.3-loong64 /opt/node22/lib /opt/node22/lib
COPY --from=build /opt/node22/lib/node_modules/node-red /opt/node22/lib/node_modules/node-red
RUN ln -s ../lib/node_modules/node-red/red.js /opt/node22/bin/node-red && \
    chown -R nodered:nodered /data
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
ENV PATH=/opt/node22/bin:$PATH
EXPOSE 1880
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://127.0.0.1:1880/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
