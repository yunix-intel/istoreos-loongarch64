# Karakeep 0.34.1 loong64 功能验证报告

日期：2026-10-25。环境：Host A（`loongson-lab`，3A6000 / loongarch64，Docker 26.1.5）。镜像 `yunixintel/karakeep:loong64`（digest `sha256:a8970acd868f...90cb`，1.45GB，`arch=loong64`）；Node v24.22.1；Python 3.11.6；Ghostscript 9.56.1。单容器 SQLite（`/data`），Web 端口 14000，mock OpenAI 端口 14080。未改宿主网络/防火墙，未改镜像/README/其它文档。

## 结论速览

| # | 功能 | 状态 | 结论 |
|---|---|---|---|
| 1 | Meilisearch 搜索 | **BLOCKED**（原生）/ PASS（未配置降级） | 官方无 loong64；源码需 Rust 1.91.1，非快速可编；未配置时查询 500，无回退 |
| 2 | monolith 全页归档 | **PASS** | Rust 1.85 构建 2.10.1 成功；生成 `fullPageArchive` 单文件 |
| 3 | 视频下载 | **PASS**（确认不提供） | 镜像无 yt-dlp/ffmpeg；开启开关后静默失败，属设计缺失非 bug |
| 4 | OCR / PDF 上传 | **PASS** | PDF 文本提取 96 字符 + 首页截图；图片 OCR 31 字符准确 |
| 5 | AI 打标/摘要 | **PASS** | mock OpenAI 调用成功，标签与摘要均写入 |
| 6 | OAuth / 多用户 | OAuth **BLOCKED**；多用户 **PASS** | 无外部 OIDC；第二用户 0 书签，跨用户取书签 404 |
| 7 | 外部 browserless WS | **BLOCKED**（无 browserless）/ 行为已确认 | WS 用 Playwright `connect`，与 CDP 不同；不可达 WS 会整体阻断抓取 |

## 1. Meilisearch：BLOCKED（原生）；未配置降级 PASS

- 官方 release 无 loong64：`v1.41.0` 资产仅 linux-amd64/aarch64、macos、windows、deb；最新 `v1.55.0` 同上并多一个 riscv64，均无 loong64。
- 源码构建门槛：`v1.41.0` 的 `rust-toolchain.toml` 要求 **Rust 1.91.1**；宿主 `rustc 1.85.0`，且无 rustup。官方 `rust-1.91.1-loongarch64-unknown-linux-gnu.tar.xz` 存在（HTTP 200），工具链可装但需额外下载。
- 架构依赖 spike：最小 crate 依赖 `ring 0.17.14` + `mimalloc 0.1.48` 在 loong64 编译并运行（`ring=32 mimalloc=ok digest=[c6,ba,ac,a9]`），说明不是硬性不可能；但 Meili 依赖图大，完整 release 构建超出 30 分钟窗口，本轮未完成，判 **BLOCKED**。
- 未配置实际表现：启动日志 `search:` 为空；索引 worker 输出 `[search][2] Search is not configured, nothing to do now`；`GET /api/v1/bookmarks/search?q=example` 返回 **HTTP 500**，日志 `TRPCError: Search functionality is not configured`。代码 `fullTextSearch()` 在 client 为空时直接 throw，**没有 SQLite FTS/LIKE 回退**。
- 剩余风险：搜索 API 不可用（不是“空结果”）；若产品要求全文搜索，需外部 Meili，或自研 provider。源码构建可作后续 1–2 小时专项，不是绝对 No-Go。

## 2. monolith 全页归档：PASS

```bash
cargo install monolith --version 2.10.1 --locked --root /tmp/monolith-root   # 5m24s
# 产物：ELF 64-bit LSB pie executable, LoongArch, monolith 2.10.1, 11.6MB
docker run ... -v /tmp/monolith-root/bin/monolith:/usr/local/bin/monolith:ro \
  -e CRAWLER_FULL_PAGE_ARCHIVE=true ...
```

- 容器内 `monolith --version` → `monolith 2.10.1`（动态链接 glibc 兼容）。
- 抓取 `https://example.com/?monolith-test=1`：`crawlStatus=success`；`assets` 出现 `assetType=fullPageArchive`；下载 822B，`content-type: text/html`，内容含 monolith CSP、`<base>` 与内联 `data:` URI。
- 日志：`[Crawler][26:0] Will attempt to archive page ...`，无失败。
- 剩余风险：monolith 需随镜像分发（本轮为宿主构建后挂载）；大页面受 `CRAWLER_FULL_PAGE_ARCHIVE_MAX_SIZE_MB`/超时限制。

## 3. 视频下载：PASS（确认“不提供”，非 bug）

- 镜像内检查：`command -v yt-dlp` → `NO_YTDLP`；`ffmpeg` → `NO_FFMPEG`。
- 设置 `CRAWLER_VIDEO_DOWNLOAD=true` 并添加 YouTube 书签：
  `[VideoCrawler][38] Attempting to download ... using ... yt-dlp` → `Failed to download ...`，随后 `Video Download Completed successfully`。
- 结论：worker 吞掉 `ENOENT`，书签不报错但无视频资产；功能应按“不提供”标注。剩余风险：用户开启该开关只会得到静默失败日志。

## 4. OCR / PDF 上传：PASS

- 手工 627B 单页 PDF（Helvetica 文本）→ `POST /api/v1/assets` → `POST /api/v1/bookmarks`（`assetType=pdf`）。
- 日志：`[assetPreprocessing][6] Extracted 96 characters from pdf`；`Successfully saved PDF screenshot`；`includeContent=true` 返回 `Karakeep loong64 PDF text extraction test 2026`，assets 含 `assetScreenshot`。
- 图片 OCR：GraphicsMagick 生成 700×220 PNG → `Attempting to extract text from image using Tesseract` → `Extracted 31 characters`，内容为 `Karakeep OCR loong64 test 2026`（准确）。
- 剩余风险：tesseract.js 首次运行需外网获取语言数据，默认缓存 `/tmp`，容器重建即丢失；离线部署应预置 `OCR_CACHE_DIR`/语言包。

## 5. AI 打标/摘要：PASS

- 本地 mock `POST /v1/chat/completions`；配置 `OPENAI_API_KEY`、`OPENAI_BASE_URL=http://172.17.0.1:14080/v1`、`INFERENCE_TEXT_MODEL=mock-model`、`INFERENCE_ENABLE_AUTO_TAGGING=true`、`INFERENCE_ENABLE_AUTO_SUMMARIZATION=true`。
- 文本书签：`taggingStatus=success`，写入 `ai-generated`/`karakeep`/`worker-test` 三个 AI 标签；mock 收到 `response_format={"type":"json_schema","json_schema":{"name":"schema","strict":true,... "required":["tags"]}}`，返回 `{"tags":[...]}`。
- 链接书签（example.com）：`taggingStatus=success`、`summarizationStatus=success`；mock 收到摘要请求 `response_format=null`，摘要写入 `summary` 字段。
- 代码细节：文本书签创建只入队 tag，不自动入队 summarize；链接抓取/资产预处理才入队 summarize。
- 剩余风险：真实模型必须遵守 strict JSON Schema；用户级 `autoSummarizationEnabled` 关闭会跳过摘要。

## 6. OAuth / 多用户：OAuth BLOCKED；多用户 PASS

- OAuth：容器无 `OAUTH_*` 环境；`createOAuthConfig()` 仅在 `OAUTH_WELLKNOWN_URL` 与 `OAUTH_CLIENT_ID` 同时存在时注册 custom provider。无外部 OIDC issuer → **BLOCKED**，登录/回调/账号链接无法验证。
- 多用户：注册第二个用户 bob（`role=user`）；Bob `GET /api/v1/bookmarks` → **0 条**；Alice 同期 **3 条**；Bob 取 Alice 书签 ID → **404 `Bookmark not found`**。首个用户 `role=admin`。
- 剩余风险：仅验证 API 列表/详情隔离，未验证配额与资产 signed URL 的越权（建议另行审计）。

## 7. 外部 browserless WebSocket：BLOCKED；行为已确认

- 代码差异：`BROWSER_WEBSOCKET_URL` → `chromium.connect(url)`（Playwright WS 协议）；`BROWSER_WEB_URL` → `chromium.connectOverCDP(url)`（CDP）。两者不是同一模式。
- 运行时配置 `BROWSER_WEBSOCKET_URL=ws://172.17.0.1:14099`（无服务）+ `BROWSER_CONNECT_ONDEMAND=true`：
  `Connecting to existing browser websocket address` → `browserType.connect: WebSocket error: connect ECONNREFUSED`；`crawlStatus=failure`，tagging/summarization 未运行；**没有回退到 plain HTTP**。
- 结论：无 browserless 环境，真实 WS 浏览器功能 → **BLOCKED**；但确认“配置了不可达 WS 会整体阻断抓取”，部署时仅在端点健康时设置。
- 剩余风险：真实 browserless 的鉴权、并发、目标站点可达性未验证。

## 清理

- 已删除测试容器 `karakeep-verify`、卷 `karakeep-verify-data`、mock 进程；未动宿主网络/防火墙，未动既有 `karakeep-private-test`。
- 保留 `/tmp/monolith-root/bin/monolith`（12MB）与 `/tmp/karakeep-archive.mhtml`（822B）供复核；其余临时源码/构建目录已删。
