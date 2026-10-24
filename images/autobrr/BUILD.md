# Autobrr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/autobrr:loong64` / `:24.10-la5`
- 大小：约 131MB（Hub 压缩）
- digest：`sha256:32f91a3164658ed60130973e87d5f3927168cfabf8e281436fe2d6250ee2dcf7`
- 版本：autobrr master（commit `dc49add`，2026-10-23）
- 验证：
  - Web UI `/` 200、`/api/healthz/liveness` 200、健康检查 healthy
  - SQLite base schema 迁移完成
  - 未配置 IRC 网络/filter/qBittorrent 的真实联调

## 构建链路

1. 前端：Vue/Vite，在 x86 WSL2 用 Node 24 + pnpm 11 构建 `web/dist`。
2. 后端：Go 1.27.2，`CGO_ENABLED=0`，`//go:embed all:dist` 把 UI 编进二进制。
3. 运行阶段 openEuler + `ca-certificates tzdata curl jq shadow util-linux`。
4. 运行用户 `autobrr` UID/GID 1113；配置/数据 `/config`；端口 7474。

## 遇到的问题

- **Go toolchain**：`go.mod` 写 `toolchain go1.27.3`，本机用 1.27.2 +
  `GOTOOLCHAIN=local` 可编（实际语言版本 1.27.0）。
- **前端内嵌**：必须先把 `web/dist` 放进源码树再 `go build`，否则 UI 404。
- **HOME 路径**：Autobrr 默认把配置写到 `$HOME`；镜像设 `HOME=/config`、
  `XDG_CONFIG_HOME=/config`、`XDG_DATA_HOME=/config`，并持久化 `/config`。
- **健康端点**：不是 `/health`，是 `/api/healthz/liveness`（readiness 另一个）。

## 运行

```bash
docker run -d --name autobrr -p 7474:7474 \
  -v autobrr-config:/config \
  yunixintel/autobrr:loong64
```

- Web UI：`http://<host>:7474/`；健康 `/api/healthz/liveness`。
- `/config` 存 `config.toml` 与 SQLite，必须持久化。
- 首次打开在 UI 里配置 IRC 网络、filter、下载器（qBittorrent 等）。
- 默认无认证/无 TLS；公网必须加反代认证。
- 真实 IRC/下载器联调需要用户自己的凭据，镜像不内置。
