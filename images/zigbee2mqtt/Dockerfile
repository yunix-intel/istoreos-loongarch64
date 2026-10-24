FROM yunixintel/node:24.22.1 AS build-base
ARG HTTPS_PROXY
ENV HTTPS_PROXY=${HTTPS_PROXY}
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo && \
    dnf install -y --setopt=install_weak_deps=False make gcc gcc-c++ python3 findutils && \
    dnf clean all && rm -rf /var/cache/dnf && \
    npm install -g pnpm@11.26.0
WORKDIR /app

FROM build-base AS build
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

FROM build-base AS prod-deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile --prod --no-optional && \
    pnpm rebuild @serialport/bindings-cpp && \
    find ./node_modules/.pnpm -type d -name prebuilds -prune -exec rm -rf {} +

FROM yunixintel/node:24.22.1
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo && \
    dnf install -y --setopt=install_weak_deps=False curl tzdata shadow util-linux systemd-udev && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -f dialout && \
    groupadd -g 1101 zigbee2mqtt && \
    useradd -u 1101 -g 1101 -G dialout -M -d /app -s /bin/bash zigbee2mqtt && \
    mkdir -p /app/data && chown -R zigbee2mqtt:zigbee2mqtt /app

WORKDIR /app
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json LICENSE index.js ./
COPY data/configuration.example.yaml ./configuration.example.yaml
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh && \
    chown -R zigbee2mqtt:zigbee2mqtt /app

ENV TZ=Asia/Shanghai \
    ZIGBEE2MQTT_DATA=/app/data
EXPOSE 8080
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
