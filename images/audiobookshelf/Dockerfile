FROM openeuler/openeuler:24.03 AS nodebase
RUN dnf -y install ca-certificates tar gzip findutils shadow-utils && dnf clean all
COPY node22/ /usr/local/
ENV PATH=/usr/local/bin:$PATH     CI=true     npm_config_nodedir=/usr/local
RUN node -v && npm -v && npm install -g node-gyp@12.2.0 && node-gyp --version

# ---- TypeScript server (no native scripts) ----
FROM nodebase AS compile-server
WORKDIR /server
COPY src/package.json src/package-lock.json src/index.js src/tsconfig.server.json ./
COPY src/server/ ./server/
RUN npm ci --include=dev --ignore-scripts
RUN npm run build:server

# ---- Production deps incl. sqlite3 built from source for loong64 ----
FROM nodebase AS build-server
RUN dnf -y install gcc gcc-c++ make python3 && dnf clean all
ENV NODE_ENV=production     npm_config_build_from_source=true
WORKDIR /server
COPY src/package.json src/package-lock.json src/index.js ./
COPY src/server/ ./server/
COPY --from=compile-server /server/dist-server ./dist-server
RUN npm ci --omit=dev  && node -e "const s=require('sqlite3'); console.log('sqlite3 ok', s.VERSION)"

FROM openeuler/openeuler:24.03
RUN dnf -y install ca-certificates tzdata ffmpeg shadow-utils && dnf clean all
COPY node22/ /usr/local/
ENV PATH=/usr/local/bin:$PATH     NODE_ENV=production     PORT=13378     CONFIG_PATH=/config     METADATA_PATH=/metadata     SOURCE=docker     FFMPEG_PATH=/usr/bin/ffmpeg     FFPROBE_PATH=/usr/bin/ffprobe     NUSQLITE3_PATH=/usr/local/lib/nusqlite3/libnusqlite3.so     SKIP_BINARIES_CHECK=1
RUN useradd -r -u 1000 -d /app -s /sbin/nologin audiobookshelf  && mkdir -p /config /metadata  && chown 1000:1000 /config /metadata
WORKDIR /app
# Nuxt 2 client built on x64 (Tailwind 4 oxide has no loong64 binary)
COPY client-dist/ /app/client/dist/
COPY --from=build-server /server /app
COPY nusqlite/ /usr/local/lib/nusqlite3/
RUN echo 1.2 > /usr/local/lib/nusqlite3/libnusqlite3.so.ver  && chown -R 1000:1000 /app
USER 1000
EXPOSE 13378
CMD ["node", "dist-server/index.js"]
