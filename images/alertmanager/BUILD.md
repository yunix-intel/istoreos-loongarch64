# Alertmanager 0.34.1 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/alertmanager:loong64` / `:24.10-la5`
- 大小：274MB，`linux/loong64`
- digest：`sha256:6f46a30db0ddbb1490a4b6cd695ec38992858cdc84053c49da603b21731e8fca`
- 验证：`/-/healthy`、`/-/ready` 200；UI 200；`/api/v2/status` 返回集群/配置；
  `amtool alert add` 推入的测试告警可在 `/api/v2/alerts` 查到。

## 为什么前端要在 x86 上编

v0.34.1 的 Web UI 是 Elm + Vite（`ui/app`），Go 侧用 `//go:embed app/dist` 嵌入。
Vite 8/Rolldown 没有 `linux-loong64-gnu` 原生 binding，所以在 x86_64 WSL2 生成
架构无关的 `dist`，再拷到龙芯构建机。

`ui/mantine-ui/` 是上游未接入构建的实验目录；本版本只使用 `ui/app`，不需要构建
Mantine。

## 1. 取源码

```bash
git clone --depth 1 --branch v0.34.1 https://github.com/prometheus/alertmanager.git
```

## 2. x86_64 WSL2 构建前端

```bash
export PATH=$HOME/node22/bin:$PATH       # Node 22.23.3
cd alertmanager/ui/app
npm ci --no-audit --no-fund
npm run build                            # vite build，内含 elm 0.19.1
```

`vite.config.mjs` 设置 `base: "./"` 以便 `--web.route-prefix` 生效，并用
`vite-plugin-compression2` 生成 `.gz`/`.br` 并删除原文件；`ui/web.go` 按
`Accept-Encoding` 选择压缩版本，所以 `dist` 里只有压缩资源是正常的。

把 `ui/app/dist/` 整个目录拷到龙芯源码树的同一位置。

## 3. 龙芯上编 Go 二进制

```bash
export GOROOT=/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64
export PATH=$GOROOT/bin:$PATH GOTOOLCHAIN=local GOPROXY=https://goproxy.cn,direct
export CGO_ENABLED=0
LDFLAGS='-s -w \
  -X github.com/prometheus/common/version.Version=0.34.1 \
  -X github.com/prometheus/common/version.Revision=v0.34.1 \
  -X github.com/prometheus/common/version.Branch=HEAD \
  -X github.com/prometheus/common/version.BuildUser=loong64@build \
  -X github.com/prometheus/common/version.BuildDate=20261021-00:10:00'
go build -trimpath -tags netgo -ldflags "$LDFLAGS" -o alertmanager ./cmd/alertmanager
go build -trimpath -tags netgo -ldflags "$LDFLAGS" -o amtool      ./cmd/amtool
```

`netgo` 让解析走纯 Go，`CGO_ENABLED=0` 产出静态 ELF，可直接放入 openEuler
（glibc 2.38）运行，不依赖宿主 glibc 2.41。

## 4. 组装镜像

构建上下文需要：

```text
Dockerfile
alertmanager        # 33MB
amtool              # 20MB
alertmanager.yml    # 默认配置
```

```bash
docker build -t alertmanager:loong64 .
docker tag alertmanager:loong64 yunixintel/alertmanager:loong64
docker tag alertmanager:loong64 yunixintel/alertmanager:24.10-la5
docker push yunixintel/alertmanager:loong64
docker push yunixintel/alertmanager:24.10-la5
```

## 5. 启动注意

- 容器以 `65534:65534`（nobody）运行，`/alertmanager` 已在镜像内 chown。
  挂载宿主目录时需自行 `chown 65534:65534`，否则通知日志写入失败。
- 默认启用 gossip 集群监听 `9094`，单节点首次启动日志会出现
  `gossip not settled`，约十几秒后转为 settled，属正常现象。
  单机不需要 HA 时可加 `--cluster.listen-address=` 关闭。
- 默认配置的 `receivers.default` 没有任何集成，只接收告警、不发送通知；
  生产请挂载自己的 `alertmanager.yml`（webhook/邮件/企业微信等）。
- 配置文件可用 `amtool check-config /etc/alertmanager/alertmanager.yml` 预检。
- 与 Prometheus 对接时，在 `prometheus.yml` 写：

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ["127.0.0.1:9093"]
```

## 6. 验证命令

```bash
curl -fsS http://127.0.0.1:9093/-/healthy
curl -fsS http://127.0.0.1:9093/-/ready
curl -fsS http://127.0.0.1:9093/api/v2/status
amtool --alertmanager.url=http://127.0.0.1:9093 alert add \
  alertname=TestAlert severity=warning 'summary="smoke test"'
curl -fsS http://127.0.0.1:9093/api/v2/alerts
```
