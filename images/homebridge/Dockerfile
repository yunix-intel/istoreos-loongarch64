FROM openeuler/openeuler:24.03 AS build
RUN dnf install -y --setopt=install_weak_deps=False \
        nodejs npm gcc-c++ make python3 && \
    npm install -g --unsafe-perm \
        homebridge@1.11.4 homebridge-config-ui-x@4.80.0 && \
    npm cache clean --force && rm -rf /root/.npm

FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        nodejs npm shadow util-linux ca-certificates tzdata curl && \
    dnf clean all && rm -rf /var/cache/dnf && \
    useradd -u 1000 -M -d /homebridge -s /sbin/nologin homebridge && \
    mkdir -p /homebridge /usr/local/share/homebridge && \
    chown -R homebridge:homebridge /homebridge
COPY --from=build /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/homebridge/bin/homebridge /usr/local/bin/homebridge
COPY config.json /usr/local/share/homebridge/config.json
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh /usr/local/bin/homebridge
EXPOSE 8581 51826
VOLUME ["/homebridge"]
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:8581/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
