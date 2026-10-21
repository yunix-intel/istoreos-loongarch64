# Actual Budget 26.10.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/actual-budget:loong64` / `:24.10-la5`
- 大小：554MB，`linux/loong64`
- digest：`sha256:47dfba5704aea671977921a74df518f3ebb19568b219798cb06e155d0fccbc0b`
- 版本：Actual Budget 26.10.0（`@actual-app/sync-server`）/ Node.js 24.22.1
- 验证：数据库迁移完成、`/` 200、标题 Actual、`actual-server --version` v26.10.0、
  `/data` 生成 migrate/server-files/user-files、健康检查 healthy。

## 构建

```bash
docker build -t actual-budget:loong64 .
docker tag actual-budget:loong64 yunixintel/actual-budget:loong64
docker tag actual-budget:loong64 yunixintel/actual-budget:24.10-la5
docker push yunixintel/actual-budget:loong64
docker push yunixintel/actual-budget:24.10-la5
```

多阶段构建：

- `build` 阶段 `FROM node:24.22.1-loong64`，安装 `gcc-c++ make python3` 后执行
  `npm install -g --unsafe-perm @actual-app/sync-server@26.10.0`。
- 运行阶段复制 `/opt/node24/{bin,lib}` 和
  `/opt/node24/lib/node_modules/@actual-app/sync-server`。
- 运行阶段重建 CLI 符号链接：
  `ln -s ../lib/node_modules/@actual-app/sync-server/build/bin/actual-server.js /opt/node24/bin/actual-server`。

## 原生依赖

Actual 的依赖里有三个原生模块：

| 模块 | 情况 |
|---|---|
| `argon2` | 有 install script，构建阶段自行编译出 `argon2.node` |
| `bcrypt` | 有 install script，构建阶段自行编译出 `bcrypt_lib.node` |
| `better-sqlite3` | **没有 install script**，npm 包只带 x64/arm 预编译；loong64 必须手动编译 |

因此 Dockerfile 在 npm install 后额外执行：

```bash
cd /opt/node24/lib/node_modules/@actual-app/sync-server/node_modules/better-sqlite3
npx node-gyp rebuild
```

不做这一步，启动会报
`Cannot find module .../better-sqlite3/build/Release/better_sqlite3.node`。

## 运行

```bash
docker run -d --name actual-budget -p 5006:5006 \
  -v actual-data:/data \
  yunixintel/actual-budget:loong64
```

- Web UI：`http://<host>:5006/`，首次打开创建服务器密码/账号。
- 数据目录 `/data`：SQLite、`server-files`、`user-files`、迁移记录都在这里。
- 容器以 UID/GID 1002（`actual`）运行；挂宿主目录需
  `chown -R 1002:1002 <dir>`。
- 环境变量：
  - `ACTUAL_DATA_DIR` 默认 `/data`
  - `ACTUAL_PORT` 默认 `5006`
  - 其他可用变量（HTTPS、OpenID、上传限制等）见镜像内 `ACTUAL_*` 支持列表。

## 注意

- 镜像只提供 HTTP，公网使用必须放在 Caddy/Nginx 反向代理后并启用 TLS。
- 反向代理场景需正确设置 `ACTUAL_TRUSTED_PROXIES`/`ACTUAL_HOSTNAME`，否则登录和
  cookie 可能异常。
- 升级前备份整个 `/data`；数据库迁移是单向的，降级大版本可能无法打开。
- 该服务是单实例 SQLite 架构，不适合多副本同时写同一数据目录。
- 首次启动会自动跑迁移；看到 `Migrations: DONE` 和 `Listening on :::5006` 即启动完成。

## 验证命令

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5006/
curl -fsS http://127.0.0.1:5006/ | grep -o '<title>[^<]*'
docker exec actual-budget /opt/node24/bin/actual-server --version
docker exec actual-budget ls -la /data
docker restart actual-budget
```
