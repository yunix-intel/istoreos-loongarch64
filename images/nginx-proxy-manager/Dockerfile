FROM openeuler/openeuler:24.03 AS builder

RUN dnf install -y gcc gcc-c++ make python3 which tar gzip findutils ca-certificates \
 && dnf clean all \
 && rm -rf /var/cache/dnf

COPY node22/ /opt/node22/
ENV PATH=/opt/node22/bin:$PATH

RUN npm install -g yarn@1.22.22 node-gyp@10 --no-audit --no-fund

WORKDIR /app

COPY backend/package.json backend/yarn.lock ./
ENV npm_config_build_from_source=true \
    npm_config_nodedir=/opt/node22
RUN yarn install --frozen-lockfile --production --network-timeout 600000

COPY backend/ /app/

FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="Nginx Proxy Manager" \
      org.opencontainers.image.description="Docker container for managing Nginx proxy hosts (loong64)" \
      org.opencontainers.image.version="2.16.0" \
      org.opencontainers.image.vendor="jc21" \
      org.opencontainers.image.url="https://nginxproxymanager.com"

COPY node22/ /opt/node22/
ENV PATH=/opt/node22/bin:$PATH \
    NODE_ENV=production \
    SUPPRESS_NO_CONFIG_WARNING=1 \
    NODE_OPTIONS=--openssl-legacy-provider \
    NPM_BUILD_VERSION=2.16.0 \
    NPM_ADMIN_PORT=81

RUN dnf install -y nginx python3-certbot python3-acme logrotate jq curl ca-certificates tzdata shadow-utils findutils procps-ng tar gzip \
 && dnf clean all \
 && rm -rf /var/cache/dnf \
 && useradd -r -U -m -d /tmp/npmuserhome -s /sbin/nologin npm \
 && mkdir -p /etc/nginx/modules /run/nginx /tmp/nginx/body \
    /var/log/nginx /var/lib/nginx/cache/public /var/lib/nginx/cache/private \
    /var/cache/nginx/proxy_temp /data /etc/letsencrypt

COPY --from=builder /app /app
COPY frontend-dist/ /app/frontend/
COPY rootfs/ /

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/bin/check-health

EXPOSE 80 81 443

VOLUME [ "/data" ]

STOPSIGNAL SIGTERM

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
