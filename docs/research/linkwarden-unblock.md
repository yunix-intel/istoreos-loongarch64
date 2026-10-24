# Linkwarden loong64 移植可行性报告

日期：2026-10-25。目标：龙芯 3A6000 / Loongnix 25 宿主，openEuler 24.03 / glibc 2.38 / 16K 页构建与运行容器。
## 0. 结论
**Go（有条件）**：Linkwarden v2.16.3 可以在 loong64 上完整运行，包括 Prisma 数据层、网页归档（截图/PDF/Readability/Monolith）、登录、集合/标签/搜索/导入导出。原先判断的三个阻塞项都已找到可执行路径，且关键路径已在真机验证：
- **Prisma**：升级到 Prisma 7.10.1（Rust-free WASM query compiler）+ `@prisma/adapter-pg`，运行时不需要任何 Prisma 原生引擎；`prisma migrate deploy` 仍依赖原生 schema-engine，改用小型 SQL 迁移器（约 60 行），99 个迁移已在 PostgreSQL 15.18 上全部跑通。
- **Playwright/Chromium**：Loongnix 25 自带 LBrowser 3.4.2293.2（Chromium 138.0.7204.310），Playwright 1.57 可直接 `executablePath` 拉起，截图/PDF/`page.content()`/CDP 均已实测；也可用 `PLAYWRIGHT_WS_URL` 接外部 browserless。
- **sharp**：源码中 0 处 import，仅 `package.json` 声明；删除并设 `images.unoptimized: true` 即可，不需要编 libvips。
版本锁定：Linkwarden `v2.16.3`（commit `952ac454`，2026-09-09）；Next.js 15.5.21；Node 22.23/24.22；Prisma 7.10.1；Playwright 1.57.0；Monolith 2.10.1；PostgreSQL 15.18；Meilisearch 不首发。
## 1. 上游结构与改动面
| 组件 | 事实 |
|---|---|
| `apps/web` | Next.js 15.5.21，58 个 API route、83 个 server controller；SSR，不能静态导出 |
| `apps/worker` | Node/TypeScript，`tsx worker.ts` 启动；归档、RSS、索引、AI 打标、迁移 worker |
| `packages/prisma` | Prisma schema 324 行，15 model、6 enum；99 个 migration，1142 行 SQL |
| `packages/lib` | Meilisearch 客户端、Readability、预览图（Jimp）、RSS、SSRF 防护 |
| 其他 | `packages/filesystem`、`packages/types`、`packages/router`；mobile/extension 不参与服务端镜像 |
数据库访问集中度：**138 个文件、326 处 `prisma.*` 调用**，但全部经 `packages/prisma/index.ts` 和 `packages/prisma/client/*` 两个 shim 导出；**0 处 `$queryRaw/$executeRaw`**，只有 12 处 `$transaction`、1 处 `groupBy`。因此换 ORM 要改 138 个文件，而升级 Prisma 只需改 shim 和构造器。
## 2. 阻塞项逐项判定
### 2.1 Prisma（推荐：Prisma 7 + driver adapter）
Prisma 7.10.1 的 Query Compiler 是 WASM，客户端不再携带 Rust query-engine/schema-engine 二进制；`@prisma/adapter-pg` 用纯 JS 的 `pg` 连接。实测（loong64，Node 24.22.1，openEuler 24.03）：
```text
npx prisma generate                      # 414ms，成功
prisma.user.findMany() -> P1001          # 无库时正确走到连接阶段，说明 WASM 已工作
PG 15.18 + 99 个 migration 后：user/collection/tag/link CRUD、include、omit、$transaction 全部成功
```
**保留 `prisma-client-js` 旧 generator**（v7 仍支持，生成到 `node_modules/@prisma/client` 与 `.prisma/client`），这样 Linkwarden 现有 65 处 `@linkwarden/prisma/client` 类型导入和 `@auth/prisma-adapter` 都无需改。代价是该 generator 在 v8 可能移除，必须 pin `7.10.1`。

迁移是唯一残留：`prisma migrate deploy` 在 loong64 报 `ENOENT .../schema-engine-debian-openssl-1.1.x`。方案对比：

| 方案 | 改动 | 工期 | 结论 |
|---|---|---|---|
| 自写 SQL 迁移器（推荐） | 1 个 `.mjs`，用 `pg` 顺序执行 migration.sql，写 `_prisma_migrations`（SHA-256 checksum、advisory lock） | 0.5 天 | **已验证**：99 个迁移全过，二次执行幂等，表内 99 行 |
| 源码编 schema-engine | Rust 工程 + OpenSSL + loong64 目标，需跟随 Prisma 内部版本 | 2–5 天 | 不做 |
| 改 Kysely/Drizzle | 138 文件/326 调用/12 事务/99 迁移 | 10–15 天 | 不做，回归风险高 |

注意：schema 里 `datasource.url` 在 v7 已移除，连接串放 `prisma.config.ts`；`new PrismaClient()` 必须传 `adapter`。Prisma 的 migration 表结构必须按官方 DDL 建，否则将来用 x86 跑 `migrate deploy` 会不认。

### 2.2 Playwright / Chromium

用途（全部在 `apps/worker`）：`page.goto`、`content()`、截图 JPEG、PDF、自动滚动、OG 预览图、Monolith/Readability 输入。**不是**只用于截图。

- 官方 Chromium/Playwright 无 linux-loong64 资产，openEuler 也没有 Chromium。Loongnix 25 仓库的 `lbrowser 3.4.2293.2`（Chromium 138.0.7204.310，deb 100MB，安装后 372MB）可用 `--headless=new`。
- 在 openEuler 24.03 容器内装 `gtk2/gtk3/nss/nspr/cups-libs/cairo/gdk-pixbuf2/pango/expat/libxcb/libxkbcommon/at-spi2-*/libX*/mesa-libgbm/libffi/kmod-libs/alsa-lib/pulseaudio-libs/libatomic/systemd-libs/pcre2/gnutls/avahi-libs/krb5-libs/iproute` 后，lbrowser 可运行；Playwright 1.57 拉起后 `version=138.0.7204.310`，`goto/content/setContent/evaluate/screenshot/pdf/connectOverCDP` 全部实测通过。
- 上游已支持三种方式：`PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH=/opt/apps/lbrowser/lbrowser`；`PLAYWRIGHT_WS_URL=ws://browserless:3000?token=...`（`chromium.connectOverCDP`，已用 lbrowser CDP 端口验证）；`DISABLE_BROWSER=true` 时整个归档路径标记 `unavailable`，书签 CRUD 不受影响。Playwright 1.57 期望 Chromium 143，lbrowser 是 138，Linkwarden 用到的 API 已逐个验证，复杂页面仍需回归。

**建议**：首发镜像内置 lbrowser（全功能）；若不允许再分发该浏览器，则改为挂载宿主 `/opt/apps/lbrowser:ro`，或首发 `DISABLE_BROWSER=true` 并明示“无归档”。

### 2.3 sharp

`apps/web/package.json` 声明 `sharp ^0.35.3`，但 `apps/web`/`apps/worker`/`packages` 源码 **0 处 import**；唯一图片处理是 `packages/lib/generatePreview.ts` 的 Jimp。sharp 只被 Next 的 `/_next/image` 优化器间接使用。

- 删依赖 + `next.config.js` 设 `images: { unoptimized: true, ... }`，`<Image>` 直接输出原图 URL，不触发 sharp。
- 不建议源码编：sharp 0.35 要求 libvips ≥ 8.17/8.18，openEuler 24.03 无 `vips`/`vips-devel`，需先编 libvips + meson 全家桶，收益仅是图片压缩。

### 2.4 PostgreSQL / Meilisearch / Node 原生模块

- **PostgreSQL**：上游 compose 用 16-alpine，但 schema/migration 只用 `gen_random_uuid()` 等 PG13+ 特性；本仓库 `yunixintel/postgres:15.18` 已实测跑完 99 个迁移。**必须 UTF8**（该镜像 entrypoint 已用 `--encoding=UTF8 --locale=C.UTF-8`）；SQL_ASCII 库会在 `20260818000000_case_insensitive_name_sorting` 的 ICU collation 上失败。
- **Meilisearch**：`MEILI_MASTER_KEY` 不设时 `meiliClient=null`，搜索自动回退到 Prisma 的 `contains`（name/url/description/tag，大小写不敏感）；索引 worker 直接 return。官方无 loong64 资产，源码编译成本高，首发不装。
- **Node/tsx**：原以为 `tsx` 的 esbuild 没有 loong64，实测 `tsx 4.19.3` 在 loong64 安装 `esbuild 0.25.x` + `@esbuild/linux-loong64` 并成功执行 TS，worker 启动方式可保持 `tsx worker.ts` 不变。
- **bcrypt**：`bcrypt 5.1.0` 是 node-gyp 原生模块。6 个文件使用 `hashSync/compareSync/hash`，改用纯 JS `bcryptjs 3.0.3`（默认导出、API 同名、哈希格式兼容），避免在运行镜像里装 Python/g++/Node headers。代价是登录哈希慢几十到几百毫秒。
- **Next SWC**：`@next/swc` 无 loong64 包，`next build` 仍在 x86_64 WSL2 做（与 Vikunja/ente-web 相同）；`.next` 是架构无关 JS，`next start` 不需要 SWC。

## 3. 推荐改动面（约 14 个文件）

| 文件 | 改动 |
|---|---|
| `packages/prisma/schema.prisma` | 删除 `datasource.url`；generator 保持 `prisma-client-js` |
| `packages/prisma/package.json` | `prisma`/`@prisma/client` → `7.10.1`；加 `@prisma/adapter-pg@7.10.1`、`pg`；`prisma` CLI 移到 devDependencies |
| `packages/prisma/index.ts` | `new PrismaClient({ adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }), log })` |
| `packages/prisma/prisma.config.ts`（新） | `defineConfig({ schema, migrations: { path }, datasource: { url: env("DATABASE_URL") } })` |
| `apps/web/package.json` | 删除 `sharp`；`bcrypt` → `bcryptjs@^3.0.3`；可加 `dependenciesMeta.sharp.built=false` |
| 6 个 bcrypt 文件 | `import bcrypt from "bcryptjs"`（postUser、deleteUserById、updateUserById、verifyByCredentials、reset-password、[...nextauth]） |
| `apps/web/next.config.js` | `images.unoptimized: true`；建议 `serverExternalPackages: ["@prisma/client","@prisma/adapter-pg","pg"]` |
| `scripts/prisma-migrate.mjs`（新） | 顺序执行 migrations、checksum、advisory lock、失败回滚 |
| `Dockerfile` / entrypoint（新） | 去掉 `prisma migrate deploy`，改跑迁移器；`concurrently next start + tsx worker.ts`；装 lbrowser 依赖 |
| `.yarnrc.yml`（可选） | `packageExtensions` 放宽 `@auth/prisma-adapter` 的 `@prisma/client` peer 到 `>=7`（只影响 warning） |

不需要改：Playwright 调用、归档逻辑、Meilisearch 回退、worker 业务代码、Prisma 查询代码。

## 4. 构建与运行

### 4.1 x86_64 WSL2（Node 22.23.3）

```bash
corepack enable && corepack prepare yarn@4.12.0 --activate
git clone --depth 1 --branch v2.16.3 https://github.com/linkwarden/linkwarden.git
# 应用第 3 节补丁后
yarn install
DATABASE_URL=postgresql://build:build@127.0.0.1:5432/build yarn prisma:generate
yarn web:build
```

把 `apps/web/.next`、`apps/web/public`、`apps/web/next.config.js`、`apps/web/package.json`、`apps/worker`、`packages`、`yarn.lock`、`.yarnrc.yml`、迁移器放到构建上下文 `artifacts/`（大目录不入库）。

### 4.2 loong64 运行镜像

```dockerfile
FROM yunixintel/node:24.22.1
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH=/data/node_modules/.bin:$PATH
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates tzdata curl bash procps-ng \
    gtk2 gtk3 nss nspr cups-libs cairo gdk-pixbuf2 pango expat libxcb libxkbcommon \
    at-spi2-atk at-spi2-core libXcomposite libXdamage libXext libXfixes libXrandr \
    mesa-libgbm libffi kmod-libs alsa-lib pulseaudio-libs libatomic systemd-libs \
    pcre2 gnutls avahi-libs krb5-libs iproute binutils && dnf clean all
# 可选：COPY lbrowser/ /opt/apps/lbrowser/   （从 deb 解出，见 4.3）
COPY artifacts/ /data/
WORKDIR /data
RUN corepack enable && yarn workspaces focus --production \
      linkwarden @linkwarden/web @linkwarden/worker
# 用 x86 builder 生成结果覆盖运行时包（纯 JS/WASM）；artifacts 内为 @prisma/client 与 .prisma
COPY artifacts/prisma-client/ /data/node_modules/@prisma/client/
COPY artifacts/prisma-generated/ /data/node_modules/.prisma/
ENV STORAGE_FOLDER=data PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH=/opt/apps/lbrowser/lbrowser
EXPOSE 3000
ENTRYPOINT ["/data/scripts/entrypoint.sh"]
```

`entrypoint.sh`：等待 PostgreSQL → `node /data/scripts/prisma-migrate.mjs` → `concurrently -k -n web,worker "cd /data/apps/web && exec next start" "cd /data/apps/worker && exec npx tsx worker.ts"`。`STORAGE_FOLDER=data` 配合各进程 `cwd/../..` 正好落到 `/data/data`。

### 4.3 Monolith 与 LBrowser

```bash
# monolith：Rust 1.85 即可，2026-10 实测 10m55s，产物 12MB，最高只要求 GLIBC_2.38
cargo install --locked monolith@2.10.1 --root /tmp/mono
cp /tmp/mono/bin/monolith /usr/local/bin/

# lbrowser：100MB deb，解出 data.tar.xz 得 /opt/apps/lbrowser
curl -fLO https://pkg.loongnix.cn/loongnix/25/pool/main/l/lbrowser/lbrowser_3.4.2293.2-1.stable_loong64.deb
ar x lbrowser_*.deb && tar xf data.tar.xz -C /opt
```

## 5. 最小 compose（无 Meilisearch）

```yaml
services:
  postgres:
    image: yunixintel/postgres:loong64
    environment: { POSTGRES_USER: linkwarden, POSTGRES_PASSWORD: change-me, POSTGRES_DB: linkwarden }
    volumes: [pgdata:/var/lib/postgresql/data]
  linkwarden:
    image: yunixintel/linkwarden:loong64
    depends_on: [postgres]
    ports: ["3000:3000"]
    env_file: .env
    environment:
      DATABASE_URL: postgresql://linkwarden:change-me@postgres:5432/linkwarden
      NEXTAUTH_URL: http://<host>:3000/api/v1/auth
      NEXTAUTH_SECRET: <openssl rand -base64 32>
      STORAGE_FOLDER: data
      PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH: /opt/apps/lbrowser/lbrowser
      # DISABLE_BROWSER: "true" | PLAYWRIGHT_WS_URL: ws://<x86>:3000?token=...
    volumes: ["./data:/data/data"]
    # 不在镜像内放浏览器：- /opt/apps/lbrowser:/opt/apps/lbrowser:ro
volumes: { pgdata: {} }
```

## 6. 验证步骤

1. `docker inspect` 架构为 `loong64`；`/` 返回 200。
2. 首启日志出现 `MIGRATIONS_OK`；`select count(*) from "_prisma_migrations"` = 99；重启后不重复执行。
3. 注册/登录；建集合、标签、书签；检查 `Link`/`Collection`/`Tag` 行；删除用户验证级联。
4. 添加 `https://example.com`，等 worker：`/data/data/archives/<cid>/<id>.jpeg/.pdf/.html` 与 preview 生成；Readability 视图可打开。
5. 设 `DISABLE_BROWSER=true` 重启：新书签仍可建，归档字段为 `unavailable`，确认降级符合预期。
6. 设 `PLAYWRIGHT_WS_URL` 指向外部 browserless，重复第 4 步。
7. 搜索（无 Meilisearch）按名称/URL/描述/标签命中；导入 HTML/Pocket/Wallabag 各一条。
8. `docker restart` 后数据与归档仍在。

## 7. 功能降级清单

| 条件 | 可用 | 不可用/降级 |
|---|---|---|
| 无浏览器 | 书签/集合/标签/搜索/导入导出/RSS/API/登录 | 截图、PDF、Readability、Monolith、OG 预览、归档期 AI 打标；字段显示 `unavailable` |
| 无 Meilisearch | SQL `contains` 搜索 | 拼写容错、相关性排序、大规模性能；索引 worker 不启动 |
| 无 sharp | 所有业务功能、图片原图直出 | Next 图片优化（`/_next/image` 多尺寸），流量增大 |
| 无 Monolith 二进制 | 截图/PDF/Readability | Monolith 单格式归档失败（仅日志，不影响其他格式） |
| 无 bcrypt 原生 | 登录/改密（bcryptjs 兼容哈希） | 哈希耗时略高 |
| 无 Prisma CLI | 运行时查询/迁移器 | Studio、`migrate dev`、`migrate deploy`；开发在 x86 做 |

## 8. 工作量与风险

| 项 | 估算 |
|---|---|
| Prisma 7 + adapter + 类型/构建修复 | 2–3 天 |
| x86 Next 构建 + loong64 运行时依赖 | 1–1.5 天 |
| LBrowser/Monolith 镜像与归档回归 | 1–1.5 天 |
| E2E、降级、文档、双 tag | 1–1.5 天 |
| **合计** | **5–7 天**（不含浏览器则 4–5 天） |

主要风险：

- **Prisma 7 旧 generator 在 v8 移除**：pin 7.10.1；后续再评估迁移到 `prisma-client` 新 generator。
- **`@auth/prisma-adapter` peer 只写到 `>=6`**：运行时和类型在 v7 下可用（生成文件仍在 `@prisma/client`），但 build 时要确认 TypeScript 不报错；必要时加 `packageExtensions` 或一处 `as any`。
- **Next 构建/运行分离**：首次 `yarn web:build` 必须确认 Prisma 7 + Next 15 的 server bundle；加 `serverExternalPackages`，并跑一次真实 `next start`。
- **LBrowser 许可与体积**：再分发前确认许可；否则用宿主挂载或外部 browserless。镜像含浏览器约 +370MB。
- **Chromium 138 vs Playwright 1.57（143）**：已覆盖 Linkwarden 用到的 API，复杂站点仍需抽样回归。
- **自写迁移器**：已用 99 个真实迁移和幂等重跑验证；后续上游新增迁移需保持 `_prisma_migrations` 格式和 checksum 兼容。

**Go/No-Go**：默认 **Go**。若要求“完全不改上游代码/必须用官方镜像”，或“必须首发内置归档但不允许再分发 LBrowser”，则对应范围 **No-Go**；前者无现实路径，后者可退化为 `DISABLE_BROWSER=true` 的基础版。
