# Ente server (museum) — loong64 构建记录

## 结论

- 镜像：`yunixintel/ente-server:loong64` / `:24.10-la5`
- 大小：约 123MB（Hub 压缩）
- digest：`sha256:bfac0212dcecc619ef0ac965797d6527c0ae41c7fd78432898b0be2c811d9d7e`
- 版本：ente server master（2026-10 快照，commit 未固定）
- 验证：
  - `/ping` 200、健康检查 healthy
  - PostgreSQL 连接/迁移成功，MinIO 三个 bucket 可写（初始化时创建）
  - 未做客户端注册/上传照片的完整流程
- **Web 端暂未包含**：`ente-web` 需要 10 个 Next 应用 + Rust WASM，构建在后续补充；
  server 可先供移动端/桌面客户端使用。

## 构建链路

1. 源码 `ente-io/ente` 的 `server/`。
2. Go 1.27.2，`CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" ./cmd/museum`。
3. 运行阶段 openEuler + `ca-certificates tzdata curl shadow util-linux`；
   复制 `configurations/`、`migrations/`、`mail-templates/`、`web-templates/`。
4. 运行用户 `ente` UID/GID 1105；`/data` 存 `museum.yaml` 与密钥。
5. entrypoint 首次启动生成 `museum.yaml`（DB/S3/三个随机密钥），
   后续启动复用；`/etc/ente/museum.yaml` 软链到 `/data/museum.yaml`。

## 依赖服务

- PostgreSQL：库 `ente_db`、用户 `pguser`。
- MinIO/S3：三个 bucket `b2-eu-cen`、`wasabi-eu-central-2-v3`、`scw-eu-fr-v3`。
  可用 `mc mb` 创建；S3 endpoint 例如 `minio:9000`。
- Web 端（可选）：官方 10 个 Next 应用，端口 3000–3010。

## 遇到的问题

- **JWT secret 编码**：`jwt.secret` 必须用 `base64.URLEncoding`（URL-safe + padding）；
  用标准 base64 会报 `illegal base64 data`。
- **加密/哈希 key**：`key.encryption`/`key.hash` 用标准 base64（StdEncoding）。
- **museum.yaml 只生成一次**：之后改 DB/S3 环境变量不会生效；需删除 `/data/museum.yaml` 或手工编辑。
- **S3 bucket 必须先建**：Museum 不会自动建桶；缺桶时上传失败。
- **Web 端缺失**：本镜像只含 API；`/` 不是图库 UI。

## 运行

```bash
docker network create ente

docker run -d --name ente-pg --network ente \
  -e POSTGRES_PASSWORD=pgpass -e POSTGRES_USER=pguser -e POSTGRES_DB=ente_db \
  -v ente-pg:/var/lib/postgresql/data yunixintel/postgres:loong64

docker run -d --name ente-minio --network ente \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  -v ente-minio:/data yunixintel/minio:loong64

# 用 mc 建桶（任意带 mc 的容器）
docker run --rm --network ente --entrypoint bash -v /path/to/mc:/mc:ro \
  yunixintel/minio:loong64 -lc \
  "/mc alias set local http://ente-minio:9000 minioadmin minioadmin &&
   /mc mb -p local/b2-eu-cen local/wasabi-eu-central-2-v3 local/scw-eu-fr-v3"

docker run -d --name ente-server --network ente -p 8080:8080 \
  -e ENTE_DB_HOST=ente-pg -e ENTE_DB_NAME=ente_db \
  -e ENTE_DB_USER=pguser -e ENTE_DB_PASSWORD=pgpass \
  -e ENTE_S3_ENDPOINT=ente-minio:9000 \
  -e ENTE_S3_KEY=minioadmin -e ENTE_S3_SECRET=minioadmin \
  -v ente-data:/data yunixintel/ente-server:loong64
```

- API：`http://<host>:8080/ping`。
- `/data` 必须持久化；`museum.yaml` 含 DB/S3 和三个密钥，丢失后旧数据无法解密。
- 修改密码/密钥前先备份数据库和 `/data/museum.yaml`。
- 生产必须加 HTTPS 反代；Web 端/客户端 endpoint 填 `http://<host>:8080`。
- 移动端可直接连 API；Web 图库待 `ente-web` 镜像。
