# Pocket ID (loong64) 构建记录

## 结论

- 镜像：`yunixintel/pocket-id:loong64` / `:24.10-la5`
- 大小：约 136MB（Hub 压缩；本地 394MB）
- digest：`sha256:7c21de80f53c03a2d0ae5cc3cb4678caf4ada07e4d0dc65d9b5de05d782d0cb4`
- 版本：Pocket ID `v2.9.0`（commit `49cb131`）
- 验证：
  - `/` 200，SvelteKit 前端正常返回
  - `/healthz` 204；Docker health `healthy`
  - 首启生成 `/data/encryption-key` 与 SQLite `pocket-id.db`，进程 UID 1122
  - 未做完整 OIDC 登录/邮件验证联调

## 构建链路

1. 前端：x86_64 WSL2，Node 24.22.1 + pnpm 10.33.0：
   ```bash
   pnpm --filter pocket-id-frontend install --frozen-lockfile
   BUILD_OUTPUT_PATH=dist pnpm --filter pocket-id-frontend run build
   ```
   产物 `frontend/dist` 复制到 `backend/frontend/dist`（`//go:embed all:dist/*`）。
2. 后端：Go 1.27.2，`CGO_ENABLED=0`：
   ```bash
   CGO_ENABLED=0 go build -trimpath \
     -ldflags "-s -w -X github.com/pocket-id/pocket-id/backend/internal/common.Version=2.9.0" \
     -o pocket-id .
   ```
3. 运行阶段 openEuler + `ca-certificates tzdata curl bash shadow util-linux`；
   非 root 用户 `pocketid` UID/GID 1122。

## 运行时契约

- 端口 1411；卷 `/data`（SQLite、上传文件、加密密钥）。
- 环境变量：
  - `APP_URL`：外部访问地址，默认 `http://localhost:1411`；OIDC 场景必须改成正式地址；
  - `ENCRYPTION_KEY`：>=16 字节；未设置时 entrypoint 生成并持久化 `/data/encryption-key`；
  - `DB_CONNECTION_STRING=/data/pocket-id.db`、`UPLOAD_PATH=/data/uploads`；
  - 可选 `PORT`、`TRUST_PROXY`、`ANALYTICS_DISABLED`、`EMAIL_*` 等上游变量。
- 首启通过 Web 向导创建管理员；之后在 UI 配置 OIDC 客户端。

## 遇到的问题

- **健康检查不能直接复用上游命令**：`pocket-id healthcheck` 会先解析完整配置，
  而 `docker exec` 不继承 entrypoint 导出的 `ENCRYPTION_KEY`，直接报
  `ENCRYPTION_KEY must be at least 16 bytes long`；改用 `curl /healthz`（204）。
- **前端不能在本机编**：SvelteKit/Vite 依赖需 x86 Node 构建，产物再 embed 进 Go。
- **默认数据路径是相对 `data/`**：容器工作目录变化会导致数据位置漂移；
  显式设置 `DB_CONNECTION_STRING` 与 `UPLOAD_PATH` 到 `/data`。

## 限制

- 未验证邮件 SMTP、SCIM、Passkey 全链路。
- 与 Authelia 功能重叠，二选一。
- 单实例 SQLite；多副本需 PostgreSQL。

## 运行

```bash
docker run -d --name pocket-id -p 1411:1411 \
  -e APP_URL=http://<host>:1411 \
  -v pocket-id-data:/data \
  yunixintel/pocket-id:loong64
```

首次打开 `http://<host>:1411/` 按向导创建管理员。
