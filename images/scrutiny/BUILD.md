# Scrutiny 0.9.5 (loong64) — 暂停，未发布

## 结论

- **状态：暂停，不发布镜像。**
- 原因：Scrutiny 0.8/0.9 的 Web 端启动时强制连接 InfluxDB 2.x；
  SQLite 只存设备元数据，SMART 历史在 InfluxDB。
- InfluxDB 2.8 在 loong64 上受阻：
  - `go.etcd.io/bbolt v1.3.6` 的 `maxMapSize`/`maxAllocSize` 没有 loongarch64 定义；
  - `github.com/influxdata/flux` 的 `libflux` C/Rust 库未构建。
- 改 Scrutiny 为纯 SQLite 涉及 28 个接口方法、166 处 Influx 引用，P1 阶段不做。
- 替代：`images/smartctl-exporter/`，把 SMART 指标交给现有 Prometheus/Grafana。

## 已完成的构建材料（备查）

- 后端：Go 1.25.1，`CGO_ENABLED=0`，可编出 `scrutiny-web` 与
  `scrutiny-collector-metrics`（LoongArch 静态 ELF）。
- 前端：Angular 13，必须用 Node 16.20 在 x86 构建。构建时需 polyfill：
  - `os.availableParallelism`（piscina）
  - `globalThis.crypto`（webpack）
- 启动验证：Web 端连 SQLite 成功后，立刻在 InfluxDB setup 检查处 panic。

Dockerfile/entrypoint 保留在本目录，若未来 InfluxDB 2.x 在 loong64 可用，可继续。

## 构建前端（x86 WSL2）

```bash
export PATH=$HOME/node16/bin:$PATH
cat > $HOME/node16-polyfill.cjs <<'EOF'
const os = require("os");
const crypto = require("crypto");
if (typeof os.availableParallelism !== "function")
  os.availableParallelism = () => os.cpus().length;
if (!globalThis.crypto) globalThis.crypto = crypto.webcrypto;
EOF
cd webapp/frontend
npm ci
NODE_OPTIONS=--require=$HOME/node16-polyfill.cjs \
  npm run build:prod -- --output-path=/tmp/scrutiny-dist
```

## 不要做什么

- 不要发布当前 `scrutiny` 镜像：没有 InfluxDB 会直接 panic。
- 不要用 `influxdb:2.8` x86 镜像 + QEMU 凑合；项目定位是原生 loong64。
- 不要把 Scrutiny 的 SQLite 当成 SMART 历史库；它只存设备元数据。
