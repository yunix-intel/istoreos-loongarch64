# Joplin Server 3.7.21 for linux/loong64
#
# The build context is the upstream source tree at tag v3.7.21
# (commit e41516e669efb693b009bedb21f3eb1fcbea4fc9), restricted to the
# workspaces listed in upstream Dockerfile.server. No x86 frontend stage is
# needed: the web UI is Mustache + static assets.
#
# Build:
#   docker build -t joplin-server:loong64 .

FROM yunixintel/node:24.22.1 AS build

RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL \
      --setopt=install_weak_deps=False --setopt=retries=1 --setopt=timeout=30 \
      gcc-c++ make python3 findutils && \
    dnf clean all && rm -rf /var/cache/dnf

ENV NODE_OPTIONS=--max-old-space-size=4096

WORKDIR /build

# Upstream Dockerfile.server COPY list. desktop/mobile/cli are deliberately
# absent: they are not server workspaces and pull large native toolchains.
COPY .yarn/releases ./.yarn/releases
COPY .yarn/patches ./.yarn/patches
COPY package.json .yarnrc.yml yarn.lock gulpfile.js tsconfig.json ./
COPY patch-package-json.js ./
COPY packages/turndown ./packages/turndown
COPY packages/turndown-plugin-gfm ./packages/turndown-plugin-gfm
COPY packages/fork-htmlparser2 ./packages/fork-htmlparser2
COPY packages/fork-sax ./packages/fork-sax
COPY packages/fork-uslug ./packages/fork-uslug
COPY packages/htmlpack ./packages/htmlpack
COPY packages/renderer ./packages/renderer
COPY packages/tools ./packages/tools
COPY packages/utils ./packages/utils
COPY packages/lib ./packages/lib
COPY packages/server ./packages/server

# onenote-converter (unused by the server) is removed, workspace postinstall
# hooks are disabled, and @joplin/turndown's Rollup is aliased to the matching
# @rollup/wasm-node because Rollup 4.2.0 has no loong64 native binding. See
# patch-package-json.js and BUILD.md for details.
RUN node patch-package-json.js

# Scripts are disabled during install: sharp, onnxruntime-node and sqlite-vec
# are dev dependencies that would otherwise try to download x86/ARM artifacts.
# sqlite3 is compiled from source in the next step.
RUN YARN_ENABLE_SCRIPTS=false \
    node .yarn/releases/yarn-4.16.0.cjs install --inline-builds

# Compile sqlite3 5.1.6 from source against the image's Node headers.
# nmHoistingLimits: workspaces gives lib/server/tools their own sqlite3 copy,
# so every copy must be rebuilt. With Node 24 node-pre-gyp selects
# napi-v6-linux-glibc-loong64.
RUN for SQLITE_DIR in $(find /build/packages -maxdepth 4 -type d -path '*/node_modules/sqlite3' | sort); do \
      echo "=== sqlite3: $SQLITE_DIR ==="; \
      NPRE=$(find "$SQLITE_DIR/../.bin" -maxdepth 1 -name node-pre-gyp | head -1); \
      if [ -z "$NPRE" ]; then NPRE=$(find /build -path '*/node_modules/.bin/node-pre-gyp' | head -1); fi; \
      ( cd "$SQLITE_DIR" && npm_config_nodedir=/opt/node24 JOBS=max \
          "$NPRE" rebuild --build-from-source ); \
    done && \
    find /build/packages -path '*/lib/binding/napi-v6-linux-glibc-loong64/node_sqlite3.node' \
      -exec ls -l {} \;

# TypeScript build for every workspace, then prune to the production closure of
# @joplin/server only. Never use "--all" here: that would keep @joplin/tools
# and its sharp production dependency in the runtime tree.
RUN BUILD_SEQUENCIAL=1 \
      node .yarn/releases/yarn-4.16.0.cjs run buildSequential && \
    YARN_ENABLE_SCRIPTS=false \
      node .yarn/releases/yarn-4.16.0.cjs workspaces focus --production @joplin/server && \
    cd /build/packages/server && node -e "const s=require('sqlite3'); const db=new s.Database(':memory:'); db.get('select sqlite_version() v',(e,r)=>{if(e){console.error(e);process.exit(1)};console.log('sqlite3 ok',r);db.close()})"

FROM openeuler/openeuler:24.03

RUN dnf install -y --setopt=install_weak_deps=False \
      shadow util-linux ca-certificates tzdata curl libstdc++ && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1119 joplin && \
    useradd -u 1119 -g 1119 -M -d /data -s /sbin/nologin joplin && \
    mkdir -p /data/logs /data/temp /data/resource /data/storage /opt/joplin && \
    chown 1119:1119 /data /data/logs /data/temp /data/resource /data/storage

COPY --from=build /opt/node24 /opt/node24
COPY --from=build /build/packages /opt/joplin/packages

# Server derives temp/resource/logs from dirname(__dirname) = packages/server.
# Persist them under /data; /data/logs and /data/temp are required for sync
# and share-page rendering even when PostgreSQL is the main database.
RUN ln -s /data/logs /opt/joplin/packages/server/logs && \
    ln -s /data/temp /opt/joplin/packages/server/temp && \
    ln -s /data/resource /opt/joplin/packages/server/resource

COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENV PATH=/opt/node24/bin:$PATH \
    NODE_ENV=production \
    RUNNING_IN_DOCKER=1 \
    APP_PORT=22300 \
    APP_NAME="Joplin Server"

WORKDIR /opt/joplin/packages/server

VOLUME ["/data"]
EXPOSE 22300

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=5 \
    CMD base="${APP_BASE_URL:-http://localhost:22300}"; hostport="${base#http://}"; hostport="${hostport%%/*}"; curl -fsS -H "Host: ${hostport}" "http://127.0.0.1:${APP_PORT:-22300}/api/ping" >/dev/null || exit 1

LABEL org.opencontainers.image.title="Joplin Server" \
      org.opencontainers.image.description="Joplin sync server for linux/loong64" \
      org.opencontainers.image.url="https://joplinapp.org/" \
      org.opencontainers.image.source="https://github.com/laurent22/joplin" \
      org.opencontainers.image.revision="e41516e669efb693b009bedb21f3eb1fcbea4fc9" \
      org.opencontainers.image.version="3.7.21"

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
