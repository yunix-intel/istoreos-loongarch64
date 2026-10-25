# Linkwarden 2.16.3 loong64 未验证功能复核

日期：2026-10-25。环境：Host A（3A6000 / Loongnix 25 / 6.6.52-loong64，8 核 31 GB）。
镜像 `yunixintel/linkwarden:loong64`（`sha256:2a00fb1b…d23340`，1,027,388,852 B）+
`yunixintel/postgres:loong64`（PG 15.18）+
`local/lbrowser-runtime:3.4.2293.2`（挂载宿主 `/opt/apps/lbrowser:ro`，`--shm-size=1g`）。
测试端口 14101–14106；测试后容器/卷/网络已清理，宿主网络与防火墙未改动。

## 结论

| # | 项 | 状态 | 摘要 |
|---|---|---|---|
| 1 | monolith 全页归档 | **PASS** | 2.10.1 源码构建 5m27s；挂载后 worker 生成单文件 HTML 并入库 |
| 2 | Meilisearch | **PASS** | 无官方 loong64 镜像；源码 22m21s 构建成功，索引 7 条，拼写容错搜索生效 |
| 3 | AI 打标 | **PASS** | mock OpenAI 调用、写库、aiTagged 全链路通过；并发批量有上游竞态 |
| 4 | 导入 | **PASS** | HTML / Pocket / Wallabag 三种 API 导入均成功 |
| 5 | OAuth / 邮箱 / 多用户 | **BLOCKED / FAIL / PASS** | OAuth 无 provider；邮箱流因镜像缺模板开箱即崩；用户隔离通过 |
| 6 | LBrowser 归档链路 | **PASS** | 截图/PDF/Readability/preview 存在且带鉴权可访问；核心回归通过 |

总体：核心归档、搜索、AI、导入可用；**邮箱相关功能需修镜像**（见 5.3），OAuth 无法在本地验证。

## 1. monolith 全页归档：PASS

- 构建：`cargo install --locked monolith@2.10.1 --root /build/mono-build/root`，Rust 1.85.0；
  日志 `Finished release profile ... in 5m 27s`，产物 11,592,192 B，ELF LoongArch，`monolith 2.10.1`。
- 挂载：`-v .../monolith:/usr/local/bin/monolith:ro`；worker 以 UID 1118 可直接执行。
  上游参数：`monolith - -I -b <url> -j -F -q -o -`（stdin 收 HTML、isolate、去 JS/字体）。
- `https://example.net`：DB `monolith=archives/1/4.html`，文件 3,415 B；
  `GET /api/v1/archives/4?format=4` 返回 `200 text/html 3415`。挂载前该字段为 `unavailable`。
- 复杂页 `https://en.wikipedia.org/wiki/Loongson`：2,389,810 B；
  `src="http…"` 0 个、`src="data:image"` 23 个、内联 `<style>` 10 个、外链 script 0 个；
  其余外链是 `<a>`/canonical/license 等元数据，不是渲染资源。单文件自包含成立。
- 风险：镜像不含 monolith，必须挂载或另建二进制；`MONOLITH_CUSTOM_OPTIONS` 会整体覆盖上述默认参数。

## 2. Meilisearch：PASS（源码构建 + 集成）

- 官方 `getmeili/meilisearch:v1.13.3` 的 Docker Hub manifest 仅 `linux/amd64`、`linux/arm64`，无 loong64。
- 源码：`git clone --branch v1.13.3`，`cargo build --release -p meilisearch --no-default-features`
  （Rust 1.85，仓库 pin 1.81；8 核）；日志 `Compiling meilisearch v1.13.3` +
  `Finished release profile ... in 22m 21s`（含拉取依赖总计 23m56s，≤30 分钟）。
  产物 42,903,872 B，`meilisearch 1.13.3`，`/health` = `available`。
  为避开 mini-dashboard 资产下载用了 `--no-default-features`，Web 面板不可用，API 不受影响。
- 集成：`MEILI_HOST=http://<gw>:14106`、`MEILI_MASTER_KEY=…`。worker 日志
  `Starting link indexing...`、`Indexed 7 links, 0 left.`；
  `/indexes/links/stats` → `numberOfDocuments: 7`。
- 证明走 Meili：搜索 `Loongsn`（少一个 o）命中 `Loongson Wikipedia`，SQL contains 不可能命中。
- 未配置时回退：无 `MEILI_*` 时 `GET /api/v1/links?searchQueryString=IANA` 与标签
  `pockettest` 均命中；代码对 name/url/description/tag 做 `contains`（insensitive）。PASS。
- 风险：无官方 loong64 镜像；自建二进制需随镜像分发并固定版本；mini-dashboard 未构建。

## 3. AI 打标：PASS（附并发缺陷）

- mock OpenAI 兼容服务（宿主 14104，SSE/JSON 均支持）。环境：
  `OPENAI_API_KEY=mock-key`、`OPENAI_MODEL=mock-model`、
  `CUSTOM_OPENAI_BASE_URL=http://172.24.0.1:14104/v1`；用户偏好
  `PUT /api/v1/users/1 {"aiTaggingMethod":"GENERATE"}`。
- 调用证据：mock 日志收到 `POST /v1/chat/completions`，`Authorization: Bearer mock-key`、
  `model=mock-model`、prompt 长度 1334；worker 日志
  `Tags for link: https://example.net => [ 'Loongson', 'Linux', 'Hardware' ]`。
- 写库证据：`Tag` 表 3 行 `aiGenerated=t`；`_LinkToTag` 关联到 link 2/4；
  `Link.aiTagged=t`。`GET /api/v1/config` 的 `AI_ENABLED=true`。
- 必需变量：任一 provider（`OPENAI_*`、`AZURE_*`、`ANTHROPIC_*`、`OPENROUTER_*`、
  `PERPLEXITY_*` 或 `NEXT_PUBLIC_OLLAMA_ENDPOINT_URL`+`OLLAMA_MODEL`）；
  用户 `aiTaggingMethod != DISABLED`；链接必须已 `lastPreserved`（即归档成功，无浏览器则不会打标）。
- 缺陷：`ARCHIVE_TAKE_COUNT=3` 并发处理 3 条链接且 mock 返回相同标签时，一条链接报
  Prisma `P2002`（Tag `name_ownerId` 唯一约束，`connectOrCreate` 并发竞态），该链接被标
  `aiTagged` 但无 AI 标签；改为串行（=1）重试两条均成功。属上游并发问题，建议默认 1 或加重试。
- 未覆盖：`EXISTING`、`PREDEFINED` 两种打标方式；真实厂商 API（仅 mock）。

## 4. 导入：PASS

- API：`POST /api/v1/migration`，JSON `{format,data}`；`1`=HTML、`2`=Wallabag、`4`=Pocket。
- HTML（Netscape 书签，2 条）：返回 `{"response":"Success."}`；新建集合 `Verify Import`，
  链接 `Example Org`、`IANA Reserved Domains` 入库，标签 `verify,import`。
- Pocket CSV（1 条）：`Success.`，集合 `Imports`，链接 `Pocket Verify`。
- Wallabag JSON（1 条）：`Success.`，集合 `Imports`，链接 `Wallabag Verify`。
- 全流程走 API，无需 UI/Playwright。导入只建链接，归档由 worker 异步补；测试用的
  `https://example.info/` 不存在，归档字段为 `unavailable`（符合预期，不是导入失败）。

## 5. OAuth / 邮箱 / 多用户

### 5.1 OAuth：BLOCKED
`/api/v1/auth/providers` 只返回 `credentials`；`GOOGLE_ENABLED=null`，未配置任何外部 provider，
无法验证 Google/GitHub 等登录。

### 5.2 凭据登录与隔离：PASS
- `POST /api/v1/users` → 201（用户 1）；NextAuth credentials → 200，`/users/me` 同 id。
- 用户 2 注册/登录后：`/users/me` id=2；`/api/v1/links` 空、`/api/v1/collections` 空；
  `PUT /api/v1/users/1` → 401；`GET /api/v1/archives/1?format=1` → 401。隔离成立。

### 5.3 邮箱注册/登录：开箱 FAIL，补模板后 PASS
- 配置 `EMAIL_SERVER=smtp://…`、`EMAIL_FROM`、`NEXT_PUBLIC_EMAIL_PROVIDER=true` 后，
  注册可写入 email；但邮件登录报
  `ENOENT: no such file or directory, open '/data/apps/web/templates/verifyEmail.html'`。
  镜像的 `artifacts/apps/web` 未包含上游 `apps/web/templates/`（4 个邮件模板），
  **这是镜像打包缺陷**，邮箱验证/改邮箱/找回密码/邀请都会受影响。
- 临时挂载 `apps/web/templates:/data/apps/web/templates:ro` 并设置
  `BASE_URL=http://127.0.0.1:14102`（上游邮件链接用 `BASE_URL`，不是 `NEXTAUTH_URL`）后：
  mock SMTP 收到邮件，链接为 `http://127.0.0.1:14102/auth/verify?token=…&email=…`；
  调用 `/api/v1/auth/callback/email` → 302 + session cookie，`/users/me` 返回
  `emailVerified=2026-10-25T10:24:53Z`。未验证用户凭据登录返回 401
  `Email not verified.`，校验生效。
- 修复建议：构建上下文补 `apps/web/templates`，文档补 `BASE_URL`。

## 6. LBrowser 归档链路：PASS（核心回归）

- sidecar：`local/lbrowser-runtime:3.4.2293.2 serve`，日志
  `DevTools listening on ws://127.0.0.1:9223/...`、`CDP proxy listening on 0.0.0.0:9222`；
  Linkwarden 用 `PLAYWRIGHT_WS_URL=http://lwv-browser:9222`，worker 日志
  `Connecting to remote browser (http://lwv-browser:9222)`、`Succeeded processing link`。
- `https://example.com`（link 1）资产：
  - 截图 `archives/1/1.jpeg` 62,610 B，JPEG 1265×823；
  - PDF `archives/1/1.pdf` 92,483 B，`%PDF-1.4`，1 页；
  - Readability `archives/1/1_readability.json` 3,114 B，可 `json.load`，含 `content`；
  - OG 预览 `archives/preview/1/1.jpeg` 26,300 B，JPEG 1280×720。
- 可访问性：带会话 cookie `GET /api/v1/archives/1?format=1|2|3` 均 200，Content-Type 分别
  `image/jpeg`/`application/pdf`/`application/json`；`format=1&preview=true` 200；
  不带 cookie 全部 401。归档 API 鉴权正常。
- 另测 `example.net`、`example.edu`、Wikipedia 均成功（含 monolith）；截图/PDF/Readability/
  preview 字段与磁盘文件一致。
- 风险：Chromium 138 与 Playwright 1.57 期望的 143 有版本差；只测了简单页与 Wikipedia，
  WebGL/视频/DRM/复杂 SPA 未覆盖；sidecar 日志有 Vulkan 无驱动告警，不影响 headless 截图/PDF。

## 7. 剩余风险与建议

1. **邮箱模板缺失**（高）：补 `apps/web/templates/`；否则 SMTP 相关功能不可用。
2. **`BASE_URL` 未文档化**（中）：邮件链接依赖它，缺失时生成 `undefined/auth/verify`。
3. **monolith 未内置**（中）：需挂载二进制；否则 HTML 归档为 `unavailable`（其他格式不受影响）。
4. **Meilisearch 无官方 loong64**（中）：自建 42.9 MB 二进制，22m21s/8 核；未构建 mini-dashboard。
5. **AI 并发竞态**（中）：`ARCHIVE_TAKE_COUNT=1` 或对 `P2002` 重试；多链接同标签时易触发。
6. **OAuth 未验证**（低）：需外部 provider；本地无凭据。
7. **浏览器版本差与许可**（中）：Chromium 138 vs 143，复杂站点需抽样回归；LBrowser 不可公开再分发。

## 8. 清理

测试容器 `lwv-app/lwv-pg/lwv-browser`、卷 `lwv-data/lwv-pgdata`、网络 `lwv-net` 已删除；
mock AI/SMTP、Meilisearch 进程已停止；未修改宿主网络、防火墙或镜像。
