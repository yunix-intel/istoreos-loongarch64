# Homarr v2.6.0 loong64 builder: Node 24 + pnpm (Bun is unavailable on loong64)
FROM openeuler/openeuler:24.03

RUN dnf install -y \
        python3 make gcc gcc-c++ pkgconf git tar xz findutils which \
        ca-certificates libstdc++ procps-ng \
    && dnf clean all

COPY src/node24 /opt/node24
ENV PATH=/opt/node24/bin:$PATH \
    npm_config_nodedir=/opt/node24 \
    CI=true

WORKDIR /app
COPY build/prepare-workspace.mjs /tmp/prepare-workspace.mjs
COPY src/homarr-2.6.0/ /app/
RUN node /tmp/prepare-workspace.mjs /app \
    && node --version && pnpm --version \
    && pnpm install --frozen-lockfile
