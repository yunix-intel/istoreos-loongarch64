# Woodpecker server (loong64) 构建记录

## 结论

- 镜像：`yunixintel/woodpecker-server:loong64` / `:24.10-la5`
- 大小：约 133MB（Hub 压缩；本地 366MB）
- digest：`sha256:e244179126c6f05532e96cb9ebde87d7977d3d6a71ea773e71f0b50f7c8b3e7f`
- 版本：Woodpecker `v3.19.0`（commit `9f5568c`）
- 验证：
  - `/` 200，内嵌 UI 的 `/assets/index-*.js` 200（462KB）
  - `/api/healthz` 204，Docker health `healthy`
  - SQLite 首次启动自动建库/迁移
  - agent 以 `WOODPECKER_AGENT_SECRET` 注册成功

## 构建链路

1. 前端：x86_64 WSL2，Node 24.22.1 + pnpm 12.9.1
   （`packageManager` 固定 12.9.1，corepack 会自动取该版本）。
   ```bash
   cd web
   pnpm install --frozen-lockfile
   pnpm run build          # vite build --base=/BASE_PATH
   ```
   `index.html` 里的 `BASE_PATH` 是运行时占位符，由 server 启动时替换，不需要手工改。
2. 把 `web/dist` 放入源码树（`web/web.go` 是 `//go:embed all:dist/*`）。
3. 后端：openEuler 24.03 容器内，Go 1.27.2，`CGO_ENABLED=1`（mattn/go-sqlite3）：
   ```bash
   CGO_ENABLED=1 go build -tags grpcnotrace \
     -ldflags "-s -w -X go.woodpecker-ci.org/woodpecker/v3/version.Version=3.19.0" \
     -o dist/woodpecker-server go.woodpecker-ci.org/woodpecker/v3/cmd/server
   ```
4. 运行阶段：openEuler + `ca-certificates tzdata curl bash shadow util-linux procps-ng`；
   非 root 用户 `woodpecker` UID/GID 1114。

## 运行时契约

- 端口：8000（HTTP/UI）、9000（gRPC，agent 用）。
- 卷：`/var/lib/woodpecker`（SQLite、`agent-secret`、`grpc-secret`）。
- **必须配置一个 forge**（Gitea、GitHub、GitLab、Forgejo 等）。未配置时启动直接失败：
  `could not setup service manager: forge not configured`。
  最小 Gitea 示例：
  ```
  WOODPECKER_GITEA=true
  WOODPECKER_GITEA_URL=https://git.example.com
  WOODPECKER_GITEA_CLIENT=...
  WOODPECKER_GITEA_SECRET=...
  ```
- 首次启动若未给 `WOODPECKER_AGENT_SECRET`，entrypoint 会生成
  `/var/lib/woodpecker/agent-secret` 并复用；agent 需使用同一个值。
- 未给 `WOODPECKER_GRPC_SECRET` 时同样生成并持久化到 `/var/lib/woodpecker/grpc-secret`，
  避免每次重启换密钥。
- `WOODPECKER_HOST` 必须是浏览器可访问的完整 URL，否则 OAuth 回调错误。

## 遇到的问题

- **forge 必填**：这是与“单容器即开即用”预期最大的差异；商店描述必须写明需要外部 Gitea/GitHub。
- **SQLite 需要 CGO**：`server/store/datastore/init_cgo.go` 只在 CGO 构建时注册 `sqlite3`；
  纯静态 `CGO_ENABLED=0` 构建无法用默认数据库。
- **`WOODPECKER_IN_CONTAINER=true`**：容器内默认数据库路径是
  `/var/lib/woodpecker/woodpecker.sqlite`；不设会落到当前目录。
- **健康检查**：`/healthz` 返回 204（不是 200），`curl -f` 仍视为成功。

## 运行

```bash
docker network create woodpecker
docker run -d --name woodpecker-server --network woodpecker \
  -p 8000:8000 -p 9000:9000 \
  -e WOODPECKER_HOST=http://<host>:8000 \
  -e WOODPECKER_OPEN=true \
  -e WOODPECKER_ADMIN=admin \
  -e WOODPECKER_GITEA=true \
  -e WOODPECKER_GITEA_URL=https://git.example.com \
  -e WOODPECKER_GITEA_CLIENT=<client> \
  -e WOODPECKER_GITEA_SECRET=<secret> \
  -v woodpecker-data:/var/lib/woodpecker \
  yunixintel/woodpecker-server:loong64
```

agent 启动时把 `WOODPECKER_AGENT_SECRET` 设成 `docker exec woodpecker-server cat /var/lib/woodpecker/agent-secret`
的输出，见 `images/woodpecker-agent/BUILD.md`。
