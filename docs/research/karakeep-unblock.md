# Karakeep loong64 移植可行性报告
日期：2026-10-24。目标：龙芯 3A6000 / Loongnix 25 宿主，openEuler 24.03 / glibc 2.38 / 16K 页构建容器。
## 0. 结论

**Go（有条件）**：可以发布 `yunixintel/karakeep:loong64` 的“基础版”，用 SQLite 单容器跑 Web + Workers，静态网页抓取、正文归档、标签/列表/笔记、AI 打标、图片/PDF 处理可用。但**必须放弃**内置 Chromium、内置 Meilisearch、原生 `sharp` 作为首发门槛；三者都不阻塞主流程，其中 `sharp` 只影响 banner WebP 压缩。

关键纠正：Karakeep 0.34 的网页正文归档**不依赖 Chromium**。Chromium 只用于 JS 渲染、截图、PDF 和反爬；无浏览器时官方明确降级为普通 HTTP 抓取（`BROWSER_WEB_URL`/`BROWSER_WEBSOCKET_URL` 都不设即可）。`sharp` 只用于 `bannerImages.ts` 的 banner 转 WebP，失败会回退原图；不是缩略图管线。

版本锁定：Karakeep `v0.34.1`，commit `ebd122bb45b38d9dd45f7c6db55b5587bf6b1265`（2026-10-22）；Node 24.22.1；pnpm 11.2.1；Next 16.4.1；better-sqlite3 13.0.3；patchright 1.59.4；sharp 0.35.5。
## 1. 上游结构

| 组件 | 事实 |
|---|---|
| `apps/web` | Next.js 16.4.1，`output: standalone`，提供 UI、tRPC/API、better-auth 登录 |
| `apps/workers` | Node/TypeScript，tsdown 打包；crawler、inference、search、assetPreprocessing、feed、backup、webhook、ruleEngine 等 worker |
| `packages/db` | Drizzle ORM + `better-sqlite3 13.0.3`；数据库固定 `${DATA_DIR}/db.db`，**0.34.1 只支持 SQLite，不支持 PostgreSQL** |
| `packages/plugins` | 文件系统/S3 资产、liteque/restate 队列、Meilisearch 搜索/向量、memory/Redis 限流；默认 liteque，单机不需要 Redis |
| 浏览器 | `patchright 1.59.4`（Playwright 分支），通过 CDP 连 Chrome；官方 Chrome 镜像为 Debian Chromium/Google Chrome |
| 搜索 | `MEILI_ADDR` 未设置时**搜索完全关闭**，没有 SQLite FTS 或 LIKE 回退；搜索页仍会显示，查询会报 “Search functionality is not configured” |
| AI | OpenAI 兼容接口或 Ollama；默认文本模型 `gpt-6-luna`，自定义网关需改 `INFERENCE_TEXT_MODEL` |
| 其他 | monolith 用于全页归档（对已抓取 HTML 运行，不是浏览器）；yt-dlp 可选；PDF 截图用 GraphicsMagick + Ghostscript；OCR 用 tesseract.js |

上游 Dockerfile 用 `node:24-slim` + s6-overlay 3.2.1.0，s6 只发布 x86_64/aarch64/riscv64 等资产，**没有 loong64**，必须改自管 entrypoint。

## 2. 阻塞项逐项判定

### 2.1 sharp / libvips

- `sharp 0.35.5` 的 optionalDependencies 只有 linux-x64/arm/arm64/ppc64/riscv64/s390x 等，**没有 linux-loong64**；`@img/sharp-libvips` 同样没有。
- `sharp 0.35.5` 的 `src/common.h` 硬性要求 **libvips >= 8.18.7**；Loongnix 25 仓库只有 `libvips-dev 8.16.1`，openEuler 24.03 连 `vips-devel` 都没有。直接拿系统 libvips 编译会失败。
- 可行路径：在 openEuler 24.03 内源码构建 libvips 8.18.7（2026-09-26 发布），再用 `SHARP_FORCE_GLOBAL_LIBVIPS=1` 源码编译 sharp。openEuler 有 glib2/expat/jpeg/png/webp/tiff/lcms2/libexif/zlib 的 devel 包；没有 libheif/cgif，关掉即可。以下是可执行命令：

```bash
# openEuler 24.03 builder
dnf install -y --setopt=install_weak_deps=False gcc-c++ make python3 \
  meson ninja-build pkgconf-pkg-config glib2-devel expat-devel \
  libjpeg-turbo-devel libpng-devel libwebp-devel libtiff-devel \
  libexif-devel lcms2-devel zlib-devel
curl -fsSLO https://github.com/libvips/libvips/releases/download/v8.18.7/vips-8.18.7.tar.xz
tar xf vips-8.18.7.tar.xz && cd vips-8.18.7
meson setup build --prefix=/opt/vips --libdir=lib --buildtype=release \
  -Dauto_features=disabled -Dmodules=disabled -Dintrospection=disabled \
  -Dexamples=false -Ddocs=false -Dcplusplus=true \
  -Djpeg=enabled -Dpng=enabled -Dwebp=enabled -Dtiff=enabled \
  -Dexif=enabled -Dlcms=enabled -Dzlib=enabled
ninja -C build && ninja -C build install
PKG_CONFIG_PATH=/opt/vips/lib/pkgconfig pkg-config --modversion vips-cpp   # 8.18.7
```
```bash
# 在运行产物的 node_modules/sharp 内（需要 Node 24 头文件）
npm install --no-save --no-package-lock --ignore-scripts node-addon-api@8.9.2
npm_config_nodedir=/opt/node24 \
PKG_CONFIG_PATH=/opt/vips/lib/pkgconfig \
LD_LIBRARY_PATH=/opt/vips/lib \
SHARP_FORCE_GLOBAL_LIBVIPS=1 \
npx --yes node-gyp@12.4.0 rebuild --directory=src
# 产物：src/build/Release/sharp-linux-loong64-0.35.5.node
node -e "const s=require('sharp'); console.log(s.versions.vips); s({create:{width:8,height:8,channels:3,background:'red'}}).webp().toBuffer().then(b=>console.log(b.length))"
```

**建议**：首发不把 sharp 作为门槛。没有 sharp 时保留原始 JPEG/PNG banner，功能正常；若要控制存储再启用上述构建，预计增加 80–120MB 镜像和 1–2 天验证。

### 2.2 Chromium / Playwright

- Loongnix 25 的 apt 仓库没有 `chromium`/`chromium-browser`（只有 Firefox ESR）；openEuler 24.03 也没有 Chromium 包。Playwright 官方不发布 linux-loong64 浏览器。
- AOSC 有社区维护的 [chromium-loongarch64](https://github.com/AOSC-Dev/chromium-loongarch64)，已 rebase 到 Chromium 148.0.7778.280；AOSC 仓库有 `chromium_148.0.7778.180-1_loongarch64.deb`（约 171MB）。但 AOSC 当前 glibc 2.44，本仓库运行镜像是 2.38、宿主是 2.41，**不能直接复用该二进制**；AOSC 的构建要求写的是 `core=32`，本机 8 核、根分区仅剩约 13GB，原生编译 Chromium 不现实。
- 可行方案：外部 browserless / Playwright server，设置 `BROWSER_WEBSOCKET_URL=ws://<x86-host>:3000?token=...`，`BROWSER_CONNECT_ONDEMAND=true`。外部浏览器负责 JS 渲染、截图、PDF；Karakeep 侧无需改代码。代价是必须有一台 x86/ARM 机器或 browserless 云服务，且目标站点要能被那台机器访问。
- 无浏览器时：静态 HTML 抓取、metascraper/readability 正文、banner 下载、文本归档正常；JS 站点、Cloudflare/DataDome、截图、PDF 不可用。建议默认 `CRAWLER_STORE_SCREENSHOT=false`、`CRAWLER_STORE_PDF=false`，避免 UI 显示空截图。

**结论**：原生 Chromium 在 3A6000 上 No-Go；外部 browserless 是唯一现实的全功能路径；无浏览器的基础版可以首发。

### 2.3 Meilisearch

- 官方 release 只有 linux-amd64/aarch64/riscv64（v1.41.0 和最新 v1.55.0 均无 loong64），没有 loong64 镜像资产。
- 上游 compose 固定 `getmeili/meilisearch:v1.41.0`。源码是 Rust 1.98.1，理论上可编，但涉及 LMDB、jemalloc、rustls/ring 等架构相关依赖，loong64 没有官方验证；按 2–4 天 spike 估算，失败风险不低。
- 零代码方案：在 x86/ARM 机器上跑 Meilisearch v1.41.0，Karakeep 设 `MEILI_ADDR=http://<host>:7700`、`MEILI_MASTER_KEY=...`。外部搜索索引和向量检索都可用。
- 纯 loong64 降级：搜索关闭。若必须本地搜索，需要自写 `PluginType.Search` 的 SQLite FTS5 provider（better-sqlite3 确实编译了 `SQLITE_ENABLE_FTS5`），但要补索引表、过滤/排序、中文分词和重建逻辑，约 5–7 天，不建议放进首发。
- PostgreSQL 全文检索不可行：0.34.1 的 db 层只有 better-sqlite3，没有 pg 驱动或迁移路径，换库等于 fork。

### 2.4 其他依赖

- `better-sqlite3 13.0.3` 没有 install script，npm 包只带 x64/arm64 prebuild；loong64 必须手动 `node-gyp rebuild`。本仓库 Actual Budget/Homarr 已有成功先例。它自带 SQLite 源码并启用 FTS5。
- `re2` 是 `url-regex-safe` 的 optional peer，加载失败会自动退回 JS RegExp；x64 的 `re2` 留在产物里不会致命，建议删除以避免混淆。
- `tesseract.js`、`pdf2json` 是 WASM/纯 JS；`pdf2pic` 需要 GraphicsMagick + Ghostscript，openEuler 两者都有。OCR/PDF 截图建议做一次真机验证，不作为阻塞。
- monolith 是 Rust 2.11.6，可尝试用 Rust 1.99.1 编 loong64；它使用 rustls/ring，需先验证。若编不出，保持 `CRAWLER_FULL_PAGE_ARCHIVE=false`，正文归档仍可用。
- s6-overlay 无 loong64 资产，不要照搬上游 aio 镜像；用 shell entrypoint 管两个进程。

## 3. 推荐构建方案

### 3.1 x86 前端/打包产物（WSL2 或 x86 构建机）

```bash
export PATH=$HOME/node24/bin:$PATH
corepack enable && corepack prepare pnpm@11.2.1 --activate
git clone --depth 1 --branch v0.34.1 https://github.com/karakeep-app/karakeep.git
cd karakeep && pnpm install --frozen-lockfile
cd apps/web && pnpm exec next build --webpack && cd ../..
pnpm --filter @karakeep/workers build
pnpm deploy --node-linker=isolated --legacy --filter @karakeep/workers --prod /out/workers
cd packages/db && pnpm exec ncc build migrate.ts -o /out/db_migrations && cp -R drizzle /out/db_migrations && cd ../..
cp -a apps/web/.next/standalone /out/web
cp -a apps/web/.next/static /out/web/apps/web/.next/static
cp -a apps/web/public /out/web/apps/web/public
```

前端用 `--webpack` 是为了避开 Next 16 默认 Turbopack 的 loong64 binding 问题；x86 上也可用原生 SWC。若改在 loong64 上直接 build，Next 会自动下载 `@next/swc-wasm-nodejs@16.4.1`，但构建明显更慢。

没有 sharp 时，在 `apps/web/next.config.mjs` 增加 `images: { unoptimized: true }`，否则 `/blur.avif` 的 `/_next/image` 请求会因缺 sharp 返回 500。

### 3.2 loong64 原生阶段与运行镜像（Dockerfile 骨架）

```dockerfile
# 说明：/out 由 3.1 在 x86 上生成，作为构建上下文 artifacts/
FROM openeuler/openeuler:24.03 AS native
RUN dnf install -y --setopt=install_weak_deps=False gcc-c++ make python3 \
    ca-certificates shadow util-linux && dnf clean all
COPY --from=yunixintel/node:24.22.1 /opt/node24 /opt/node24
ENV PATH=/opt/node24/bin:$PATH npm_config_nodedir=/opt/node24
COPY artifacts/ /artifacts/
RUN npm i -g node-gyp@12.4.0 && \
    find /artifacts -type d -name better-sqlite3 -path '*/node_modules/*' -print0 \
      | xargs -0 -I{} sh -c 'cd "{}" && node-gyp rebuild'

FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates tzdata curl \
    shadow util-linux libjpeg-turbo libpng libwebp libtiff lcms2 libexif glib2 expat \
    GraphicsMagick ghostscript && dnf clean all && \
    groupadd -g 1116 karakeep && useradd -u 1116 -g 1116 -M -d /data -s /sbin/nologin karakeep
COPY --from=yunixintel/node:24.22.1 /opt/node24 /opt/node24
COPY artifacts/web /app
COPY artifacts/workers /app/apps/workers
COPY artifacts/db_migrations /app/db_migrations
COPY entrypoint.sh /entrypoint.sh
ENV PATH=/opt/node24/bin:$PATH NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000 \
    DATA_DIR=/data NEXT_TELEMETRY_DISABLED=1 SERVER_VERSION=0.34.1
RUN chmod +x /entrypoint.sh && mkdir -p /data/assets && chown -R 1116:1116 /data
VOLUME ["/data"]
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fsS http://127.0.0.1:3000/api/health || exit 1
ENTRYPOINT ["/entrypoint.sh"]
```

若启用 sharp，在 `native` 阶段按 2.1 构建 libvips，再编译 sharp，运行镜像 `COPY --from=native /opt/vips /opt/vips`，并设 `LD_LIBRARY_PATH=/opt/vips/lib`。

### 3.3 entrypoint 要点

- 以 root 启动，只 `chown -R 1116:1116 /data`；生成 `NEXTAUTH_SECRET` 到 `/data/.nextauth_secret`（0600）并持久化。
- 先以 UID 1116 运行 `NODE_PATH=/app/node_modules node /app/db_migrations/index.js`；再分别启动 `apps/web/server.js` 与 `apps/workers/dist/index.js`。
- 用 `trap 'kill -TERM ...; wait' TERM INT` + `wait -n` 管理两个子进程，不做 s6。
- 必填 `NEXTAUTH_URL`（外部可访问地址）；首次启动保持 `DISABLE_SIGNUPS=false` 创建首个 admin，随后改 `true`；建议 `DB_WAL_MODE=true`、`LOG_LEVEL=info`。

## 4. 功能清单

| 功能 | 首发 | 说明 |
|---|---|---|
| 注册/登录/首用户 admin、API key、多用户 | 可用 | better-auth；`NEXTAUTH_*` 必填 |
| 书签/文本/图片/PDF 上传、标签、列表、笔记、高亮 | 可用 | SQLite + 本地资产 |
| 静态网页抓取、标题/正文/元数据、banner 原图 | 可用 | 无浏览器，普通 HTTP + readability |
| 网页正文归档（文本） | 可用 | 默认行为 |
| 全页单文件归档 | 条件可用 | 需 monolith loong64；否则保持关闭 |
| 截图、PDF 快照、JS 渲染页面、反爬站点 | 缺失 | 需外部 browserless |
| 全文搜索、语义搜索 | 缺失 | 需外部 Meilisearch；无 SQLite 回退 |
| AI 自动标签/摘要 | 可用 | 外部 OpenAI 兼容/Ollama |
| 图片 OCR、PDF 文本/首页截图 | 可用（需验证） | tesseract.js / pdf2json / GM+Ghostscript |
| 视频保存（yt-dlp） | 缺失 | 首发不装 Python/yt-dlp |
| S3 资产存储、Redis 限流、Restate 队列 | 可选 | 默认文件系统/liteque/memory |
| CLI/MCP/移动端 | 不随镜像 | 上游独立产物；Web/API 不受影响 |

## 5. 验证步骤

```bash
docker build -t yunixintel/karakeep:loong64 .
docker inspect yunixintel/karakeep:loong64 --format '{{.Architecture}} {{.Os}}'
docker run -d --name karakeep -p 3000:3000 -v karakeep-data:/data \
  -e NEXTAUTH_URL=http://<host>:3000 -e NEXTAUTH_SECRET=$(head -c 36 /dev/urandom | base64) \
  yunixintel/karakeep:loong64
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/api/health
docker exec karakeep node -e "const D=require('better-sqlite3');const d=new D('/data/db.db');console.log(d.prepare('select count(*) from user').get())"
docker exec karakeep find /app -name '*.node' -exec file {} \;
```

人工验证：首个账号成为 admin；添加 `https://example.com` 后抓取成功、标题/正文出现；上传 JPEG/PDF 后 OCR/截图任务不崩；创建列表/标签/笔记；重启容器后数据仍在；不配 Meili 时搜索页报错与文档一致；配外部 `BROWSER_WEBSOCKET_URL` 后截图出现。若构建了 sharp，再执行 2.1 的 `sharp` 自检。

## 6. 风险与工作量

| 项 | 判断 |
|---|---|
| x86 Next standalone 内含 x64 better-sqlite3 | 高风险但可控：所有副本必须 `node-gyp rebuild`，用 `file` 检查无 x86 `.node` |
| sharp 源码构建 | 中风险，可选；libvips 8.18.7 必须自编，失败则回退原图 |
| 外部 browserless | 依赖另一台机器；JS/截图恢复，但网络延迟和可达性要测 |
| 外部 Meilisearch | 依赖另一台机器；不配则搜索完全不可用 |
| 原生 Meilisearch | 不建议首发；无官方 loong64，Rust/ring/jemalloc 风险高，2–4 天 spike |
| 原生 Chromium | No-Go：无 openEuler/Loongnix 包，AOSC 二进制 glibc 2.44，构建需 32 核和 100GB+ 磁盘 |
| s6-overlay | 已规避，改 shell entrypoint |
| monolith | 可选 spike；失败则关闭全页归档 |
| 镜像体积 | 基础版约 1.0–1.4GB；加 libvips/sharp 约 +0.1GB；不含 Chromium/Meili |
| 工作量 | 基础版 4–5 天；加 sharp 2 天；外部 sidecar compose/文档 1 天；全功能本地化另计 |

**最终建议**：按“Karakeep 基础版（SQLite + 静态抓取）”立项并发布，商店描述明确“搜索/截图/JS 页面需外部 Meilisearch/browserless”；sharp 作为第二阶段可选增强。若产品要求单机 LoongArch 开箱即得全文搜索 + 浏览器级归档，则当前应判 **No-Go**，不要做“能拉但核心功能不可用”的假覆盖。
