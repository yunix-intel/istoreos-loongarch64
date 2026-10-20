# Homarr v2.6.0 loong64 image
# Build: homarr-builder:loong64 (Dockerfile.builder) + build/build-homarr.sh,
# because Bun and Turborepo have no loong64 builds and Next 16 has no loong64
# SWC/Turbopack binary. Next is built with --webpack + @next/swc-wasm-nodejs.
# Artifacts are extracted to build/artifacts/ from the build container.
FROM openeuler/openeuler:24.03

RUN dnf install -y \
        nginx redis gettext bash openssl ca-certificates curl libstdc++ util-linux shadow \
    && dnf clean all \
    && mkdir -p /appdata /var/cache/nginx /var/log/nginx /var/lib/nginx \
        /run/nginx /etc/nginx/templates /etc/nginx/ssl/certs \
    && touch /run/nginx/nginx.pid

WORKDIR /app

# Node 24.22.0 (loong64) from /opt/node24; only libc/libm are required.
COPY src/node24/bin/node /usr/local/bin/node

COPY build/artifacts/standalone/ /app/
COPY build/artifacts/cli.cjs /app/apps/cli/cli.cjs
COPY build/artifacts/migrations/ /app/db/migrations/
COPY build/artifacts/better_sqlite3.node /app/build/better_sqlite3.node
COPY src/homarr-2.6.0/scripts/run.sh /app/run.sh
COPY src/homarr-2.6.0/scripts/trusted-proxies.mjs /app/scripts/trusted-proxies.mjs
COPY src/homarr-2.6.0/scripts/entrypoint.sh /app/entrypoint.sh
COPY src/homarr-2.6.0/packages/redis/redis.conf /app/redis.conf
COPY src/homarr-2.6.0/nginx.conf /etc/nginx/templates/nginx.conf

RUN chmod +x /app/run.sh /app/entrypoint.sh \
    && sed -i 's|exec su-exec $PUID:$PGID "$@"|exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups "$@"|' /app/entrypoint.sh \
    && printf '#!/bin/sh\ncd /app/apps/cli && exec node ./cli.cjs "$@"\n' > /usr/bin/homarr \
    && chmod +x /usr/bin/homarr

ENV DB_URL=/appdata/db/db.sqlite \
    DB_DIALECT=sqlite \
    DB_DRIVER=better-sqlite3 \
    AUTH_PROVIDERS=credentials \
    REDIS_IS_EXTERNAL=false \
    NODE_ENV=production

VOLUME ["/appdata"]
EXPOSE 7575

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:7575/ >/dev/null || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh", "run.sh"]
