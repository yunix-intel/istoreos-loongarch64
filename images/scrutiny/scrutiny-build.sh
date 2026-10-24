#!/bin/sh
# Reproducible build for Scrutiny 0.9.5 with a SQLite SMART-metrics backend.
# Target: linux/loong64 (LoongArch64). No QEMU / no x86 runtime dependency.
set -eu

SRC=/build/scrutiny-src
IMGCTX=/build/scrutiny-image
PATCH=/build/scrutiny-sqlite.patch
GOPROXY_URL=https://goproxy.cn,direct
NPM_REGISTRY=https://registry.npmmirror.com

rm -rf "$SRC"
git clone --depth 1 --branch v0.9.5 https://github.com/AnalogJ/scrutiny.git "$SRC"
cd "$SRC"
git apply "$PATCH"

# Go binaries: native amd64 (for validation) and loong64 (for the image).
# glebarez/sqlite is pure Go, so CGO_ENABLED=0 is sufficient for both.
docker run --rm -v "$SRC":/src -w /src \
  -e GOPROXY="$GOPROXY_URL" -e CGO_ENABLED=0 \
  golang:1.25-trixie sh -c "
    go build -trimpath -ldflags \"-s -w\" -o bin/scrutiny ./webapp/backend/cmd/scrutiny
    go build -trimpath -ldflags \"-s -w\" -o bin/scrutiny-collector-metrics ./collector/cmd/collector-metrics
    GOOS=linux GOARCH=loong64 go build -trimpath -ldflags \"-s -w\" -o bin/loong64/scrutiny ./webapp/backend/cmd/scrutiny
    GOOS=linux GOARCH=loong64 go build -trimpath -ldflags \"-s -w\" -o bin/loong64/scrutiny-collector-metrics ./collector/cmd/collector-metrics
  "

# Angular frontend (static files only).
docker run --rm -v "$SRC":/src -w /src/webapp/frontend \
  -e NODE_OPTIONS=--max-old-space-size=4096 -e NG_CLI_ANALYTICS=false node:20 sh -c "
    npm config set registry $NPM_REGISTRY
    npm ci --no-audit --no-fund
    npx ng build --configuration production --output-path=/src/dist
  "

# openEuler 24.03 LTS loongarch64 root filesystem (Docker Hub has no loong64 tag).
cd /build
test -f openEuler-docker.loongarch64.tar || xz -dk openEuler-docker.loongarch64.tar.xz
docker load -i openEuler-docker.loongarch64.tar

# smartmontools 7.3 for loongarch64 (from the openEuler 24.03 repo).
test -f smartmontools.rpm || curl -sL -o smartmontools.rpm \
  https://repo.openeuler.org/openEuler-24.03-LTS/OS/loongarch64/Packages/smartmontools-7.3-1.oe2403.loongarch64.rpm
rm -rf /build/smartmontools-root && mkdir -p /build/smartmontools-root
bsdtar -xf smartmontools.rpm -C /build/smartmontools-root

# Assemble a COPY-only image (no RUN under emulation).
rm -rf "$IMGCTX" && mkdir -p "$IMGCTX/bin" "$IMGCTX/web" "$IMGCTX/drivedb"
cp "$SRC"/bin/loong64/scrutiny "$SRC"/bin/loong64/scrutiny-collector-metrics "$IMGCTX"/bin/
cp -r "$SRC"/dist/. "$IMGCTX"/web/
cp /build/smartmontools-root/usr/sbin/smartctl "$IMGCTX"/smartctl
cp -r /build/smartmontools-root/usr/share/smartmontools/. "$IMGCTX"/drivedb/

cat > "$IMGCTX/scrutiny.yaml" <<YAML
version: 1
web:
  listen:
    host: 0.0.0.0
    port: 8080
  database:
    location: /opt/scrutiny/config/scrutiny.db
  src:
    frontend:
      path: /opt/scrutiny/web
log:
  level: INFO
YAML

cat > "$IMGCTX/collector.yaml" <<YAML
version: 1
host:
  id: ""
api:
  endpoint: http://127.0.0.1:8080
YAML

cat > "$IMGCTX/entrypoint.sh" <<SH
#!/bin/sh
set -e
mkdir -p /opt/scrutiny/config
if [ "\$1" = "collector" ]; then
  shift
  exec scrutiny-collector-metrics run "\$@"
fi
exec scrutiny start --config /opt/scrutiny/config/scrutiny.yaml
SH
chmod +x "$IMGCTX/entrypoint.sh"

cat > "$IMGCTX/Dockerfile" <<DOCKER
FROM openeuler-24.03-lts:latest
EXPOSE 8080
WORKDIR /opt/scrutiny
ENV PATH="/opt/scrutiny/bin:\${PATH}"
COPY bin/scrutiny /opt/scrutiny/bin/scrutiny
COPY bin/scrutiny-collector-metrics /opt/scrutiny/bin/scrutiny-collector-metrics
COPY web /opt/scrutiny/web
COPY smartctl /usr/sbin/smartctl
COPY drivedb /usr/share/smartmontools
COPY scrutiny.yaml /opt/scrutiny/config/scrutiny.yaml
COPY collector.yaml /opt/scrutiny/config/collector.yaml
COPY entrypoint.sh /entrypoint.sh
CMD ["/entrypoint.sh"]
DOCKER

docker build --platform linux/loong64 -t scrutiny:loong64-test "$IMGCTX"
