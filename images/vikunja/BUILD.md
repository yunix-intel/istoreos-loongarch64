# Vikunja v2.7.1 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/vikunja:loong64` / `:24.10-la5`
- 大小：约 169MB（Hub 压缩）
- digest：`sha256:2533351078b4184b0683a64cf4f6ca81c10d83b8cdb5edbcbd371b6fa620a0a3`
- 版本：Vikunja v2.7.1
- 验证：
  - `/` 200、`/health` 200、`/api/v1/info` 返回 `version=v2.7.1`
  - 注册 `POST /api/v1/register` 200，登录 `POST /api/v1/login` 返回 token
  - SQLite 迁移完成，健康检查 healthy
  - 未做 Kanban 拖拽/CalDAV 客户端测试

## 构建链路

1. 前端：Vue + Vite，要求 Node >=24、pnpm 11.27；在 x86 WSL2 用 Node 24.22.1
   构建（`sass-embedded` 无 loong64）：
   `pnpm install --frozen-lockfile && pnpm run build`，产物 `frontend/dist`。
2. 后端：Go 1.27.2，`CGO_ENABLED=1`（`mattn/go-sqlite3`），在 openEuler 24.03
   容器内用 `gcc sqlite-devel` 编：
   `go build -ldflags "-s -w -X code.vikunja.io/api/pkg/version.Version=v2.7.1"`。
3. 运行阶段 openEuler + `curl tzdata shadow util-linux procps-ng`；
   二进制 `/app/vikunja/vikunja`，数据 `/app/vikunja/files`，SQLite `/db/vikunja.db`。
4. 运行用户 `vikunja` UID/GID 1104，端口 3456。

## 遇到的问题

- **前端必须 Node 24**：Node 22 不满足 `engines.node >=24`；`sass-embedded`
  也没有 loong64 binding，所以必须在 x86 构建 dist。
- **`service.publicurl` 必填**：默认 `cors.enable=true`，没有 publicurl 会直接
  `service.publicurl is required when cors.enable is true` 退出。
- **端口配置键不是 `service.port`**：Vikunja 用 `service.interface`，默认 `:3456`。
  只设 `VIKUNJA_SERVICE_PORT` 会被忽略，日志出现 `address 0.0.0.0: missing port`。
- **JWT secret 已弃用**：`service.jwtsecret` 迁移到 `service.secret`；
  entrypoint 生成并持久化到 `/db/jwt.secret`（0600），同时兼容旧环境变量。
- **SQLite 需要 CGO**：必须在 openEuler 容器内编，避免宿主 glibc 2.41 依赖。

## 运行

```bash
docker run -d --name vikunja -p 3456:3456 \
  -e VIKUNJA_SERVICE_PUBLICURL=http://<host>:3456/ \
  -v vikunja-files:/app/vikunja/files \
  -v vikunja-db:/db \
  yunixintel/vikunja:loong64
```

- Web/API：`http://<host>:3456/`；健康检查 `/health`。
- 首次使用在 Web 注册；默认允许注册，生产建议关闭或加邀请。
- `/app/vikunja/files` 存附件；`/db` 存 SQLite 与 JWT secret，必须持久化。
- `VIKUNJA_SERVICE_PUBLICURL` 必须与浏览器地址一致，否则邮件/链接错误。
- 默认无 TLS；公网放在反代之后。
