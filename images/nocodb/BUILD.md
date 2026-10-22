# NocoDB 0.301.3 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/nocodb:loong64` / `:24.10-la5`
- 大小：1.58GB，`linux/loong64`
- digest：`sha256:19218f4aea9758f437d562f093a49f49788268d1ccad7efdc5c88cc8e6166bc7`
- 版本：NocoDB 0.301.3 / Node.js 24.22.1
- 验证：`/api/v1/health` 200、`/` 302→`/dashboard/` 200、SQLite `/data/noco.db`
  初始化、健康检查 healthy。

## 构建

```bash
docker build -t nocodb:loong64 .
docker tag nocodb:loong64 yunixintel/nocodb:loong64
docker tag nocodb:loong64 yunixintel/nocodb:24.10-la5
docker push yunixintel/nocodb:loong64
docker push yunixintel/nocodb:24.10-la5
```

多阶段构建：

- `build` 阶段 `FROM node:24.22.1-loong64`，安装 `gcc-c++ make python3`。
- `npm install -g --ignore-scripts nocodb@0.301.3`。
- 进入 `node_modules/sqlite3` 执行 `npx node-gyp rebuild`。
- 运行阶段复制 `/opt/node24/{bin,lib}` 和 NocoDB 包。

## 两个关键坑

1. **npm 包的 preinstall 强制 pnpm**

   NocoDB 的 package.json 有 `preinstall: npx only-allow pnpm`，用 npm 全局安装会报
   `npm error command sh -c npx only-allow pnpm`。本镜像用 `--ignore-scripts` 跳过它，
   再手动编译 sqlite3。

2. **npm 包不包含 `docker/main`**

   npm tarball 只有 `dist/bundle.js`，没有官方镜像里的 `docker/main.js`。但 bundle
   导出了 `Noco`，因此本仓库提供等价 runner
   [docker-main.js](docker-main.js)（与原 `dockerEntry.ts` 相同：express + cors +
   `Noco.init`）。

3. **NC_DB 的 SQLite 写法**

   SQLite 文件名必须放在查询参数里：

   ```text
   NC_DB=sqlite3://?d=/data/noco.db
   ```

   `sqlite3:///data/noco.db` 会报 `Meta database configuration missing SQLite file name`。

## 运行

```bash
docker run -d --name nocodb -p 8080:8080 \
  -v nocodb-data:/data yunixintel/nocodb:loong64
```

- Web UI：`http://<host>:8080/`（自动跳转 `/dashboard/`）。
- 健康检查：`/api/v1/health`。
- 数据目录 `/data`：默认 `noco.db`；挂宿主目录需 `chown -R 1000:1000`。
- 默认环境：
  - `NC_DB=sqlite3://?d=/data/noco.db`
  - `NC_TOOL_DIR=/data`
  - `PORT=8080`
  - `NODE_ENV=production`
  - `NC_DISABLE_TELE=true`

## 注意

- 镜像较大（1.58GB），主要是 NocoDB 163 个 npm 依赖和前端静态资源。
- 默认 SQLite 适合单实例；多实例/高并发应改用 `NC_DB` 指向 PostgreSQL/MySQL。
- 镜像无 TLS，公网必须放在 Caddy/Nginx 反向代理后。
- 首次打开创建管理员；不要让未认证的 8080 直接暴露公网。
- 升级前备份整个 `/data`；NocoDB 大版本会做元数据库迁移。

## 验证命令

```bash
curl -fsS http://127.0.0.1:8080/api/v1/health
curl -fsS -L -o /dev/null -w '%{http_code} %{url_effective}\n' http://127.0.0.1:8080/
docker exec nocodb ls -la /data
docker exec nocodb node -v
docker restart nocodb
```
