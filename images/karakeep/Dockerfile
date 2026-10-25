# Karakeep 0.34.1 (loong64), SQLite single-container base edition.
#
# The web (Next.js standalone) and workers bundles in artifacts/ are produced on
# an x86_64 build host. This Dockerfile only rebuilds the loong64 native bits:
#   - better-sqlite3 for every copy under artifacts/
#   - sharp is reused from yunixintel/node-sharp:24.22.1 (libvips 8.18.7)
# No Chromium is bundled; an external LBrowser sidecar can be enabled with
# BROWSER_WEB_URL (see BUILD.md).

FROM yunixintel/node-sharp:24.22.1 AS native
SHELL ["/bin/bash", "-c"]

RUN dnf install -y --setopt=install_weak_deps=False \
        gcc-c++ make python3 shadow util-linux findutils file && \
    dnf clean all && rm -rf /var/cache/dnf

RUN npm install -g node-gyp@12.4.0 && npm cache clean --force

ENV npm_config_nodedir=/opt/node24

COPY artifacts/ /artifacts/

# Rebuild better-sqlite3 for loong64 in every node_modules copy. --force_build=1
# is required: the npm tarball ships prebuilds for x64/arm64, which makes
# binding.gyp skip compilation otherwise.
RUN set -euxo pipefail; \
    find /artifacts -type d -path '*/node_modules/better-sqlite3' -print0 \
      | while IFS= read -r -d '' dir; do \
          echo "== node-gyp rebuild $dir"; \
          (cd "$dir" && node-gyp rebuild --force_build=1); \
          rm -rf "$dir/prebuilds" "$dir/deps" "$dir/src" "$dir/binding.gyp" "$dir/node_modules"; \
          rm -rf "$dir/build/Release/obj.target" "$dir/build/.deps"; \
          rm -f "$dir/build/Makefile" "$dir/build/binding.Makefile" "$dir/build/config.gypi" "$dir/build"/*.mk; \
        done; \
    echo "== rebuilt .node files"; \
    find /artifacts -name '*.node' -exec file {} \;


FROM yunixintel/node-sharp:24.22.1
SHELL ["/bin/bash", "-c"]

RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata curl shadow util-linux findutils file \
        GraphicsMagick ghostscript && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1116 karakeep && \
    useradd -u 1116 -g 1116 -M -d /data -s /sbin/nologin karakeep

COPY --from=native /artifacts/web /app
COPY --from=native /artifacts/workers /app/apps/workers
COPY --from=native /artifacts/db_migrations /app/db_migrations

# Reuse node-sharp's loong64 sharp addon inside each app-local sharp package
# (method C in docs/BASE-IMAGES.md). Then drop every non-LoongArch .node left
# over from the x86_64 build host.
RUN set -euxo pipefail; \
    src="$(find /opt/node_modules/sharp/src/build/Release -name 'sharp-linux-loong64-*.node' | head -n1)"; \
    test -n "$src"; \
    find /app -type d -name sharp -path '*/node_modules/*' -print0 \
      | while IFS= read -r -d '' dir; do \
          mkdir -p "$dir/src/build/Release"; \
          cp "$src" "$dir/src/build/Release/"; \
        done; \
    find /app -path '*/prebuilds/*.node' -delete; \
    find /app -path '*/@img/sharp-linux-*/*' -name '*.node' -delete; \
    find /app -path '*/@swc/*' -name '*.node' -delete; \
    find /app -path '*/re2/build/Release/*.node' -delete; \
    find /app -name '*.node' -exec file {} \;

COPY entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh && \
    mkdir -p /data/assets && \
    chown -R 1116:1116 /data

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    DATA_DIR=/data \
    ASSETS_DIR=/data/assets \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXTAUTH_URL_INTERNAL=http://127.0.0.1:3000 \
    DB_WAL_MODE=true \
    SERVER_VERSION=0.34.1 \
    HOME=/data

EXPOSE 3000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3000/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
