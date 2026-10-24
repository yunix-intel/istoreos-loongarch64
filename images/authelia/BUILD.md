# Authelia v4.39.28 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/authelia:loong64` / `:24.10-la5`
- 大小：约 139MB（Hub 压缩）
- digest：`sha256:e05a03ac6060c114ca58ff2396e169f6e12e0d5aafb77a5f6c49d55cbb24d83a`
- 版本：Authelia v4.39.28
- 验证：
  - `/api/health` 200、门户 `/` 200、健康检查 healthy
  - SQLite 存储迁移 0→29 完成
  - 自动生成配置、用户库、session/storage 密钥
  - 未做完整登录/TOTP/forward-auth 联调

## 构建链路

1. 源码 `authelia/authelia` v4.39.28。
2. 前端：React/Vite，Node 24 + pnpm 12，在 x86 构建；
   输出到 `internal/server/public_html`。还要把仓库 `api/` 复制到
   `public_html/api/`，否则启动报 `api/index.html` 不存在。
3. 后端：Go 1.27.2，**CGO_ENABLED=1**（`mattn/go-sqlite3`），
   在 openEuler 容器内用 `gcc sqlite-devel` 编。
4. 运行阶段 openEuler + `curl gettext libstdc++ libgcc sqlite-libs`。
5. 运行用户 `authelia` UID/GID 1107；配置 `/config`。

## 自动配置

entrypoint 首次启动：

- 生成 `/config/session.secret`、`/config/storage.key`（0600）；
- 用 `authelia crypto hash generate argon2` 生成管理员密码哈希，
  写入 `/config/users_database.yml`；
- 用模板 + `envsubst` 生成 `/config/configuration.yml`；
- `authelia validate-config` 预检后启动。

环境变量：

- `AUTH_DOMAIN`（默认 `example.com`）
- `AUTH_URL`（默认 `https://auth.example.com`）
- `AUTH_DEFAULT_REDIRECT_URL`（默认 `https://app.example.com`）
- `ADMIN_USER` / `ADMIN_PASSWORD` / `ADMIN_EMAIL`

## 遇到的问题

- **CGO SQLite**：`CGO_ENABLED=0` 报 `undefined: sqlite3.Error`；必须 CGO + sqlite-devel。
- **前端 assets 不完整**：只复制 Vite `public_html` 会缺 `api/index.html`；
  必须把仓库 `api/` 目录一并复制。
- **cookie domain 校验**：`localhost` 不是合法 cookie domain；用带点的域名或 IP。
  `authelia_url`/`default_redirection_url` 必须是 HTTPS 且不能相同。
- **storage 加密键**：`storage.encryption_key` 是顶层键，不是 `storage.local` 下；
  还需要 `identity_validation.reset_password.jwt_secret`。
- **`AUTHELIA_*` 环境变量会被配置解析器当成配置键**：管理变量改用 `ADMIN_*`/`AUTH_*`。

## 运行

```bash
docker run -d --name authelia -p 9091:9091 \
  -e AUTH_DOMAIN=example.com \
  -e AUTH_URL=https://auth.example.com \
  -e AUTH_DEFAULT_REDIRECT_URL=https://app.example.com \
  -e ADMIN_USER=admin -e ADMIN_PASSWORD='change-me' \
  -v authelia-config:/config \
  yunixintel/authelia:loong64
```

- 门户：`http://<host>:9091/`；健康 `/api/health`。
- 首次启动自动生成配置/用户/密钥；修改密码需删除 `users_database.yml` 或手工改哈希。
- `/config` 必须持久化；`configuration.yml` 一旦生成不会被覆盖。
- 默认 `access_control` 为 `one_factor`，所有请求需登录；forward-auth 需在反代配置。
- 无 TLS 终止，公网必须放在 HTTPS 反代之后。
