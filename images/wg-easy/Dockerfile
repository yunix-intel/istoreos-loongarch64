# wg-easy v15.4.0 (loong64)
#
# The build context must contain:
#   vendor/wg-easy-v15.4.0.tar.gz
#   vendor/pnpm-11.21.0.tgz
#   vendor/libsql/index.node
#   vendor/oxc-parser-binding/{package.json,parser.linux-loong64-gnu.node}
#   vendor/oxc-transform-binding/{package.json,transform.linux-loong64-gnu.node}
#   vendor/rolldown-binding/{package.json,rolldown-binding.linux-loong64-gnu.node}
#   vendor/lightningcss-binding/lightningcss.linux-loong64-gnu.node
# See BUILD.md for provenance and SHA-256 values.

ARG NODE_IMAGE=yunixintel/node:24.22.1

FROM ${NODE_IMAGE} AS build
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tar gzip patch findutils && \
    dnf clean all && rm -rf /var/cache/dnf

WORKDIR /src
COPY vendor/wg-easy-v15.4.0.tar.gz /tmp/wg-easy.tar.gz
RUN echo "87aa90b91bd22309d4c4a27e49a340a243582821e3964b6a878e865e88efc05c  /tmp/wg-easy.tar.gz" | sha256sum -c - && \
    tar xzf /tmp/wg-easy.tar.gz && \
    test -d /src/wg-easy-15.4.0/src

WORKDIR /src/wg-easy-15.4.0/src
COPY patches/0001-replace-argon2-with-hash-wasm.patch /tmp/
RUN patch -p1 --batch < /tmp/0001-replace-argon2-with-hash-wasm.patch

# pnpm 11.21.0 is pure JS and matches the upstream packageManager field.
COPY vendor/pnpm-11.21.0.tgz /tmp/pnpm.tgz
RUN mkdir -p /opt/pnpm && \
    echo "87237d37eadb79dc626a0576eb3a52d23d70422c323ae5e00fc05c91f4323780  /tmp/pnpm.tgz" | sha256sum -c - && \
    tar xzf /tmp/pnpm.tgz -C /opt/pnpm --strip-components=1
RUN node /opt/pnpm/bin/pnpm.cjs install --ignore-scripts --no-frozen-lockfile

# Four loong64 native bindings that upstream's lockfile/platform filter cannot fetch.
COPY vendor/libsql/index.node /vendor/libsql-index.node
COPY vendor/oxc-parser-binding/ /vendor/oxc-parser-binding/
COPY vendor/oxc-transform-binding/ /vendor/oxc-transform-binding/
COPY vendor/rolldown-binding/ /vendor/rolldown-binding/
COPY vendor/lightningcss-binding/lightningcss.linux-loong64-gnu.node /vendor/
RUN set -eux; \
    mkdir -p node_modules/@oxc-parser/binding-linux-loong64-gnu; \
    cp -a /vendor/oxc-parser-binding/. node_modules/@oxc-parser/binding-linux-loong64-gnu/; \
    mkdir -p node_modules/@oxc-transform/binding-linux-loong64-gnu; \
    cp -a /vendor/oxc-transform-binding/. node_modules/@oxc-transform/binding-linux-loong64-gnu/; \
    mkdir -p node_modules/@rolldown/binding-linux-loong64-gnu; \
    cp -a /vendor/rolldown-binding/. node_modules/@rolldown/binding-linux-loong64-gnu/; \
    LCSS=$(find node_modules/.pnpm -maxdepth 1 -type d -name 'lightningcss@1.33.0' | head -1); \
    cp /vendor/lightningcss.linux-loong64-gnu.node "$LCSS/node_modules/lightningcss/"; \
    LIBSQL=$(find node_modules/.pnpm -maxdepth 4 -type d -path '*/libsql@0.5.29/node_modules/libsql' | head -1); \
    cp /vendor/libsql-index.node "$LIBSQL/index.node"

# pnpm scripts call `pnpm` again (cli:trace && nuxt build && cli:build).
RUN printf '#!/bin/sh\nexec node /opt/pnpm/bin/pnpm.cjs "$@"\n' > /usr/local/bin/pnpm && \
    chmod 0755 /usr/local/bin/pnpm
RUN node /opt/pnpm/bin/pnpm.cjs build

# Nitro traces the libsql package but not its native .node; inject it after the build.
RUN set -eux; \
    LIBSQL=$(find node_modules/.pnpm -maxdepth 4 -type d -path '*/libsql@0.5.29/node_modules/libsql' | head -1); \
    cp "$LIBSQL/index.node" .output/server/node_modules/libsql/index.node

FROM ${NODE_IMAGE}
# EPOL must stay enabled: wireguard-tools is only in openEuler EPOL.
RUN dnf install -y --setopt=install_weak_deps=False \
        wireguard-tools iproute iptables procps-ng && \
    dnf clean all && rm -rf /var/cache/dnf

WORKDIR /app
COPY --from=build /src/wg-easy-15.4.0/src/.output /app
COPY --from=build /src/wg-easy-15.4.0/src/server/database/migrations /app/server/database/migrations
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh

ENV PATH=/opt/node24/bin:$PATH \
    TZ=Asia/Shanghai \
    LIBSQL_JS_DEV=1 \
    PORT=51821 \
    HOST=0.0.0.0 \
    INSECURE=false \
    INIT_ENABLED=false \
    DISABLE_IPV6=false \
    DEBUG=Server,WireGuard,Database,CMD,Firewall

VOLUME ["/etc/wireguard"]
EXPOSE 51820/udp 51821/tcp
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD wg show | grep -q interface || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
