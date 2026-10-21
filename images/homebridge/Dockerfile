FROM node:22.23.3-loong64 AS build
RUN dnf install -y --setopt=install_weak_deps=False gcc-c++ make python3 git && \
    npm install -g --unsafe-perm --ignore-scripts \
        homebridge@2.4.0 homebridge-config-ui-x@5.29.0 && \
    git clone --depth 1 --branch v0.14.1 \
        https://github.com/homebridge/node-pty-prebuilt-multiarch.git /tmp/node-pty && \
    cd /tmp/node-pty && \
    npm install --ignore-scripts && \
    npx node-gyp rebuild && \
    mkdir -p /opt/node22/lib/node_modules/homebridge-config-ui-x/node_modules/@homebridge/node-pty-prebuilt-multiarch/build/Release && \
    cp build/Release/pty.node \
        /opt/node22/lib/node_modules/homebridge-config-ui-x/node_modules/@homebridge/node-pty-prebuilt-multiarch/build/Release/pty.node && \
    npm cache clean --force && rm -rf /root/.npm

FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        shadow util-linux ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1000 -M -d /homebridge -s /sbin/nologin homebridge && \
    mkdir -p /homebridge /usr/local/share/homebridge && \
    chown -R homebridge:homebridge /homebridge
COPY --from=node:22.23.3-loong64 /opt/node22/bin /opt/node22/bin
COPY --from=node:22.23.3-loong64 /opt/node22/lib /opt/node22/lib
COPY --from=build /opt/node22/lib/node_modules/homebridge /opt/node22/lib/node_modules/homebridge
COPY --from=build /opt/node22/lib/node_modules/homebridge-config-ui-x /opt/node22/lib/node_modules/homebridge-config-ui-x
RUN ln -s ../lib/node_modules/homebridge/bin/homebridge.js /opt/node22/bin/homebridge
COPY config.json /usr/local/share/homebridge/config.json
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh /opt/node22/bin/homebridge
ENV PATH=/opt/node22/bin:$PATH
EXPOSE 8581 51826
VOLUME ["/homebridge"]
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:8581/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
