# Grafana 13.2.4 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/grafana:loong64` / `:24.10-la5`
- 大小：1.18GB，`linux/loong64`
- digest：`sha256:5b4bd1fb478a1f368c796a021e75c83b6d83c281235a1ea8c93eb783dfd3f282`
- 版本：Grafana 13.2.4
- 验证：`/api/health` 返回 `database: ok`、`/login` 200、登录页 JS 资源 200、
  `grafana --version` 13.2.4、SQLite 自动迁移、健康检查 healthy。

## 构建链路

Grafana 的 `public` 是运行时静态目录，不打进 Go 二进制，因此分两步：

1. **x86_64 WSL2 构建前端**（Node 22.23.3 + 仓库自带 Yarn 4.17.1）：

```bash
export PATH=$HOME/node22/bin:$PATH
cd grafana
node .yarn/releases/yarn-4.17.1.cjs install --immutable
node .yarn/releases/yarn-4.17.1.cjs build
```

产物 `public/` 约 406MB，其中 `public/build/*.map` 占 189MB；镜像的 assets
阶段用 `find /public -name '*.map' -delete` 删除，最终 `public` 约 217MB。

2. **龙芯上构建 Go 后端**（Go 1.26.9 要求，本机用 1.27.2）：

```bash
export GOROOT=/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64
export PATH=$GOROOT/bin:$PATH GOTOOLCHAIN=local GOPROXY=https://goproxy.cn,direct
export GOCACHE=/build/gocache GOTMPDIR=/build/gotmp
unset GOFLAGS
export CGO_ENABLED=0 GOOS=linux GOARCH=loong64
go build -buildvcs=false -trimpath -tags oss \
  -ldflags "-s -w \
    -X main.version=13.2.4 \
    -X main.commit=$(git rev-parse HEAD) \
    -X main.buildBranch=v13.2.4 \
    -X main.buildstamp=$(date +%s)" \
  -o grafana ./pkg/cmd/grafana
```

Grafana 的 `go.work` 工作区与 `-mod=mod` 冲突，构建时必须清掉 `GOFLAGS`。
`/tmp` 只有 8GB tmpfs，Grafana 依赖编译会写满，必须把 `GOCACHE`/`GOTMPDIR`
指到 `/build`（22GB）。二进制约 347MB。

## 镜像组装

构建上下文：

```text
Dockerfile
grafana          # 347MB
public/          # 前端产物，map 已在 assets 阶段删除
defaults.ini     # 来自 conf/defaults.ini
grafana.ini      # 本仓库提供的最小配置
docker-entrypoint.sh
```

```bash
docker build -t grafana:loong64 .
docker tag grafana:loong64 yunixintel/grafana:loong64
docker tag grafana:loong64 yunixintel/grafana:24.10-la5
docker push yunixintel/grafana:loong64
docker push yunixintel/grafana:24.10-la5
```

## 运行时

```bash
docker run -d --name grafana -p 3000:3000 \
  -v grafana-data:/var/lib/grafana \
  yunixintel/grafana:loong64
```

- `http://<host>:3000/`，默认 `admin/admin`，首次登录会要求改密码。
- 容器以 UID/GID 472（`grafana`）运行；命名卷自动继承属主，挂宿主目录需
  `chown -R 472:472 <dir>`。
- 数据目录 `/var/lib/grafana`（含 `grafana.db`、插件、PNG/PDF 导出）；
  日志走 stdout，`docker logs` 可看。
- 配置：
  - `/etc/grafana/grafana.ini`：本仓库最小配置（路径、3000 端口、关闭
    usage analytics 和版本检查）。
  - `/usr/share/grafana/conf/defaults.ini`：Grafana 官方默认值。
  - `/etc/grafana/provisioning/`：数据源/仪表盘/告警 provisioning 目录。

## 注意

- 镜像只包含 Grafana 核心与内置数据源，不包含官方镜像里的额外 bundled 插件，
  也没有 Image Renderer（`grafana-image-renderer`）和 PhantomJS；需要图片渲染时
  另起 renderer 服务并在配置中指定。
- 默认 SQLite 适合家用；多副本或高并发应改用外部 PostgreSQL/MySQL，
  并设置 `[database]`。
- 对接本机 Prometheus 时，若 Grafana 用 bridge 网络，容器内 `127.0.0.1:9090`
  指向自己；应使用 `host.docker.internal`、宿主 IP 或 compose 服务名。
  Prometheus 数据源 URL 填 `http://<host>:9090`。
- 首次启动会自动迁移数据库；`/api/health` 返回 `database: ok` 才表示完成。
- 升级大版本前备份整个 `/var/lib/grafana`，不要只备份 `grafana.db`（插件和
  导出文件也在里面）。
- `check_for_updates=false` 关闭 Grafana 版本检查；插件更新检查仍可能访问网络，
  完全离线部署需在 `[plugins]` 中按需关闭。

## 验证命令

```bash
curl -fsS http://127.0.0.1:3000/api/health
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/login
docker exec grafana /usr/share/grafana/bin/grafana --version
docker exec grafana ls -la /var/lib/grafana
docker restart grafana
```
