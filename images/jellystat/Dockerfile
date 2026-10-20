FROM openeuler/openeuler:24.03 AS builder

# Vite 6 + @vitejs/plugin-react (Babel) are used because Vite 8's
# Rolldown and @swc/core have no linux-loong64 native bindings.
RUN dnf install -y nodejs npm \
    && dnf clean all \
    && rm -rf /var/cache/dnf

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="Jellystat" \
      org.opencontainers.image.version="1.1.12" \
      org.opencontainers.image.source="https://github.com/CyferShepard/Jellystat"

ENV NODE_ENV=production \
    TZ=UTC \
    HOME=/tmp \
    NPM_CONFIG_CACHE=/tmp/.npm

RUN dnf install -y nodejs npm shadow-utils \
    && dnf clean all \
    && rm -rf /var/cache/dnf

WORKDIR /app
COPY --from=builder /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/backend ./backend
COPY entry.sh /entry.sh

RUN chmod 755 /entry.sh \
    && mkdir -p /app/data \
    && ln -s /app/data /app/backend/backup-data \
    && groupadd -g 1000 jellystat \
    && useradd -u 1000 -g 1000 -M -d /app/data -s /sbin/nologin jellystat \
    && chown -R 1000:1000 /app

VOLUME /app/data
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:3000/auth/isConfigured || exit 1

USER 1000:1000
CMD ["/entry.sh"]
