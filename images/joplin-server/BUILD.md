# Joplin Server 3.7.21 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/joplin-server:loong64`、`:24.10-la5`、`:3.7.21`
- digest（`loong64` / `24.10-la5` 相同）：`sha256:59177faf22ef40fc7579a609cb855911ad09a375b4ab14d3dbe1d1b77adb4bff`
- 大小：859MB（未压缩，`docker inspect .Size=859361110`）；registry 压缩后约 273.4MiB
- 架构：`linux/loong64`（`crane config` 返回 `"architecture":"loong64"`）
- 上游：`laurent22/joplin` tag `v3.7.21`，commit `e41516e669efb693b009bedb21f3eb1fcbea4fc9`
- 版本：`@joplin/server` 3.7.1（启动日志 `Starting server v3.7.1 (prod)`）/ Node.js 24.22.1 /
  sqlite3 5.1.6（bundled SQLite 3.41.1）/ PostgreSQL 15.18
- 验证：51 个迁移自动执行、`/api/ping` 200、admin 登录与改密、普通用户创建/登录、
  含图片附件笔记的上传/分享页/附件字节、重启持久化、`/data/temp/joplin.sqlite`、
  `/data/logs` 可写、Docker healthcheck `healthy`。

## 上游与构建范围

按上游 `Dockerfile.server` 的 COPY 清单，只取 server 所需 workspace：

```text
package.json .yarnrc.yml yarn.lock gulpfile.js tsconfig.json
.yarn/releases .yarn/patches
packages/{turndown,turndown-plugin-gfm,fork-htmlparser2,fork-sax,fork-uslug,
          htmlpack,renderer,tools,utils,lib,server}
```

不含 desktop/mobile/cli。Web UI 是 Mustache + 静态 CSS/JS，没有 SPA 打包器，
因此可以全程在 loong64 上构建，不需要 x86 前端阶段。

## 构建

### 1. 准备上下文（稀疏克隆）

```bash
mkdir -p /opt/joplin-build/src && cd /opt/joplin-build/src
git init -q
git remote add origin https://github.com/laurent22/joplin.git
git fetch -q --depth 1 --filter=blob:none origin refs/tags/v3.7.21
git checkout -q FETCH_HEAD
git sparse-checkout init --cone
git sparse-checkout set .yarn/releases .yarn/patches \
  packages/turndown packages/turndown-plugin-gfm packages/fork-htmlparser2 \
  packages/fork-sax packages/fork-uslug packages/htmlpack packages/renderer \
  packages/tools packages/utils packages/lib packages/server
git rev-parse HEAD   # e41516e669efb693b009bedb21f3eb1fcbea4fc9
```

把上表文件和 `Dockerfile`、`docker-entrypoint.sh`、`patch-package-json.js` 放进构建上下文。

### 2. 标准构建（Dockerfile）

磁盘充足（`/var/lib/docker` 至少 10GB 可用）时直接用多阶段 Dockerfile：

```bash
docker build -t joplin-server:loong64 .
```

构建阶段依次执行：

1. `dnf install gcc-c++ make python3 findutils`
2. `node patch-package-json.js`：删除 `onenote-converter`、清空各 workspace 的
   `postinstall`、把 `@joplin/turndown` 的 rollup 指向 `@rollup/wasm-node@4.2.0`
3. `YARN_ENABLE_SCRIPTS=false node .yarn/releases/yarn-4.16.0.cjs install --inline-builds`
4. 对 `packages/{lib,server,tools}/node_modules/sqlite3` 逐个源码编译
5. `BUILD_SEQUENCIAL=1 yarn run buildSequential`
6. `yarn workspaces focus --production @joplin/server`（**不是** `--all`）
7. 在 `packages/server` 下 `require('sqlite3')` 做门禁

### 3. 本次实际构建（磁盘受限路径）

本机 `/var`（Docker 数据盘）只剩约 6.5GB，首次 `docker build` 在 yarn link 阶段
写满 `/var` 被终止；`/opt` 与 `/var` 同分区，只有 `/` 有约 13GB。因此把相同的构建
步骤放进一个常驻 loong64 构建容器，产物写到 `/` 上的 bind mount，最后只用
`Dockerfile.runtime` 组装运行镜像。**没有使用 x86 阶段，构建工具链仍是
`yunixintel/node:24.22.1`（loong64）。**

```bash
mkdir -p /joplin-build/work
docker run -d --name joplin-build --network host \
  -v /joplin-build/work:/build -w /build yunixintel/node:24.22.1 sleep infinity

docker exec joplin-build bash -lc '
  dnf install -y --disablerepo=debuginfo --disablerepo=EPOL \
    --setopt=install_weak_deps=False gcc-c++ make python3 findutils
  cd /build
  node patch-package-json.js
  YARN_ENABLE_SCRIPTS=false node .yarn/releases/yarn-4.16.0.cjs install --inline-builds
'

# sqlite3：三个 workspace 副本都要编（nmHoistingLimits: workspaces）
docker exec joplin-build bash -lc '
  NPRE=$(find /build -path "*/node_modules/.bin/node-pre-gyp" | head -1)
  for d in $(find /build/packages -maxdepth 4 -type d -path "*/node_modules/sqlite3"); do
    (cd "$d" && npm_config_nodedir=/opt/node24 JOBS=max "$NPRE" rebuild --build-from-source)
  done
'

docker exec joplin-build bash -lc '
  cd /build
  BUILD_SEQUENCIAL=1 node .yarn/releases/yarn-4.16.0.cjs run buildSequential
  YARN_ENABLE_SCRIPTS=false node .yarn/releases/yarn-4.16.0.cjs \
    workspaces focus --production @joplin/server
  cd packages/server && node -e "require(\"sqlite3\")"
'

# 把生产树复制成最小上下文，组装运行镜像
mkdir -p /joplin-build/runtime
cp -a /joplin-build/work/packages /joplin-build/runtime/packages
cp /joplin-build/work/docker-entrypoint.sh /joplin-build/runtime/
docker build -f Dockerfile.runtime -t joplin-server:loong64 /joplin-build/runtime
```

`Dockerfile.runtime` 只做运行阶段：openEuler 24.03 + `/opt/node24` + 已裁剪的
`packages/` + UID/GID 1119 + `/data` 四目录 + 健康检查。它与 `Dockerfile` 的
runtime stage 一致。

## Rollup 坑（turndown 构建）

`@joplin/turndown` 使用 rollup **4.2.0**，该版本没有 loong64 原生 binding：

- `@rollup/rollup-linux-loong64-gnu` 在 npmjs 从 **4.50.2** 起才有，在
  `registry.loongnix.cn:5873` 从 **4.21.3** 起才有；
- rollup 的 `native.js` 要求 binding 与 rollup 版本**完全一致**，4.21.3 的 binding
  不能配 4.2.0。

因此按可行性报告 §2 的降级路径，使用官方同版本 wasm 实现，并且只作用于 turndown：

```json
"resolutions": {
  "@joplin/turndown/rollup": "npm:@rollup/wasm-node@4.2.0"
}
```

`turndown-plugin-gfm` 自己的 rollup 0.50.1 不受影响。验证输出：

```text
src/turndown.js → lib/turndown.cjs.js ... created
src/turndown.js → lib/turndown.browser.cjs.js ... created
src/gfm.js → lib/turndown-plugin-gfm.cjs.js ... created
```

wasm 只用于构建期；运行镜像里没有 rollup 依赖。

## sqlite3 5.1.6 编译

```bash
cd packages/<workspace>/node_modules/sqlite3
npm_config_nodedir=/opt/node24 JOBS=max <node-pre-gyp> rebuild --build-from-source
```

- 产物：`lib/binding/napi-v6-linux-glibc-loong64/node_sqlite3.node`（2,374,056 字节），
  另生成 `napi-v3-linux-glibc-loong64`。
- `readelf -h`：`ELF64` / `Machine: LoongArch`；运行时读取 ELF `e_machine=0x102`。
- 加载门禁（server 与 lib 两个解析路径）：

```text
sqlite3 ok { v: '3.41.1' }
```

- `nmHoistingLimits: workspaces` 使 lib/server/tools 各有一份 sqlite3；只编一份会在
  server 启动时报 `Cannot find module .../napi-v6-linux-glibc-loong64/node_sqlite3.node`。
- 宿主机 `getconf PAGESIZE=16384`；`/data/temp/joplin.sqlite` 在 16K 页上正常创建并
  用于分享页渲染。

## 生产依赖裁剪

`focus --production @joplin/server` 后，运行树 497MB，以下模块均确认 **ABSENT**：

```text
sharp  sqlite-vec  onnxruntime-node  pm2  better-sqlite3
```

`@joplin/tools`（sharp 的 production 依赖）随 devDependencies 被裁掉。

## 运行

```bash
docker run -d --name joplin \
  -p 22300:22300 \
  -v joplin-data:/data \
  -e APP_BASE_URL=https://notes.example.com \
  -e DB_CLIENT=pg \
  -e POSTGRES_HOST=db -e POSTGRES_PORT=5432 \
  -e POSTGRES_DATABASE=joplin -e POSTGRES_USER=joplin -e POSTGRES_PASSWORD=change-me \
  -e DEFAULT_ADMIN_PASSWORD='change-me-too' \
  yunixintel/joplin-server:loong64
```

| 变量 | 说明 |
|---|---|
| `APP_BASE_URL` | 外部可访问 URL；分享链接和 cookie 依赖它 |
| `APP_PORT` | 默认 22300 |
| `DB_CLIENT` | `pg`（推荐）或 `sqlite3` |
| `POSTGRES_*` | 库/用户需预先存在；容器内不要写 `localhost`，会被改成 `host.docker.internal` |
| `DEFAULT_ADMIN_PASSWORD` | 首次启动前设置；管理员固定 `admin@localhost`（`APP_ADMIN_EMAIL` 不读取） |
| `MAX_TIME_DRIFT` | 无外网 NTP 时设 `0`；本次 NTP 可用（offset -87ms），未设置 |
| `COOKIES_SECURE` | 反向代理 TLS 时设 `true` |
| `STORAGE_DRIVER` | 可选 `Type=Filesystem; Path=/data/storage`；默认数据库存储 |

- 容器内 UID/GID 1119；entrypoint 在每次启动时用 `install -d -o 1119 -g 1119`
  重建 `/data/{logs,temp,resource,storage}`，再 `chown 1119:1119 /data` 顶层，不递归。
  bind mount 会遮住镜像内的子目录，因此这一步是必需的；无需宿主预先 `chown -R`。
- healthcheck 使用 `APP_BASE_URL` 的 host:port 作为 `Host` 头访问 `127.0.0.1:22300/api/ping`。
  Joplin 会拒绝 origin 不匹配的请求；固定用 `127.0.0.1` 作 Host 会一直 404。
- 日志走 stdout（未装 PM2）；用 Docker `--log-opt max-size` 或宿主 logrotate。
- `server/logs`、`server/temp`、`server/resource` 是指向 `/data/*` 的符号链接。
- 主库在 PostgreSQL，但服务端仍会创建 `/data/temp/joplin.sqlite` 临时库，这是
  Joplin 模型序列化/分享页渲染所需，不是配置错误。

## 测试证据（2026-10-25，Host A）

测试栈：`yunixintel/postgres:loong64`（PG 15.18）+ `joplin-server:loong64`，
`APP_BASE_URL=http://127.0.0.1:22300`，`DB_CLIENT=pg`，命名卷 `joplin-data`。

### 迁移与启动

```text
App: Starting server v3.7.1 (prod) on port 22300 and PID 15...
App: Connection check: { latestMigration: null, isCreated: false, error: null }
App: Auto-migrating database...
App: Latest migration: { name: '20260821120000_token_purpose.js', done: true }
```

- `packages/server/src/migrations` 共 51 个 `.ts` 迁移，PG `knex_migrations` 行数 **51**。
  （任务描述里的“99”不是该 tag 的实际迁移数；v3.7.21 是 51。）
- `GET /api/ping` → `200 {"status":"ok","message":"Joplin Server is running"}`
- `docker inspect` healthcheck → `healthy`（start-period 90s）

### 登录/改密/普通用户

| 操作 | API/UI 路径 | 结果 |
|---|---|---|
| admin 登录 | `POST /api/sessions` `{email:"admin@localhost",password:<DEFAULT_ADMIN_PASSWORD>}` | 200，返回 session id |
| 用户列表 | `GET /api/users`（`X-Api-Auth: <session>`） | 200 |
| 改 admin 密码 | `PATCH /api/users/:id` `{"password":"..."}` | 200 |
| 旧密码 | `POST /api/sessions` | 403（拒绝） |
| 新密码 | `POST /api/sessions` | 200 |
| 建普通用户 | `POST /api/users` `{email,full_name}` | 200，返回用户 id |
| 设普通用户密码 | `PATCH /api/users/:id` `{password,must_set_password:0,email_confirmed:1}` | 200 |
| 普通用户登录 | `POST /api/sessions` | 200 |
| Web 登录页 | `GET /login` | 200 |
| Web 登录（admin） | `POST /login`（form `email`/`password`） | 302 → `/admin/dashboard` |
| Web 登录（普通用户） | `POST /login` | 302 → `/home` |
| 错误密码 | `POST /login` | 403，页面含 `Invalid email or password` |
| 管理页 | `GET /admin/dashboard`（cookie） | 200 |

### 笔记/图片附件/分享页

以普通用户身份通过 API 上传（`PUT /api/items/.../content`，multipart `file`）：

- 笔记：`root:/a1b2c3d4e5f60718293a4b5c6d7e8f90.md:`，正文引用
  `![my image](:/b1c2d3e4f5061728394a5b6c7d8e9f01)`
- 资源元数据：`root:/b1c2d3e4f5061728394a5b6c7d8e9f01.md:`（`type_: 4`，image/png，size 70）
- 资源 blob：`root:/.resource/b1c2d3e4f5061728394a5b6c7d8e9f01:`
- 分享：`POST /api/shares` `{type:1, note_id:"..."}` → share id

结果：

- `GET /api/items/root:/<note>.md:/content` 200，内容含笔记标题；
- `GET /api/items/root/delta?limit=100` 200，返回 3 个 item（同步路径可用）；
- `GET /shares/<shareId>` 200，30,156 字节，含笔记标题、`data-resource-id` 和
  `<img ... resource_id=...>`；
- `GET /shares/<shareId>?resource_id=<id>&t=1` 200，70 字节，与上传 PNG **逐字节相同**；
- PG 行：users=2、items=3、shares=1；items 为 `.resource/<id>`、`<note>.md`、`<resource>.md`。

### 重启与数据目录

`docker restart joplin-test` 后：

- `/api/ping` 200，`Starting server v3.7.1` + `Latest migration ... done: true` 再次出现；
- 普通用户登录 200；
- 分享页 200 且仍含标题；附件仍是 70 字节；
- `/data/temp/joplin.sqlite` 存在（442,368 字节，owner `joplin:joplin`）；
- `/data/logs` 可写（容器内 `touch` 成功）；
- `/data`、`/data/logs`、`/data/temp` 权限 `joplin:joplin 755`。

## sqlite-vec

运行镜像中没有 `sqlite-vec` 模块，服务端不传 `sqliteVec`，
`JoplinDatabase.tryLoadSqliteVec()` 走 `sqliteVecAvailable_=false` 分支，
向量检索禁用。这是**预期行为**，不影响同步、分享或附件。

注意：该分支的日志 `sqlite-vec not provided by the host app; vector search disabled`
在 `v3.7.21` 的 server 里**不会出现在 stdout**，因为
`packages/server/src/utils/joplinUtils.ts:111` 的 `db_.setLogger(...)` 被上游注释掉了；
`packages/lib/JoplinDatabase.ts:173` 使用默认 logger。因此不要用“日志里没有这行”
判断 sqlite-vec 是否加载；以镜像内无该模块、启动正常为准。

## 限制/未验证

- 本机因为 `/var` 只有约 6.5GB，标准 `docker build .` 未在本机完整跑通；构建步骤是在
  loong64 容器内按同样命令执行，运行阶段用 `Dockerfile.runtime` 组装。`Dockerfile`
  是标准可复现入口，建议在 Docker 数据盘 ≥10GB 的机器上验证一次。
- 只测试了 PostgreSQL 15.18 主库；未测试 `DB_CLIENT=sqlite3` 单机模式。
- 未用真实 Joplin 桌面/移动客户端做双端同步；同步验证限于 Server 的 `/api/items`
  上传/读取/delta 和分享页。
- 未验证 LDAP/SAML、Stripe、邮件、Transcribe/HTR（独立服务）。
- 未验证多实例/共享存储；默认单实例。
- 镜像只提供 HTTP，公网必须放在 Caddy/Nginx 等 TLS 反代后；注意 `APP_BASE_URL` 与
  `COOKIES_SECURE`。
- 未装 PM2，日志轮转由 Docker/宿主负责；未装 tini，PID 1 为 node。
- 镜像 859MB（压缩 273MiB），主要来自 Node 24 运行时、生产 node_modules 和
  `@joplin/lib` 编译产物。
- `@rollup/wasm-node` 仅构建期使用；升级 Joplin 后若 rollup 升到 ≥4.50.2，可改用
  `@rollup/rollup-linux-loong64-gnu` 原生 binding。

## 验证命令

```bash
curl -fsS http://127.0.0.1:22300/api/ping
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:22300/login
docker inspect joplin-test --format '{{.State.Health.Status}}'
docker exec joplin-test sh -c 'ls -l /data/temp /data/logs'
docker exec -e PGPASSWORD=joplinpass joplin-pg \
  psql -h 127.0.0.1 -U joplin -d joplin -c 'select count(*) from knex_migrations'
docker restart joplin-test && sleep 15 && curl -fsS http://127.0.0.1:22300/api/ping
```

端到端 API 测试脚本见 [test-api.mjs](test-api.mjs)：

```bash
docker exec <node-container> node /build/test-api.mjs
```
