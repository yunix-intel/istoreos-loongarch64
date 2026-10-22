# Penpot frontend 2.18.3 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/penpot-frontend:loong64` / `:24.10-la5`
- Hub 压缩大小：约 274MB
- digest：`sha256:71153a40e65855d7dab6ead7704b2f539467824692779e88bd6ca4575c9eea96`
- 版本：Penpot 2.18.3 静态前端
- 验证：`/` 200、标题 `Penpot | Full-stack design`、`/js/main.js` 200、
  `/api/rpc/command/get-profile` 经代理返回 200、健康检查 healthy

## 构建链路

前端是编译后的静态站点（约 243MB），与 CPU 架构无关，直接复用官方镜像产物：

1. `crane export --platform linux/amd64 penpotapp/frontend:latest`，
   取 `/var/www/app`。
2. 运行阶段基于 `openeuler/openeuler:24.03`，安装 `nginx gettext`。
3. 自写 nginx 模板，保留官方关键行为：
   - `root /var/www/app`，SPA fallback 到 `index.html`；
   - `/api`、`/assets`、`/readyz`、`/ws/notifications` 代理到
     `PENPOT_BACKEND_URI`；
   - `/api/export` 代理到 `PENPOT_EXPORTER_URI`；
   - `/js/config.js` 禁止缓存，静态资源缓存 7 天；
   - 请求体上限 350MiB；
   - 使用 Docker 内置 DNS `127.0.0.11` + 变量 `proxy_pass`，
     后端晚于前端启动也不会导致 nginx 启动失败。
4. entrypoint 每次启动重写 `js/config.js` 中的
   `penpotFlags` / `penpotPublicURI`，再用 `envsubst` 生成 nginx 配置。

## 遇到的问题

- **官方 nginx 镜像的 `nginx.conf` 是模板**：直接复制会在启动时缺少
  `PENPOT_BACKEND_URI` 等变量。必须保留 `envsubst` 步骤。
- **`config.js` 重启后会重复追加 `penpotPublicURI`**：entrypoint 先删除旧行
  再写入，保证幂等。
- **admin-console / MCP 的 location 模板**：未移植对应服务，模板中不包含这些
  路由；因此 `PENPOT_FLAGS` 不要启用 `enable-admin-console` / `enable-mcp`。
- **nginx 启动时后端容器可能还没起来**：用变量 `proxy_pass` + resolver，
  避免 `host not found in upstream` 直接退出。
- **导出功能依赖 exporter**：本仓库暂无 loong64 Chromium exporter，
  `/api/export` 会 502；绘图、协作、评论不受影响。

## 运行

见 [../penpot-backend/BUILD.md](../penpot-backend/BUILD.md) 的完整 compose 命令。
前端单独启动：

```bash
docker run -d --name penpot-frontend -p 9001:8080 \
  --network penpot \
  -e PENPOT_PUBLIC_URI=http://<host>:9001 \
  -e PENPOT_BACKEND_URI=http://penpot-backend:6060 \
  -e PENPOT_FLAGS="disable-email-verification disable-secure-session-cookies" \
  yunixintel/penpot-frontend:loong64
```

- `PENPOT_PUBLIC_URI` 必须与浏览器地址一致。
- 反向代理需支持 WebSocket（`/ws/notifications`）。
- 如需 HTTPS，建议在 frontend 前再加一层 Caddy/NPM，并把
  `PENPOT_PUBLIC_URI` 改为 `https://...`。
