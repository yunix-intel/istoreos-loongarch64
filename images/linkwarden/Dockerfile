# Linkwarden 2.16.3 (loong64), web + worker in one container.
#
# Next.js is built on x86_64 (no @next/swc for loong64) and the resulting .next
# is plain JS. Runtime needs no Prisma or sharp native binaries:
#   - Prisma 7.10.1 query compiler is WASM; @prisma/adapter-pg uses `pg`
#   - sharp is removed and images.unoptimized is set
#   - bcrypt is replaced by bcryptjs
#   - tsx/esbuild runs the worker; the loong64 @esbuild binary is in artifacts/
# Chromium is NOT bundled. Point PLAYWRIGHT_WS_URL at an LBrowser sidecar, or
# set DISABLE_BROWSER=true for bookmark CRUD without preservation.

FROM yunixintel/node:24.22.1

SHELL ["/bin/bash", "-c"]

RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata bash util-linux shadow && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1118 linkwarden && \
    useradd -u 1118 -g 1118 -M -d /data -s /sbin/nologin linkwarden

WORKDIR /data

# artifacts/ is produced on x86_64 (see BUILD.md) and is not committed.
COPY --chown=1118:1118 artifacts/ /data/
COPY prisma-migrate.mjs /data/scripts/prisma-migrate.mjs
COPY entrypoint.sh /entrypoint.sh

RUN chmod 0755 /entrypoint.sh && \
    chmod 0755 /data/node_modules/@esbuild/linux-loong64/bin/esbuild && \
    mkdir -p /data/data && \
    chown 1118:1118 /data/data

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    HOME=/data \
    STORAGE_FOLDER=data \
    PRISMA_HIDE_UPDATE_MESSAGE=1 \
    NEXT_TELEMETRY_DISABLED=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

EXPOSE 3000

# Upstream keeps the app itself in /data and archives in /data/data; mount this
# path (./linkwarden-data:/data/data) to persist archives.
VOLUME ["/data/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3000/ >/dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
