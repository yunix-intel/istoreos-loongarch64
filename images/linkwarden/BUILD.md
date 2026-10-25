# Linkwarden 2.16.3 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/linkwarden:loong64` / `:24.10-la5` / `:2.16.3`
- Registry digest（三个 tag 相同）：
  `sha256:742abfdd51f656f5b8b5e3c06c584155a7bcb5b678170781d37804a56950b852`
- 架构：`linux/loong64`
- 本地大小：1,027,424,379 B（1.03 GB），10 层
- Hub 压缩后：333,396,847 B（317.9 MiB）
- 镜像 ID：`sha256:4825ae5e8f23e38ec98ee79fe8581a6f21f08a207d7503b0b0703d3b66675534`
- 版本：Linkwarden `v2.16.3`（commit `952ac4540657cae3a67c3ca59433899d2fda8374`）、
  Node.js 24.22.1、Next.js 15.5.21、Prisma 7.10.1、`@prisma/adapter-pg` 7.10.1、
  `pg` 8.23.1、bcryptjs 3.0.3、Playwright 1.57.0、tsx 4.19.3 / esbuild 0.25.2
- 运行：UID/GID `1118`，端口 3000，持久化卷 `/data/data`，`STORAGE_FOLDER=data`
- 范围：Web + Worker 单容器。不内置 Chromium；截图/PDF/Readability 通过
  `PLAYWRIGHT_WS_URL` 接 LBrowser sidecar。`DISABLE_BROWSER=true` 时书签 CRUD
  正常，归档字段为 `unavailable`。
- 实测：全新库 99 个迁移、重启幂等、`/` 200、注册/登录、集合/标签/书签、
  无浏览器降级、LBrowser 截图/PDF/Readability/preview、重启后数据与归档保留、
  搜索回退、邮件验证与找回密码（mock SMTP）、UID 1118、三 tag 同 digest。

### 上游 commit 说明

GitHub 的 `v2.16.3` tag 指向 `474dd11`；需求指定的 `952ac454` 是其后一个
merge commit（仅 `apps/mobile` 变更，服务端代码一致）。本镜像按 `952ac454`
构建，`apps/web/package.json` 仍为 `v2.16.3`。

## 上游与 x86_64 构建

构建机：WSL2 Ubuntu 26.04 x86_64，Node 24.22.1，Yarn 4.12.0。
`@next/swc` 没有 loong64 包，所以 Next 必须在 x86_64 构建；`.next` 是架构无关
JS，运行镜像只跑 `next start` 和 `tsx worker.ts`。

```bash
export PATH=$HOME/node24/bin:$PATH
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 NEXT_TELEMETRY_DISABLED=1
export YARN_ENABLE_IMMUTABLE_INSTALLS=false

git clone --depth 1 --branch v2.16.3 https://github.com/linkwarden/linkwarden.git
cd linkwarden
git fetch --depth 2 origin 952ac4540657cae3a67c3ca59433899d2fda8374
git checkout FETCH_HEAD

# 应用依赖/源码改造（见下一节）
python3 -I /path/to/images/linkwarden/prepare-upstream.py .

yarn install
DATABASE_URL=postgresql://build:build@127.0.0.1:5432/build yarn prisma:generate
DATABASE_URL=postgresql://build:build@127.0.0.1:5432/build \
NEXTAUTH_URL=http://127.0.0.1:3000/api/v1/auth \
NEXTAUTH_SECRET=build-time-placeholder-0000000000000000 \
  yarn web:build
```

`prepare-upstream.py` 是可重复执行的，改动如下。

### Prisma 7

| 文件 | 改动 |
|---|---|
| `packages/prisma/package.json` | `prisma` / `@prisma/client` = `7.10.1`；加 `@prisma/adapter-pg` 7.10.1、`pg` 8.23.1；`prisma` CLI 移到 devDependencies |
| `packages/prisma/schema.prisma` | 删除 `datasource.url`；保留 `prisma-client-js` generator（v7 仍支持，pin 版本） |
| `packages/prisma/prisma.config.ts`（新） | `defineConfig({ schema, migrations, datasource: { url: env("DATABASE_URL") } })`，仅供 x86 CLI 使用 |
| `packages/prisma/index.ts` | `new PrismaClient({ adapter: new PrismaPg({ connectionString }) })` |
| `apps/worker/lib/getLinkBatch.ts` | 该文件是唯一一处绕过 shim 的 `new PrismaClient()`；改为复用 `@linkwarden/prisma` 的 `prisma`（否则 v7 抛 “driver adapter is required”） |

Prisma 7 的 Query Compiler 是 WASM，运行时不需要任何 Rust query-engine /
schema-engine 二进制；`@prisma/adapter-pg` 用纯 JS 的 `pg`，所以 loong64 上
`findMany`、`include`、`$transaction` 等均已实际跑通（注册、登录、CRUD、worker
查询均经过它）。

### 迁移器 `prisma-migrate.mjs`

`prisma migrate deploy` 在 loong64 缺少 `schema-engine-debian-openssl-1.1.x`，
因此用约 180 行 Node 脚本替代：

- 读取 `packages/prisma/migrations/*/migration.sql`，按目录名排序执行；
- 维护 Prisma 官方格式的 `_prisma_migrations` 表
  （`id` UUID、`checksum` SHA-256、`finished_at`、`migration_name`、`logs`、
  `rolled_back_at`、`started_at`、`applied_steps_count`）；
- 每个迁移一个事务；checksum 与库中记录不一致时拒绝启动；
- `pg_advisory_lock(72707369)` 串行化并发实例；
- 已完成的迁移跳过，未完成（中断）的记录删除后重试，因此可重复执行；
- 连接数据库带 60 次重试，等待 PostgreSQL 就绪；
- 成功后输出 `MIGRATIONS_OK applied_now=… already=… recorded=99 folders=99`。

迁移表与 checksum 格式与 Prisma 一致，未来在 x86 上用 `prisma migrate deploy`
仍能识别该库。

### sharp / bcrypt / Next

- `apps/web/package.json` 删除 `sharp`；`bcrypt` → `bcryptjs@^3.0.3`（6 个文件
  只改 import，API 同名、哈希格式兼容）；删除 `@types/bcrypt`。
- Next 自己仍会把 `sharp` 作为 optional dependency 拉进 node_modules；构建上下文
  组装时删除 `node_modules/sharp`、`node_modules/@img`，运行镜像内不存在 sharp。
- `apps/web/next.config.js`：`images.unoptimized: true`；
  `serverExternalPackages: ["@prisma/client","@prisma/adapter-pg","pg"]`。
- 根 `postinstall` 改为只跑 `patch-package`，不再调用 Playwright 的
  `install --with-deps`（Ubuntu 26.04 不受 Playwright 1.57 支持，且不需要浏览器）。
- `apps/worker/workers/linkProcessing.ts`：`DISABLE_BROWSER` /
  `DISABLE_PRESERVATION` 为 true 时不再 `launchBrowser()`，只把链接交给
  `archiveHandler` 标记为 `unavailable`；否则 worker 会因找不到浏览器而退出。

### 构建上下文 `artifacts/`（不提交仓库）

```bash
cd linkwarden
YARN_ENABLE_SCRIPTS=false yarn workspaces focus --production \
  linkwarden @linkwarden/web @linkwarden/worker
rm -rf apps/web/.next/cache           # 364 MB，运行时不需要

mkdir -p /tmp/esb && cd /tmp/esb
npm pack @esbuild/linux-loong64@0.25.2
cd -

rm -rf artifacts && mkdir -p artifacts
cp -a node_modules artifacts/
rm -rf artifacts/node_modules/sharp artifacts/node_modules/@img \
       artifacts/node_modules/@next/swc-linux-x64-gnu \
       artifacts/node_modules/@esbuild/linux-x64
mkdir -p artifacts/node_modules/@esbuild/linux-loong64
tar xzf /tmp/esb/esbuild-linux-loong64-0.25.2.tgz \
  -C artifacts/node_modules/@esbuild/linux-loong64 --strip-components=1
chmod +x artifacts/node_modules/@esbuild/linux-loong64/bin/esbuild

mkdir -p artifacts/apps/web artifacts/apps/worker
cp -a apps/web/.next apps/web/public apps/web/templates apps/web/next.config.js \
      apps/web/next-i18next.config.js apps/web/package.json artifacts/apps/web/
rm -rf artifacts/apps/web/.next/cache
cp -a apps/worker/{package.json,tsconfig.json,worker.ts,index.ts,lib,workers,templates} \
      artifacts/apps/worker/
cp -a packages artifacts/
```

`node_modules/@linkwarden/*` 是指向 `../../apps/*`、`../../packages/*` 的相对
symlink，Docker `COPY` 会原样保留，因此运行时布局必须是 `/data/{apps,packages}`。

### loong64 镜像

`Dockerfile` 单阶段，基于 `yunixintel/node:24.22.1`（openEuler 24.03 /
glibc 2.38）：

- 安装 `ca-certificates tzdata bash util-linux shadow`，创建 UID/GID 1118；
- `COPY --chown=1118:1118 artifacts/ /data/`，避免额外 chown 层；
- 复制 `prisma-migrate.mjs` 与 `entrypoint.sh`；
- 运行库不含 Chromium，也不含 Playwright 浏览器。

```bash
cd images/linkwarden
./build.sh
# 等价于
DOCKER_BUILDKIT=0 docker build --network=host \
  -t yunixintel/linkwarden:loong64 \
  -t yunixintel/linkwarden:24.10-la5 \
  -t yunixintel/linkwarden:2.16.3 .
```

## 运行

```bash
docker run -d --name linkwarden -p 3000:3000 \
  -v linkwarden-data:/data/data \
  -e DATABASE_URL=postgresql://linkwarden:change-me@postgres:5432/linkwarden \
  -e NEXTAUTH_URL=http://<host>:3000/api/v1/auth \
  -e NEXTAUTH_SECRET="$(openssl rand -base64 32)" \
  yunixintel/linkwarden:loong64
```

- `NEXTAUTH_URL` 必须带 `/api/v1/auth`（上游约定），不能只写站点根。
- `NEXTAUTH_SECRET` 可省略：entrypoint 会生成 48 字节随机值并以 0600 持久化到
  `/data/data/.nextauth_secret`；显式传环境变量时不写文件。
- `DATABASE_URL`、`NEXTAUTH_URL` 为必填，缺失时退出码 1。
- 持久化路径是 `/data/data`（上游 `cwd/../..` + `STORAGE_FOLDER=data` 的结果）。
  镜像声明 `VOLUME ["/data/data"]`；应用代码在 `/data` 的其余路径。挂载 `/data`
  会覆盖应用文件，请勿这样做。
- 未配置任何浏览器（`PLAYWRIGHT_WS_URL` /
  `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH`）时，entrypoint 自动设置
  `DISABLE_BROWSER=true` 并打印提示，避免 worker 崩溃。
- `DISABLE_BROWSER=true` 时书签/集合/标签/搜索/导入导出仍可用；截图、PDF、
  Monolith、Readability、OG 预览、归档期 AI 打标不执行，字段为 `unavailable`。
- 未配 Meilisearch 时搜索回退到 Prisma `contains`（name/url/description/tag）。
- 无 sharp：`/_next/image` 优化关闭，图片原图直出。

### 邮件 / `BASE_URL`

邮件验证、改邮箱、找回密码、邀请四类邮件都读取
`/data/apps/web/templates/*.html`。公共镜像和 private 镜像均已包含
`acceptInvitation.html`、`passwordReset.html`、`verifyEmail.html`、
`verifyEmailChange.html`；缺失时接口会抛
`ENOENT /data/apps/web/templates/verifyEmail.html`。

启用邮件需要同时设置：

| 变量 | 示例 | 说明 |
|---|---|---|
| `EMAIL_FROM` | `linkwarden@example.com` | 发件人；同时决定 `emailEnabled`（与 `EMAIL_SERVER` 一起） |
| `EMAIL_SERVER` | `smtp://user:pass@smtp.example.com:587` | Nodemailer 连接串；无认证可写 `smtp://host:port` |
| `BASE_URL` | `http://<host>:3000` | **站点根**，不要带 `/api/v1/auth`；邮件正文链接用 `BASE_URL` |
| `NEXTAUTH_URL` | `http://<host>:3000/api/v1/auth` | NextAuth 回调；验证邮件实际跳到 `/auth/verify`，再由前端转 `/api/v1/auth/callback/email` |

- `BASE_URL` 未设置时，邮件正文中的链接会变成
  `undefined/auth/verify?token=…`，用户无法完成验证。
- `EMAIL_FROM`/`EMAIL_SERVER` 任一未设置时 `emailEnabled=false`：注册不再要求
  邮箱，也不会发送验证邮件，`emailVerified` 一直为空。
- 邮件模板随 `apps/web/templates` 进入镜像；x86 构建上下文的
  `artifacts/apps/web/` 必须包含该目录（见上一节）。

启用邮件的完整示例（在基础 `docker run` 上追加）：

```bash
-e BASE_URL=http://<host>:3000 \
-e EMAIL_FROM=linkwarden@example.com \
-e EMAIL_SERVER=smtp://user:pass@smtp.example.com:587
```

## LBrowser sidecar（不内置、不推送）

LBrowser 许可证不清晰，镜像内没有浏览器字节。需要真实归档时，在宿主挂载
`/opt/apps/lbrowser` 并以 sidecar 运行：

```yaml
services:
  postgres:
    image: yunixintel/postgres:loong64
    environment:
      POSTGRES_USER: linkwarden
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: linkwarden
    volumes: ["./pgdata:/var/lib/postgresql/data"]

  linkwarden:
    image: yunixintel/linkwarden:loong64
    depends_on: [postgres, lbrowser]
    ports: ["3000:3000"]
    volumes: ["./data:/data/data"]
    environment:
      DATABASE_URL: postgresql://linkwarden:change-me@postgres:5432/linkwarden
      NEXTAUTH_URL: http://<host>:3000/api/v1/auth
      NEXTAUTH_SECRET: <openssl rand -base64 32>
      STORAGE_FOLDER: data
      PLAYWRIGHT_WS_URL: http://lbrowser:9222

  lbrowser:
    image: local/lbrowser-runtime:3.4.2293.2
    command: ["serve"]
    shm_size: "1g"
    volumes:
      - /opt/apps/lbrowser:/opt/apps/lbrowser:ro
```

- `PLAYWRIGHT_WS_URL` 实际走 `chromium.connectOverCDP`，写 `http://`，不是 `ws://`。
- 必须 `--shm-size=1g`（至少 512 MB）。
- LBrowser DevTools 只监听 `127.0.0.1`，`serve` 内的 `cdp-proxy.mjs` 负责跨容器
  监听 9222 并改写 `/json/*` 的 WebSocket 地址。
- 也可让 worker 直接拉起挂载的宿主 LBrowser：
  `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH=/opt/apps/lbrowser/lbrowser`。
- `local/lbrowser-runtime` 只在本机构建，不推送。

## 测试结果（Host A / 3A6000，实际执行）

测试环境：`lw-pg`（`yunixintel/postgres:loong64`）+ `lw-app`
（`-p 13000:3000`、`-v lwtest-data:/data/data`、
`NEXTAUTH_URL=http://127.0.0.1:13000/api/v1/auth`）。

| 项 | 结果 |
|---|---|
| 全新数据库迁移 | `applied_now=99 already=0`，`_prisma_migrations` 99 行且 99 行 finished；`/` 200 |
| 重启幂等 | `MIGRATIONS_OK applied_now=0 already=99 recorded=99`，计数仍 99，无重复 |
| `/` | 200；Docker health 正常（`starting` 后转 healthy） |
| 注册 | `POST /api/v1/users` 201；用户 id=1 |
| 登录 | NextAuth credentials 200；`/api/v1/users/me` 返回同一用户 |
| 集合 | `POST /api/v1/collections` 201，id=1 |
| 标签 | `POST /api/v1/tags` 200，id=1 |
| 书签 | `POST /api/v1/links` 201，`https://example.com`，id=1 |
| 无 sidecar + `DISABLE_BROWSER=true` | worker 正常处理，link 字段 `image/pdf/monolith/readable/preview=unavailable`，无浏览器缺失报错；书签 CRUD 正常 |
| 有 sidecar（`PLAYWRIGHT_WS_URL=http://lw-browser:9222`） | worker 日志 `Connecting to remote browser`；新书签 id=2 |
| 截图 | `/data/data/archives/1/2.jpeg`，62,610 B，JPEG 1265×823 |
| PDF | `/data/data/archives/1/2.pdf`，92,483 B，PDF 1.4，1 页 |
| Readability | `/data/data/archives/1/2_readability.json`，3,114 B，含正文 JSON |
| OG 预览 | `/data/data/archives/preview/1/2.jpeg`，26,300 B，JPEG 1280×720 |
| Monolith/HTML | 镜像未装 monolith，日志 `spawn monolith ENOENT`，被 `handleMonolith` 捕获；其他格式成功，link 的 `monolith=unavailable` |
| 重启持久化 | 重启后迁移不重复；2 个 link、集合/标签、截图/PDF/Readability/preview 仍在；会话 cookie 仍有效 |
| 搜索（无 Meilisearch） | `GET /api/v1/links?searchQueryString=Example` 命中，`textContent` 已由 Readability 写入 |
| 进程用户 | `docker top`：`next-server` 与 `tsx worker.ts` 均为 UID 1118；entrypoint 为 root |
| 必填参数 | 缺 `NEXTAUTH_URL` / `DATABASE_URL` 时 entrypoint 报错退出 1 |
| 自动 secret | 未传 `NEXTAUTH_SECRET` 时生成 64 字符文件（0600）；重启输出 `Loaded NEXTAUTH_SECRET` |
| 邮件模板 | `/data/apps/web/templates/` 内 4 个文件（acceptInvitation/passwordReset/verifyEmail/verifyEmailChange），9006/8761/8301/9459 B |
| 注册（启用邮件） | `POST /api/v1/users` 201，`emailVerified=null` |
| 未验证凭据登录 | `callback/credentials` 401，`error=Email not verified.` |
| 验证邮件 | mock SMTP 收到 9,403 B；正文链接 `http://127.0.0.1:13010/auth/verify?token=…&email=…`（`BASE_URL` 生效） |
| 邮件回调 | `/auth/verify` 200；`/api/v1/auth/callback/email?token&email` 302 → `http://127.0.0.1:13010`，Set-Cookie `next-auth.session-token` |
| 验证结果 | `/api/v1/users/me` 200，`emailVerified:"2026-10-25T11:01:14.491Z"`；DB `emailVerified` 非空 |
| 已验证登录 | `callback/credentials` 200，`/users/me` 200 |
| 找回密码邮件 | `POST /api/v1/auth/forgot-password` 200；mock SMTP 收到 9,354 B（`passwordReset.html`） |
| 依赖版本 | `@prisma/client` 7.10.1、`@prisma/adapter-pg` 7.10.1、`pg` 8.23.1、`bcryptjs` 3.0.3 |
| 无 sharp / no x64 SWC | 容器内 `node_modules/sharp`、`@img`、`@next/swc-*` 均不存在 |
| loong64 esbuild | `/data/node_modules/@esbuild/linux-loong64/bin/esbuild --version` = 0.25.2，ELF LoongArch |
| 架构 / digest | `linux/loong64`；`:loong64`、`:24.10-la5`、`:2.16.3` 均为 `sha256:742abfdd…` |

测试使用的 sidecar 为 `local/lbrowser-runtime:3.4.2293.2 serve`（挂载宿主
`/opt/apps/lbrowser:ro`，`--shm-size=1g`），Chromium 138.0.7204.310。

## 补验（2026-10-25）

- monolith 2.10.1（Rust 1.85，5m27s）挂载后全页归档 PASS，单文件 HTML 自包含。
- Meilisearch 1.13.3 源码构建（22m21s，`--no-default-features`）PASS；7 条索引，拼写容错命中。
- AI 打标（mock OpenAI）PASS；并发 `ARCHIVE_TAKE_COUNT=3` 触发上游 P2002 竞态，建议串行。
- HTML/Pocket/Wallabag 导入 PASS；用户隔离 PASS；OAuth BLOCKED（无 provider）。
- LBrowser 截图 62,610B、PDF 92,483B、Readability 3,114B、预览 26,300B；带 cookie 可访问，匿名 401。
- 邮箱流（2026-10-25 修复后复测）PASS：补入 `apps/web/templates/` 并重建，
  注册→mock SMTP 验证邮件→`/auth/verify`→`/api/v1/auth/callback/email`
  302 + session→`emailVerified` 非空；未验证凭据登录 401；找回密码邮件
  `passwordReset.html` 也已发出。

## 未验证

- **Monolith / 单文件 HTML**：发布镜像不内置 monolith（默认 `unavailable`）；
  补验时以额外挂载的 monolith 2.10.1 验证 PASS。
- **Meilisearch**：发布镜像不内置；补验用外部源码构建实例验证 PASS，
  未配时仍回退 SQL `contains`。
- **AI 打标/摘要**、**RSS 外部源**、**导入 HTML/Pocket/Wallabag**：补验已 PASS
  （mock OpenAI / 外部实例），未在发布镜像内重复。
- **Wayback Machine 提交**、**OAuth/SSO**、**Stripe**：未配置。
- **改邮箱（verifyEmailChange.html）/ 邀请（acceptInvitation.html）完整链路**：
  模板已随镜像提供，未逐项跑通；邮箱验证与找回密码已实测。
- **上传 PDF/图片类型的书签**（`type=pdf/image`）：未测试。
- **多用户/邀请/权限**：未逐项测试。
- **非 root、只读根文件系统、SELinux/AppArmor、rootless Docker**：未验证。
- **LBrowser 的 WebGL/视频/DRM/GPU 与复杂站点回归**：未验证；本次只测
  example.com。
- **反向代理后的 `NEXT_PUBLIC_USER_CONTENT_DOMAIN` 归档查看页**：未配置；
  归档文件与 DB 字段已验证。

## 体积

```text
docker images yunixintel/linkwarden
yunixintel/linkwarden  loong64     4825ae5e8f23  1.03GB
yunixintel/linkwarden  24.10-la5   4825ae5e8f23  1.03GB
yunixintel/linkwarden  2.16.3      4825ae5e8f23  1.03GB
```

本地 1,027,424,379 B；Hub manifest 10 层，压缩后合计 333,396,847 B
（317.9 MiB）。主要组成：openEuler + Node 基础层约 426 MB，
`node_modules` 约 700 MB（未压缩），Next `.next` 约 27 MB，邮件模板 52 KB。

## 推送

```bash
docker save -o linkwarden.tar yunixintel/linkwarden:loong64
export HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=http://127.0.0.1:17890
/build/bin/crane push linkwarden.tar yunixintel/linkwarden:loong64
/build/bin/crane push linkwarden.tar yunixintel/linkwarden:24.10-la5
/build/bin/crane push linkwarden.tar yunixintel/linkwarden:2.16.3
/build/bin/crane digest yunixintel/linkwarden:loong64
# sha256:742abfdd51f656f5b8b5e3c06c584155a7bcb5b678170781d37804a56950b852
```

## 文件

- `Dockerfile`：单阶段运行镜像，UID 1118，无 Chromium/sharp/Prisma 原生引擎
- `entrypoint.sh`：必填校验、浏览器缺省降级、secret 持久化、迁移、Web + Worker
- `prisma-migrate.mjs`：99 个 SQL 迁移的幂等执行器（checksum + advisory lock）
- `prepare-upstream.py`：对 v2.16.3/952ac454 的源码与依赖改造，可重复执行
- `build.sh`：`DOCKER_BUILDKIT=0 docker build --network=host`，打三个 tag
- `artifacts/`：x86_64 生成的构建上下文（不提交仓库）
