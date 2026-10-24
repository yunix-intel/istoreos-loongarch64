# Readeck (loong64) 构建记录

## 结论

- 镜像：`yunixintel/readeck:loong64` / `:24.10-la5`
- 大小：约 118MB（Hub 压缩；本地 338MB）
- digest：`sha256:14c9426bafc308717554444a6754405b4e6af1c450b2d49d74f95ff75e514719`
- 版本：Readeck `0.9.2`（commit `ef6f135`）
- 验证：
  - `/` 303→欢迎/引导页 200
  - 首启生成 `/data/config.toml`、`/data/data/db.sqlite3`
  - Docker health `healthy`；进程 UID 1117

## 构建链路

1. 前端：x86_64 WSL2，Node 22 + npm：
   ```bash
   cd web
   npm ci
   npm run build        # gulp → ../assets/www
   ```
   产物 `assets/www` 复制回源码树。
2. 后端：Go 1.27.2，**CGO_ENABLED=1**（mattn/go-sqlite3），在 openEuler 容器内编：
   ```bash
   CGO_ENABLED=1 CGO_CFLAGS=-D_LARGEFILE64_SOURCE go build \
     -tags "netgo osusergo sqlite_omit_load_extension sqlite_foreign_keys sqlite_json1 sqlite_fts5 sqlite_secure_delete" \
     -ldflags "-s -w -X codeberg.org/readeck/readeck/configs.version=0.9.2" \
     -trimpath -o readeck .
   ```
3. 运行阶段 openEuler + `ca-certificates tzdata curl bash shadow util-linux libgcc`；
   非 root 用户 `readeck` UID/GID 1117。
4. 工作目录 `/data`；配置 `/data/config.toml`，数据目录相对配置为 `data/`。

## 运行时契约

- 端口 8000；卷 `/data`（配置、SQLite、书签资源）。
- 环境：`READECK_SERVER_HOST=0.0.0.0`、`READECK_SERVER_PORT=8000`、`TZ`。
- 首次打开进入欢迎/引导页创建管理员；`config.toml` 与 `data/` 自动生成。
- 可选环境变量见上游：`READECK_LOG_LEVEL`、`READECK_ALLOWED_HOSTS`、
  `READECK_DATABASE_SOURCE`（可切 PostgreSQL）等。

## 遇到的问题

- **CGO-free 路径不可用**：`CGO_ENABLED=0` 走 `modernc.org/sqlite v1.25.0`，
  该版本没有 loongarch64 生成文件（`undefined: sqlite3_index_orderby` 等）；
  必须使用 `CGO_ENABLED=1` 的 mattn 驱动。
- **前端构建链**：gulp 4 + Node 22 正常；产物目录是仓库根部 `assets/www`，不是 `web/dist`。
- **数据位置**：`data_directory` 是相对配置文件的 `data`，所以整体放在 `/data` 下最稳。

## 限制

- 未做完整书签抓取/归档联调（需要外网页面与内容提取器）。
- 未启用 PostgreSQL；默认 SQLite。
- 与 Wallabag/Shiori 功能重叠。

## 运行

```bash
docker run -d --name readeck -p 8000:8000 \
  -v /srv/readeck:/data \
  yunixintel/readeck:loong64
```

首次打开 `http://<host>:8000/` 创建管理员；之后在设置中配置导入/抓取选项。
