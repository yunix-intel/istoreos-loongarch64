# Homebox v0.10.3 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/homebox:loong64` / `:24.10-la5`
- 大小：346MB，`linux/loong64`
- digest：`sha256:6aad740083ab7721f8c2a8a21b57c5effda0ecfd955fb5cf7cb9e61387a80c12`
- 版本：Homebox v0.10.3（Go 1.27.2 + Nuxt 3.6.5 静态前端）
- 验证：`/` 200、`/api/v1/status` health=true、版本 v0.10.3、SQLite 初始化、
  健康检查 healthy。

## 构建

Homebox 官方只发布 x86/ARM 资产，loong64 走源码构建。

### 1. 前端（x86_64 WSL2）

```bash
export PATH=$HOME/node22/bin:$PATH
npm install -g pnpm@8.15.9
cd frontend
pnpm install --frozen-lockfile --shamefully-hoist
pnpm build
```

- `--shamefully-hoist` 必须加：否则 Vite 解析不到 PWA 的 `workbox-window`，
  构建报 `Rollup failed to resolve import "workbox-window"`。
- 产物 `.output/public` 约 1.2MB，架构无关。

### 2. 后端（龙芯）

把 `.output/public` 放到 `backend/app/api/static/public`（对应
`//go:embed all:static/public/*`），然后：

```bash
cd backend
export GOROOT=/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64
export PATH=$GOROOT/bin:$PATH GOTOOLCHAIN=local GOPROXY=https://goproxy.cn,direct
export GOCACHE=/build/gocache GOTMPDIR=/build/gotmp
unset GOFLAGS

# v0.10.3 自带的 modernc.org/sqlite v1.27 没有 loong64 生成代码，必须升级
go get modernc.org/sqlite@v1.61.0

CGO_ENABLED=0 GOOS=linux GOARCH=loong64 go build -trimpath \
  -ldflags "-s -w -X main.version=v0.10.3 \
    -X main.commit=$(git rev-parse HEAD) \
    -X main.buildTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -o homebox ./app/api
```

不做 `go get modernc.org/sqlite@v1.61.0` 会在 `modernc.org/sqlite/lib` 报大量
`undefined: sqlite3_index_constraint` / `Xsqlite3_threadsafe` 错误，原因是旧版
没有 loong64 的生成文件。

### 3. 镜像

```bash
docker build -t homebox:loong64 .
docker tag homebox:loong64 yunixintel/homebox:loong64
docker tag homebox:loong64 yunixintel/homebox:24.10-la5
docker push yunixintel/homebox:loong64
docker push yunixintel/homebox:24.10-la5
```

运行镜像基于 openEuler，二进制在 `/app/homebox`，前端已 embed，无需额外静态目录。

## 运行

```bash
docker run -d --name homebox -p 7745:7745 \
  -v homebox-data:/data yunixintel/homebox:loong64
```

- Web UI：`http://<host>:7745/`，首次打开注册管理员。
- 数据目录 `/data`：`homebox.db`、WAL/SHM；挂宿主目录需 `chown -R 1000:1000`。
- 默认环境：
  - `HBOX_MODE=production`
  - `HBOX_STORAGE_DATA=/data`
  - `HBOX_STORAGE_SQLITE_URL=/data/homebox.db?_pragma=busy_timeout=2000&_pragma=journal_mode=WAL&_fk=1`
- 健康检查：`/api/v1/status`。

## 注意

- v0.10.3 是上游当前最新 release（2024-01），项目更新较慢；新功能/安全修复需关注上游。
- 默认允许注册（`allowRegistration=true`）；公网部署应在首次注册后关闭注册或加反代认证。
- 镜像不含 TLS，公网必须放在 Caddy/Nginx 反向代理后。
- 备份时同时保留 `homebox.db-wal`/`homebox.db-shm`，或先停容器再拷贝。
- SQLite 单实例，不适合多副本同时写同一 `/data`。

## 验证命令

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:7745/
curl -fsS http://127.0.0.1:7745/api/v1/status
docker exec homebox /app/homebox --help 2>/dev/null || true
docker exec homebox ls -la /data
```
