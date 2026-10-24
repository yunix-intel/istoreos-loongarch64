# Joplin Server loong64 移植可行性报告
日期：2026-10-24。目标：龙芯 3A6000 / Loongnix 25（6.6.52 内核，16K 页，8 核，31GB），
构建容器 openEuler 24.03 / glibc 2.38。对象是 Joplin 同步服务端，不含桌面/移动客户端。
## 0. 结论
**Go（推荐 PostgreSQL；小规模单机也可 SQLite）。** 唯一真正的原生阻塞是 `sqlite3 5.1.6`，可源码
编译；`sharp`、`sqlite-vec` 都不是服务端运行时依赖。不需要 x86 前端阶段。预计 **2–3 人日**。
三个纠正：
1. **sharp/sqlite-vec 不是服务端运行时依赖。** 稳定 tag `v3.7.21` 里它们是 `@joplin/lib`
   的 devDependencies（`packages/lib/package.json:43-44`）；服务端只执行
   `shimInit({ nodeSqlite })`（`packages/server/src/app.ts:39-42`）。任务里的 sharp `0.35.0`
   对应 dev 分支，最新稳定 tag 是 `0.34.5`，结论相同。
2. **PostgreSQL 不能绕开 sqlite3。** PG 只替换主库；服务端仍会建 `${tempDir}/joplin.sqlite`
   临时库（本方案为 `/data/temp/joplin.sqlite`），用于 lib 的模型序列化/分享页渲染
   （`packages/server/src/utils/joplinUtils.ts:107-112`），且 `sqlite3` 在 app.ts 顶层 import，
   `DB_CLIENT=pg` 也会加载原生模块。
3. **sqlite-vec 可以完全禁用。** 它只服务桌面端 AI 向量检索；服务端没有 AI/向量代码，缺省时
   `JoplinDatabase` 打印 “sqlite-vec not provided ... vector search disabled” 后继续启动
   （`packages/lib/JoplinDatabase.ts:154-183`）。
版本锁定：tag **v3.7.21**（2026-09-25）；`@joplin/server` 3.7.1，`@joplin/lib` 3.7.3；
Node `>=22.12`，统一 Node 24.22.1；Yarn 4.16.0（自带 `.yarn/releases/yarn-4.16.0.cjs`）；dev 分支 server 3.7.3、sharp 0.35.0，不影响结论。
## 1. 上游构建方式

- Yarn 4 workspace（`nodeLinker: node-modules`，`nmHoistingLimits: workspaces`）+ gulp。
- server `build` 只生成 `dist/packageInfo.js`（`packages/server/gulpfile.js`）；TypeScript 由根脚本
  `yarn tsc` / `buildSequential` 编到各 workspace 的 `dist/`。
- **没有 SPA/打包器**：管理/登录页是 Mustache + `public/` 静态 CSS/JS；不存在需 x86 构建的产物。
- 运行产物：`packages/server/{dist,src/views,public,assets,package.json,node_modules}`。
- 官方 `Dockerfile.server`：`node:24` 构建，`yarn install` 后 `focus --production --all`；运行用
  `node:24-slim` + PM2 + tini。因此可以全程在 loong64 上构建，**不要**照搬 x86 前端阶段。
## 2. 原生依赖逐项判定

| 模块 | 声明位置 | 运行时需要 | 结论 |
|---|---|---|---|
| `sharp 0.34.5`（dev 0.35.0） | lib devDependency；tools 的 production 依赖 | 否 | 不装/不加载；`focus @joplin/server` 会裁掉 tools |
| `sqlite-vec 0.1.9` | lib devDependency | 否 | 禁用；服务端不传 `sqliteVec` |
| `sqlite3 5.1.6` | server/lib 的 production 依赖 | **是** | 源码编译，必须过门禁 |
| `onnxruntime-node 1.24.3` | lib devDependency | 否 | 不装/不加载 |
| `better-sqlite3` | lib 的实验驱动 | 否 | 不能 drop-in 替换 |

`@joplin/tools` 把 sharp 写成 production 依赖（`packages/tools/package.json:41`），但 tools 只是
server 的 devDependency（`packages/server/package.json:67-68`），运行时不 import。**不要用
`focus --production --all`**，否则 tools 及 sharp 可能留在产物里；用 `focus @joplin/server`。
## 3. 数据库支持
`DB_CLIENT=pg` 分支在 `config.ts:58-78`，knex 使用 pg dialect（`db.ts:87-110`）。官方 compose 用
PostgreSQL 16，代码最低要求 12（`db.ts` 的 `versionCheck`），本仓库 PostgreSQL 15.18 满足要求；
上游单测也覆盖 PostgreSQL 15.3。建议直接用 `yunixintel/postgres:loong64`。
但即使 PG 可用，服务端启动仍无条件 `import * as nodeSqlite from 'sqlite3'` 并
`shimInit({ nodeSqlite })`；随后 `initializeJoplinUtils()` 创建 `${tempDir}/joplin.sqlite`
临时库（每次删除重建），用于笔记/资源/标签的序列化与分享页渲染。这个临时库与主库类型无关。
所以“改用 PostgreSQL 完全避开 SQLite 原生模块”不成立；真要无 sqlite3，需同时改 `app.ts` 和
`joplinUtils.ts`，把临时模型库改为 PG/better-sqlite3 适配层，改动大且偏离上游，不建议。
`DB_CLIENT=sqlite3` 也可用，但只适合单实例、小规模个人；官方 README 把 SQLite 定位为测试/开发
默认。生产建议 PG。服务端不 import 任何 AI/向量模块，sqlite-vec 缺失没有功能损失。
## 4. sharp 与 sqlite-vec

- sharp 在 lib 中用于桌面/CLI 的图片读取、缩放和 `imageToDataUrl`；服务端没有调用点，只把资源
  当二进制 blob 存取/下发。`shimInit` 只传 nodeSqlite，`shim.sharpEnabled()` 为 false。
- **推荐路径：不安装 sharp。** 最终 `focus @joplin/server` 裁掉。若未来需要，按
  `docs/research/karakeep-unblock.md` §2.1 源码构建 libvips 8.18.7 再用
  `SHARP_FORCE_GLOBAL_LIBVIPS=1` 编 sharp；会增加 80–120MB 和 1–2 天，对 Joplin Server 无收益。
  sharp 的 wasm32 资产不是 Node 服务端原生模块的通用替代，服务端也不调用。
- sqlite-vec 只用于桌面端 `note_embeddings_vec` 向量索引/KNN；服务端没有该功能。启动日志
  “sqlite-vec not provided ... vector search disabled” 是预期，不是错误。若未来桌面端要在
  loong64 启用：它是单文件 C 扩展，Linux 默认走标量路径，没有 LoongArch 汇编依赖，用系统
  sqlite3 头文件 `gcc -fPIC -shared -O3 sqlite-vec.c -o vec0.so` 即可；本服务端不需要。
## 5. sqlite3 5.1.6 可编译性
不要换 better-sqlite3：`DatabaseDriverNode` 明确使用 node-sqlite3 的回调 API
（`new sqlite3.Database()`、`.verbose()`、`.loadExtension()`，见
`packages/lib/database-driver-node.ts`）。lib 的 `database-driver-better-sqlite.ts` 是实验驱动，
服务端没使用，且注释提示其 `SQLITE_DQS=0` 与现有 SQL 不兼容。系统 sqlite 也只能让 binding.gyp
链接外部库，addon 仍要编译，没有收益；继续用 npm 包自带的 SQLite 3.41.1。
推荐命令（Node 24.22.1，镜像内 `/opt/node24/include/node`）：

```bash
# 装 Yarn 依赖但跳过 install/postinstall，避免 sharp/onnxruntime 下载预编译
YARN_ENABLE_SCRIPTS=false node .yarn/releases/yarn-4.16.0.cjs install --inline-builds
SQLITE_DIR=$(dirname "$(node -p "require.resolve('sqlite3/package.json')")")
NPRE=$(find /build -path '*/node_modules/.bin/node-pre-gyp' | head -1)
(cd "$SQLITE_DIR" && npm_config_nodedir=/opt/node24 JOBS=max \
  "$NPRE" rebuild --build-from-source)
# 门禁：加载并打开文件数据库（同时验证 16K 页宿主）
node -e "const s=require('sqlite3'); const db=new s.Database('/tmp/t.sqlite');
db.get('select sqlite_version() v',(e,r)=>{if(e)process.exit(1);console.log(r);db.close();});"
```

`node-pre-gyp rebuild` 读取 `package.json` 的 `binary.module_name`，在 Node 24 上选择
`napi-v6-linux-glibc-loong64` 产物；`npm_config_nodedir=/opt/node24` 用镜像内头文件，避免从
unofficial-builds 下载。`JOBS=max` 用满 8 核。
证据：本仓库 `images/nocodb/Dockerfile` 已在 loong64 上用 `npx node-gyp rebuild` 编过
`sqlite3 ^5.1.7`；本次又对 `sqlite3@5.1.6` 做了独立 spike，结果见 §11。
## 6. Dockerfile 多阶段建议
构建上下文用 Joplin `v3.7.21` 源码（并把本仓库 `docker-entrypoint.sh` 放进上下文）；按上游
`Dockerfile.server` 的 COPY 清单只复制 server/lib/renderer/utils/tools/htmlpack/fork 等目录，
避免装入 desktop/mobile workspace。**没有 x86 阶段。**

```dockerfile
FROM yunixintel/node:24.22.1 AS build
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL \
      --setopt=install_weak_deps=False gcc-c++ make python3 && dnf clean all
WORKDIR /build
# 按上游 Dockerfile.server 复制 .yarn/releases、package.json、yarn.lock、gulpfile.js、tsconfig.json 及 packages/{server,lib,renderer,utils,tools,htmlpack,fork-*} 等
RUN sed -i '/onenote-converter/d' packages/lib/package.json && \
    YARN_ENABLE_SCRIPTS=false node .yarn/releases/yarn-4.16.0.cjs install --inline-builds
RUN SQLITE_DIR=$(dirname "$(node -p "require.resolve('sqlite3/package.json')")"); \
    NPRE=$(find /build -path '*/node_modules/.bin/node-pre-gyp' | head -1); \
    cd "$SQLITE_DIR" && npm_config_nodedir=/opt/node24 JOBS=max \
      "$NPRE" rebuild --build-from-source
RUN BUILD_SEQUENCIAL=1 node .yarn/releases/yarn-4.16.0.cjs run buildSequential && \
    YARN_ENABLE_SCRIPTS=false node .yarn/releases/yarn-4.16.0.cjs \
      workspaces focus --production @joplin/server && \
    node -e "require('sqlite3'); console.log('sqlite3 ok')"
FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
      shadow util-linux ca-certificates tzdata curl libstdc++ && dnf clean all && \
    groupadd -g 1119 joplin && useradd -u 1119 -g 1119 -M -d /data -s /sbin/nologin joplin && mkdir -p /data /opt/joplin
COPY --from=build /opt/node24 /opt/node24
COPY --from=build /build/packages /opt/joplin/packages
RUN mkdir -p /data/{logs,temp,resource,storage} && \
    ln -s /data/logs /opt/joplin/packages/server/logs && \
    ln -s /data/temp /opt/joplin/packages/server/temp && \
    ln -s /data/resource /opt/joplin/packages/server/resource
COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENV PATH=/opt/node24/bin:$PATH NODE_ENV=production RUNNING_IN_DOCKER=1 APP_PORT=22300
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fsS http://127.0.0.1:22300/api/ping >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
```

entrypoint 以 root 启动，只对 `/data` 顶层 `chown 1119:1119`（禁止递归 chown），然后
`exec runuser -u joplin -- /opt/node24/bin/node /opt/joplin/packages/server/dist/index.js`。
不要用 PM2；日志走 stdout，用 Docker `--log-opt max-size` 或宿主 logrotate。运行镜像约 600–800MB。
## 7. 运行参数

| 变量 | 建议值 |
|---|---|
| `APP_BASE_URL` | 外部 URL，如 `https://notes.example.com` |
| `APP_PORT` / `DB_CLIENT` | `22300` / `pg` |
| `POSTGRES_HOST` / `PORT` | compose 服务名 `db` / `5432` |
| `POSTGRES_DATABASE` / `USER` / `PASSWORD` | 与 postgres 容器一致；库/用户需预先存在 |
| `RUNNING_IN_DOCKER` | `1`（镜像已设） |
| `MAX_TIME_DRIFT` | 无外网 UDP/123 时设 `0`；否则保持 2000ms |
| `COOKIES_SECURE` | 反代 TLS 时 `true` |
| `DEFAULT_ADMIN_PASSWORD` | 首启前设强密码；默认 `admin` |
| `SQLITE_DATABASE` / `STORAGE_DRIVER` | 仅 SQLite 设 `/data/db.sqlite`；可选 `Type=Filesystem; Path=/data/storage` |

设计文档里的 `APP_ADMIN_EMAIL` **代码不读取**；管理员固定 `admin@localhost`
（`packages/server/src/db.ts:38`），登录后改密码并另建同步用户。Postgres 主机不要写
`localhost`，`RUNNING_IN_DOCKER=1` 时会改写成 `host.docker.internal`；用服务名 `db` 最稳。
## 8. 验证步骤
1. `docker inspect` 确认 `loong64`；`file`/`readelf -h` 确认 `node_sqlite3.node` 是 LoongArch。
2. 构建门禁：`node -e "require('sqlite3')"`；`ldd .../node_sqlite3.node | grep 'not found'` 为空。
3. 启动 PG 与 Joplin；日志出现 `Auto-migrating database...`、`Latest migration:`，最后
   `Starting server ... on port 22300`。
4. `curl -fsS http://127.0.0.1:22300/api/ping` 返回 `{"status":"ok",...}`。
5. 登录 `admin@localhost`，改密码，新建普通用户；Joplin 客户端同步目标设为 Joplin Server，
   URL 填 `APP_BASE_URL`，用普通用户同步。
6. 创建含图片附件的笔记，双客户端同步，确认分享页图片可打开；重启容器后再次同步。
7. 检查 `/data/temp/joplin.sqlite`、`/data/logs`；主库在 PG。预期日志含
   `sqlite-vec not provided ... vector search disabled`，不是错误。
8. 可选：`DB_CLIENT=sqlite3` + `SQLITE_DATABASE=/data/db.sqlite` 做单机建库/同步冒烟。
## 9. 功能降级清单

| 功能 | 影响 |
|---|---|
| 笔记/文件夹/标签同步、分享、发布页 | 无影响 |
| PostgreSQL 主库、LDAP/SAML、Stripe、邮件 | 无影响 |
| 附件原图存取/下载 | 无影响（服务端不做图片缩放） |
| 桌面端 AI 语义搜索/向量索引 | 服务端本来就没有；sqlite-vec 禁用 |
| sharp 图片处理 | 服务端没有调用点；不装 |
| PM2 日志轮转 | 不装 PM2；用 Docker/宿主日志轮转替代 |
| Transcribe/HTR | 独立服务，不在本镜像，不影响核心同步 |

## 10. 风险与工作量
主要风险：忘记 `YARN_ENABLE_SCRIPTS=false` 会让 sharp/onnxruntime 安装脚本失败；
`focus --production --all` 可能把 tools 的 sharp 留在产物里；`sqlite3.node` 与 Node ABI 绑定，
升级 Node 必须重编；无外网 NTP 时启动会卡在时间漂移检查并最终失败，需 `MAX_TIME_DRIFT=0`
（前提宿主时间已同步）；`temp/logs/resource` 必须可写；PG 15.18 高于最低 12 但上游 compose
用 16，首次迁移需实测；16K 页宿主要用实际 sqlite3 文件库冒烟；构建需 3–5GB 磁盘和 4GB+ 内存，
OOM 时给 Node 加 `--max-old-space-size=4096`；`APP_BASE_URL`/`COOKIES_SECURE` 配错会导致登录
cookie 或分享链接异常。

| 工作 | 估算 |
|---|---|
| Dockerfile + 依赖裁剪 + sqlite3 编译门禁 | 1 天 |
| PostgreSQL/卷/权限/entrypoint/健康检查 | 0.5–1 天 |
| 双客户端同步、附件、重启、升级验证 | 0.5 天 |
| 文档、镜像标签、回归 | 0.5 天 |
| **合计** | **2–3 人日** |

## 11. 本次 spike 结果
`sqlite3@5.1.6` 在 `yunixintel/node:24.22.1` + openEuler 24.03 工具链下用 node-pre-gyp
（node-gyp 8.4.1）源码编译成功，产物为 `napi-v6-linux-glibc-loong64`；bundled SQLite 3.41.1，
开启 FTS3/4/5、RTREE。宿主 `getconf PAGESIZE=16384`；加载后执行建表、插入、查询得到
`sqlite3 5.1.6 / sqlite 3.41.1 / row { x: 42 } / dbsize 8192`。这是本方案 Go 判定的硬门禁。
## 12. 参考
上游 `Dockerfile.server`、`packages/server/{package.json,src/app.ts,src/utils/joplinUtils.ts,src/config.ts}`、
`packages/lib/{package.json,JoplinDatabase.ts}`（tag `v3.7.21`）；本仓库 `docs/IMAGE-BUILD.md`、
`images/actual-budget/`、`images/nocodb/`、`images/postgres/`、`docs/research/karakeep-unblock.md`。
