# Karakeep 0.34.1 (loong64) 基础版构建记录

## 结论

- 镜像：`yunixintel/karakeep:loong64` / `:0.34.1`
- Registry digest（两 tag 相同）：
  `sha256:261827ead66bc1b6b64d61c54dc97eab99d5acf94e921a40fcfb3a448160f445`
- 架构：`linux/loong64`
- 本地大小：1,453,038,638 B（1.45 GB）；Hub 压缩后 492,798,375 B（470.0 MiB）
- 镜像 ID：`sha256:a8970acd868f83137f970b8e039c478d6531effd234541bf1f44657dbbb590cb`
- 版本：Karakeep `v0.34.1`（commit `ebd122bb45b38d9dd45f7c6db55b5587bf6b1265`）、
  Node.js 24.22.1、Next.js 16.4.1、better-sqlite3 13.0.3、sharp 0.35.5、
  libvips 8.18.7（复用 `yunixintel/node-sharp:24.22.1`）
- 范围：SQLite 单容器 Web + Workers，默认不内置 Chromium；静态抓取、
  正文归档、banner 原图/WebP、标签/列表/笔记可用；AI 打标需外部模型，未实测。
- 实测：健康检查、首次注册（首个用户为 admin）/登录、example.com 静态抓取、
  Wikipedia banner 转 WebP、Next 图片优化、重启持久化、SQLite、原生模块架构、
  LBrowser sidecar 截图/PDF 全部通过。

## 上游与产物

上游 pin：`karakeep-app/karakeep` `v0.34.1`，
commit `ebd122bb45b38d9dd45f7c6db55b5587bf6b1265`（2026-10-22）。

前端与 workers 在 x86_64 WSL2（Ubuntu 26.04，32 核）用 Node 24.22.1 +
pnpm 11.2.1 构建；loong64 只做原生模块重编译和镜像组装。

构建上下文 `images/karakeep/artifacts/` 的布局（**不提交仓库**）：

```text
artifacts/
  web/             Next standalone（188 MB）
  workers/         pnpm deploy 产物（588 MB）
  db_migrations/   ncc 迁移器 + drizzle（12 MB）
```

### x86_64 构建命令

```bash
export PATH=$HOME/node24/bin:$PATH
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 NEXT_TELEMETRY_DISABLED=1
git clone --depth 1 --branch v0.34.1 https://github.com/karakeep-app/karakeep.git
cd karakeep
corepack prepare pnpm@11.2.1 --activate
pnpm install --frozen-lockfile

# 1) Next standalone。必须 --webpack；full build 的 page-data 阶段会读取
#    NEXTAUTH_SECRET，所以给一个构建期占位值（运行时由 entrypoint 另行生成）。
cd apps/web
NEXTAUTH_SECRET=build-time-placeholder-0000000000000000 \
DATA_DIR=/tmp/karakeep-build-data \
  pnpm exec next build --webpack
cd ../..

# 2) workers + 生产依赖
pnpm --filter @karakeep/workers build
CI=true pnpm deploy --node-linker=isolated --legacy \
  --filter @karakeep/workers --prod /out/workers

# 3) DB 迁移器。关键：--external better-sqlite3。默认 ncc 会把构建机上
#    x86 的 .node 绝对路径和 x64 prebuilds 打进 index.js。
cd packages/db
CI=true pnpm --config.verify-deps-before-run=false \
  exec ncc build migrate.ts -o /out/db_migrations --external better-sqlite3
cp -R drizzle /out/db_migrations/drizzle

# 4) standalone 补 public/static
mkdir -p /out/web
cp -a apps/web/.next/standalone/. /out/web/
mkdir -p /out/web/apps/web/.next
cp -a apps/web/.next/static /out/web/apps/web/.next/static
cp -a apps/web/public /out/web/apps/web/public
```

`next.config.mjs` 未设置 `images.unoptimized`；Next 图片优化保持开启，运行时
由复用的 sharp 处理（已实测返回 WebP）。

## loong64 原生阶段

`Dockerfile` 两阶段，均基于 `yunixintel/node-sharp:24.22.1`（openEuler 24.03 /
glibc 2.38 / Node 24.22.1 / libvips 8.18.7 / sharp 0.35.5）。

1. `native` 阶段安装 `gcc-c++ make python3 shadow util-linux findutils file`，
   `npm i -g node-gyp@12.4.0`，`npm_config_nodedir=/opt/node24`。
2. 对 `artifacts/**/node_modules/better-sqlite3` 的每个副本执行：

   ```bash
   node-gyp rebuild --force_build=1
   ```

   - `--force_build=1` 必需：npm 包自带 x64/arm64 `prebuilds/`，否则
     `binding.gyp` 会跳过编译。
   - 编译后删除 `prebuilds/ deps/ src/ binding.gyp node_modules/` 和中间对象，
     只保留 `lib/` 与 `build/Release/better_sqlite3.node`。
   - `db_migrations` 通过 `--external better-sqlite3` 解析到
     `/app/node_modules/better-sqlite3`，不重复打包。
3. sharp 复用 node-sharp 的预编译产物（BASE-IMAGES 的“方式 C”）：
   把 `/opt/node_modules/sharp/src/build/Release/sharp-linux-loong64-0.35.5.node`
   复制进应用内每个 `sharp/src/build/Release/`。运行时由
   `SHARP_FORCE_GLOBAL_LIBVIPS=1` + `LD_LIBRARY_PATH=/opt/vips/lib` 使用全局 libvips。
4. 删除 x86_64 遗留的 `.node`：`better-sqlite3/prebuilds/*`、
   `@img/sharp-linux-x64/*`、`@swc/*`、`re2/build/Release/*`。
   `find /app -name '*.node' -exec file {}` 的 6 个文件全部为
   `ELF 64-bit LSB shared object, LoongArch`。

## 运行镜像

- 端口 3000；卷 `/data`；UID/GID `1116`；健康检查 `/api/health`。
- 运行库：`ca-certificates tzdata curl shadow util-linux findutils file
  GraphicsMagick ghostscript`。
- entrypoint（`/bin/bash`，root 启动）：
  - 校验必填 `NEXTAUTH_URL`，缺失时退出码 1；
  - 建 `/data/assets` 并 chown 1116；
  - `NEXTAUTH_SECRET`：环境变量优先；否则读 `/data/.nextauth_secret`；
    首次用 `head -c 48 /dev/urandom | base64` 生成并以 0600 持久化。
    显式传环境变量时不写文件，后续重启需继续传入同一个值。
  - 以 1116 运行 `/app/db_migrations/index.js`；
  - 以 1116 启动 `/app/apps/web/server.js` 与 `/app/apps/workers/dist/index.js`；
  - `trap TERM/INT` + `wait -n`，任一进程退出即停止另一个；不用 s6。
- 默认 `DB_WAL_MODE=true`、`DATA_DIR=/data`、`ASSETS_DIR=/data/assets`、
  `HOME=/data`。
- 无浏览器时 crawler 自动进入 `Running in browserless mode`，走普通 HTTP +
  readability，不产生截图/PDF；搜索在未配 `MEILI_ADDR` 时关闭。

### 首次使用

```bash
docker run -d --name karakeep -p 3000:3000 \
  -v karakeep-data:/data \
  -e NEXTAUTH_URL=http://<host>:3000 \
  yunixintel/karakeep:loong64
```

首个注册用户自动成为 admin。创建完成后建议设置 `DISABLE_SIGNUPS=true`。
`NEXTAUTH_SECRET` 不需要手工提供，会生成到 `/data/.nextauth_secret`；
如需接管可显式传 `-e NEXTAUTH_SECRET=...`。

## LBrowser sidecar（可选，不内置、不推送）

LBrowser 的许可证不清晰，**禁止再分发**；本镜像不含浏览器字节。需要 JS 渲染、
截图、PDF 时，在宿主挂载 `/opt/apps/lbrowser` 并以 sidecar 运行：

```yaml
services:
  karakeep:
    image: yunixintel/karakeep:loong64
    ports: ["3000:3000"]
    volumes: ["./data:/data"]
    environment:
      NEXTAUTH_URL: http://<host>:3000
      BROWSER_WEB_URL: http://chrome:9222
      CRAWLER_HEADLESS_BROWSER: "true"
      CRAWLER_STORE_PDF: "true"     # 默认 false；需要 PDF 时打开
  chrome:
    image: local/lbrowser-runtime:3.4.2293.2
    command: ["serve"]
    shm_size: "1g"
    volumes:
      - /opt/apps/lbrowser:/opt/apps/lbrowser:ro
```

- 必须 `--shm-size=1g`（至少 512 MB）。
- Karakeep 用 Patchright `connectOverCDP` 连接 `BROWSER_WEB_URL`，写
  `http://chrome:9222`；不要用 `BROWSER_WEBSOCKET_URL`（那是 Playwright server 协议）。
- LBrowser DevTools 只监听 127.0.0.1，`serve` 内的 `cdp-proxy.mjs` 负责跨容器
  监听 9222 并改写 `/json/*` 的 WebSocket 地址。
- 本镜像**不推送** LBrowser；`local/lbrowser-runtime:3.4.2293.2` 只在本机构建。

## 测试结果（Host A / 3A6000，实际执行）

测试容器：`-p 13000:3000`、`-v karakeep-test-data:/data`、
`NEXTAUTH_URL=http://127.0.0.1:13000`。

| 项 | 结果 |
|---|---|
| `/api/health` | 200 `{"status":"ok","message":"Web app is working"}`；Docker health = `healthy` |
| 首次注册 | 200；首个用户 `role=admin`；会话 cookie 正常 |
| 登录 | 200，返回同一用户 |
| 静态抓取 `https://example.com` | `crawlStatus=success`；标题 `Example Domain`；正文 HTML 已归档 |
| Wikipedia banner | 抓取成功；`bannerImage` 资产落盘为 **WebP**（10,158 B，原图为 PNG） |
| Next 图片优化 | `/_next/image?...&w=256&q=75` + `Accept: image/webp` → 200、`image/webp`、1,724 B、256×256 |
| 重启持久化 | 重启后 secret SHA-256 不变；2 个书签、标题/正文/banner 资产仍在 |
| SQLite | `user=1`、`bookmarks=2`、`assets=2`；`user/bookmarks/assets/session/account` 等表可查 |
| 原生模块 | 容器内 6 个 `.node`，6 个 `file` 结果均为 LoongArch |
| 原生模块加载 | web/workers 两个 better-sqlite3 副本均输出 SQLite 3.53.4；两个 sharp 副本均输出 libvips 8.18.7 / sharp 0.35.5 |
| 进程用户 | `next-server` 与 `node dist/index.js` 均以 UID/GID 1116 运行；entrypoint 为 root |
| 必填参数 | 未传 `NEXTAUTH_URL` 时 entrypoint 报错并退出码 1 |
| 显式 `NEXTAUTH_SECRET` | 全新卷 + 环境变量启动，health 200，不生成 `/data/.nextauth_secret` |
| 最终镜像复测 | `a8970acd868f`（digest `261827…`）重新注册/建 key/抓 example.com 成功；6 个 `.node` 全部 LoongArch |
| 优雅停止 | `docker stop` → exit 0，日志出现 `[entrypoint] Stopping web and workers` |
| LBrowser 截图 | sidecar 接入后 `Captured the screenshot`；JPEG 1440×900，65,594 B |
| LBrowser PDF | 同一次抓取 `Captured the PDF`；PDF 1.4，1 页，92,459 B |

## 补充验证（2026-10-25 独立复验）

- 默认 `CRAWLER_STORE_PDF=false`；设置 `CRAWLER_STORE_PDF=true` 后，Wikipedia 页面 PDF 落盘 **649,933 B**，截图 211,990 B，HTML 277,148 B。
- 未设该变量时日志为 `Skipping storing the PDF as it's empty`，这是默认关闭，不是失败。
- 真实 LBrowser sidecar 截图验证：example.org 65,594 B；Wikipedia 截图 215,523 B。

## 未验证

- **全文/语义搜索**：未配 Meilisearch，搜索关闭（上游 0.34.1 只支持 SQLite，
  没有 FTS 回退）。
- **全页单文件归档**：未构建 monolith，`CRAWLER_FULL_PAGE_ARCHIVE` 保持 false。
- **视频下载**：未安装 yt-dlp/ffmpeg。
- **OCR / PDF 文本提取 / PDF 首页截图**：已装 tesseract.js（WASM）、pdf2json、
  GraphicsMagick + Ghostscript，但未跑上传 PDF 的完整链路。
- **AI 打标/摘要**：未配置 OpenAI 兼容或 Ollama 端点。
- **S3/Redis/Restate**：保持默认文件系统 / liteque / 内存限流。
- **多用户、邀请、邮件验证、OAuth**：未逐项验证。
- **外部 Meilisearch / browserless WebSocket 模式**：未验证。
- **非 root、只读根文件系统、SELinux/AppArmor、rootless Docker**：未验证。
- **LBrowser 的 WebGL/视频/DRM/GPU**：未验证。

## 体积

```text
docker images yunixintel/karakeep
yunixintel/karakeep  loong64  a8970acd868f  1.45GB
yunixintel/karakeep  0.34.1   a8970acd868f  1.45GB
```

本地 1,453,038,638 B；Hub manifest 14 层，压缩后合计 492,798,375 B
（470.0 MiB）。主要组成：openEuler + Node + libvips 基础层约 446 MB，
Web/Workers/db_migrations 约 790 MB（未压缩），GraphicsMagick/Ghostscript
及运行库约 100 MB。

## 复现

```bash
cd images/karakeep
# 先按上文在 x86_64 上生成 artifacts/{web,workers,db_migrations}
./build.sh
# 等价于：
DOCKER_BUILDKIT=0 docker build --network=host \
  -t yunixintel/karakeep:loong64 -t yunixintel/karakeep:0.34.1 .
```

推送（`crane` + 本地代理）：

```bash
docker save -o karakeep.tar yunixintel/karakeep:loong64
export HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=http://127.0.0.1:17890
/build/bin/crane push karakeep.tar yunixintel/karakeep:loong64
/build/bin/crane push karakeep.tar yunixintel/karakeep:0.34.1
/build/bin/crane digest yunixintel/karakeep:loong64
# sha256:261827ead66bc1b6b64d61c54dc97eab99d5acf94e921a40fcfb3a448160f445
```

## 文件

- `Dockerfile`：native + 运行两阶段；better-sqlite3 重编译、sharp 复用、清理 x64 `.node`
- `entrypoint.sh`：必填校验、secret 持久化、迁移、Web + Workers、`wait -n`/trap
- `build.sh`：`DOCKER_BUILDKIT=0 docker build --network=host`
- `artifacts/`：构建上下文（由 x86_64 生成，不提交仓库）
