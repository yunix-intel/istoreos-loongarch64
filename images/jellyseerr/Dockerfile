FROM openeuler/openeuler:24.03 AS nodebase
RUN dnf -y install ca-certificates tar gzip findutils shadow-utils && dnf clean all
COPY node22/ /usr/local/
ENV PATH=/usr/local/bin:$PATH     CI=true     COREPACK_ENABLE_DOWNLOAD_PROMPT=0     CYPRESS_INSTALL_BINARY=0     NEXT_TELEMETRY_DISABLED=1     npm_config_nodedir=/usr/local
RUN node -v && npm -v  && corepack enable  && corepack prepare pnpm@10.24.0 --activate  && npm install -g node-gyp@12.2.0  && pnpm -v && node-gyp --version

FROM nodebase AS build
RUN dnf -y install gcc gcc-c++ make python3 && dnf clean all
WORKDIR /app
COPY src/ /app/
RUN pnpm install --frozen-lockfile
# Next 16 defaults to Turbopack, which has no loong64 binding; force webpack + SWC WASM.
# The upstream config only declares an SVGR rule for Turbopack, so add the webpack one.
COPY patch/next.config.ts /app/next.config.ts
RUN pnpm build:server
RUN pnpm exec next build --webpack
RUN rm -rf .next/cache

FROM nodebase AS prod-deps
RUN dnf -y install gcc gcc-c++ make python3 && dnf clean all
WORKDIR /app
COPY src/ /app/
RUN pnpm install --prod --frozen-lockfile

FROM openeuler/openeuler:24.03
RUN dnf -y install ca-certificates tzdata shadow-utils && dnf clean all
COPY node22/ /usr/local/
ENV PATH=/usr/local/bin:$PATH     NODE_ENV=production     NEXT_TELEMETRY_DISABLED=1     PORT=5055
RUN useradd -r -u 1000 -d /app -s /sbin/nologin jellyseerr
WORKDIR /app
COPY src/ /app/
COPY --from=prod-deps /app/node_modules /app/node_modules
COPY --from=build /app/.next /app/.next
COPY --from=build /app/dist /app/dist
# Runtime must not parse next.config.ts (needs SWC); use plain JS config.
COPY patch/next.config.js /app/next.config.js
RUN rm -f /app/next.config.ts  && mkdir -p /app/config  && touch /app/config/DOCKER  && echo '{"commitTag":"v3.5.0"}' > /app/committag.json  && chown -R 1000:1000 /app
USER 1000
EXPOSE 5055
CMD ["node", "dist/index.js"]
