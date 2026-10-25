# Linkwarden 2.16.3 private 单镜像（LBrowser 内置）构建记录

> **许可证警告：禁止分发。** LBrowser deb 不含 `LICENSE`/`COPYING`/`copyright`
> 文件，再分发授权不清晰。本镜像只允许在本机构建、本机使用，**不得 tag 成
> `yunixintel/*`，不得 push 到 Docker Hub 或任何 registry**。`build-private.sh`
> 对非 `local/*` 的镜像名直接拒绝构建。

## 结论

- 镜像：`local/linkwarden-private:2.16.3-p1`（唯一 tag）
- 镜像 ID：`sha256:44ac2849982bc73d16e51a27dc6817703150d2071a05e9b69595713a224b5f5c`
- 架构：`linux/loong64`；本地大小 2,070,824,576 B（`docker images`
  显示 2.07 GB）
- 基线：`yunixintel/linkwarden:2.16.3`（1,027,424,379 B，
  ID `sha256:4825ae5e8f23…`）
- 浏览器：`local/lbrowser-embedded:3.4.2293.2-local` 中的
  `/opt/apps/lbrowser`（386,909,552 B，LBrowser 3.4.2293.2 / Chromium
  138.0.7204.310）
- 形态：Web + Worker + LBrowser **单容器**；无 sidecar、无
  `/opt/apps/lbrowser` 宿主挂载、无 `PLAYWRIGHT_WS_URL`
- 范围：只在本机使用；未 push，无 registry digest
- 实测：PostgreSQL + 单镜像，99 迁移、`/` 200、注册/登录、集合、书签
  `https://example.com`、截图/PDF/Readability/OG preview 全部在容器内生成、
  重启幂等且归档保留、进程 UID 1118、`--shm-size=1g`
- 邮件：`apps/web/templates/` 4 个模板在 private 镜像内；mock SMTP 实测
  注册→验证邮件→`callback/email` 302+session→`emailVerified` 非空

## 与公共版的差异

| 项 | `Dockerfile`（公共） | `Dockerfile.private` |
|---|---|---|
| 浏览器 | 不内置；`PLAYWRIGHT_WS_URL` 接 sidecar 或挂载宿主 LBrowser | `/opt/apps/lbrowser` 烘进镜像 |
| 运行库 | `ca-certificates tzdata bash util-linux shadow` | 再加 openEuler 24.03 的 GTK/NSS/X11/ALSA/CUPS/字体等 100 个包 |
| 默认环境 | 无 `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH` | 固定设为 `/opt/apps/lbrowser/lbrowser` |
| 无浏览器时 | entrypoint 自动 `DISABLE_BROWSER=true` | 不触发（executable path 非空） |
| 归档 | 依赖外部浏览器 | worker 自己拉起 LBrowser |
| 外部依赖 | 无 | 构建期需要 `local/lbrowser-embedded:3.4.2293.2-local` |
| 体积 | 1.03 GB | 2.07 GB |
| 分发 | `yunixintel/linkwarden` | 仅 `local/linkwarden-private` |

entrypoint 与 worker 的实际判断（无需改代码）：

- `entrypoint.sh` 只在 `PLAYWRIGHT_WS_URL` **和**
  `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH` 都为空时才设置
  `DISABLE_BROWSER=true`。本镜像的 executable path 是镜像级 ENV，因此不会
  走降级分支。
- `apps/worker/lib/browser.ts`：`PLAYWRIGHT_WS_URL` 存在时用
  `chromium.connectOverCDP()`；否则把
  `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH` 转成
  `chromium.launch({ executablePath })`。
- `apps/worker/workers/linkProcessing.ts` 的日志据此区分
  `Connecting to remote browser (...)` 与 `Launching browser.`。本次实测日志
  只有后者，见下。
- 运行时若显式设置 `PLAYWRIGHT_WS_URL`，仍会优先走 sidecar（未在本次镜像上
  重测）。

## 构建

前提：两个本地镜像已存在。

```bash
docker image inspect yunixintel/linkwarden:2.16.3
docker image inspect local/lbrowser-embedded:3.4.2293.2-local
```

构建：

```bash
cd images/linkwarden
./build-private.sh
```

等价于：

```bash
DOCKER_BUILDKIT=0 docker build --network=host \
  -f Dockerfile.private \
  --build-arg LBROWSER_IMAGE=local/lbrowser-embedded:3.4.2293.2-local \
  -t local/linkwarden-private:2.16.3-p1 .
```

- 构建上下文中**不需要** `artifacts/`：应用代码已在公共镜像里。
- 不安装 `dpkg`/Perl：浏览器载荷用多阶段
  `COPY --from=lbrowser /opt/apps/lbrowser /opt/apps/lbrowser` 复制。
- 构建期守卫：`test -x /opt/apps/lbrowser/lbrowser` 且
  `ldd ... | grep -q "not found"` 必须无输出，否则构建失败。
- 2026-10-25 实构建：dnf 安装 100 个包、升级 1 个，下载 314 MB；
  新增层 `dnf` 656 MB + `COPY` 387 MB；结果
  `Successfully tagged local/linkwarden-private:2.16.3-p1`。
- 实测容器内 `rpm -q perl dpkg` 均为 `package ... is not installed`。

## 运行

```bash
docker run -d --name linkwarden-private \
  -p 3000:3000 \
  --shm-size=1g \
  -v linkwarden-data:/data/data \
  -e DATABASE_URL=postgresql://linkwarden:change-me@postgres:5432/linkwarden \
  -e NEXTAUTH_URL=http://<host>:3000/api/v1/auth \
  -e NEXTAUTH_SECRET="$(openssl rand -base64 32)" \
  local/linkwarden-private:2.16.3-p1
```

- 不要挂载 `/opt/apps/lbrowser`，不要设置 `PLAYWRIGHT_WS_URL`。
- **必须 `--shm-size=1g`**（默认 64 MB 的 `/dev/shm` 在复杂页面下容易崩）。
- 浏览器以 UID 1118 运行，Playwright 默认带 `--no-sandbox`；
  `HOME=/data`，profile 落在 `/tmp/playwright_chromiumdev_profile-*`。
- 其余参数（`NEXTAUTH_URL` 必带 `/api/v1/auth`、自动 `NEXTAUTH_SECRET`、
  持久化 `/data/data`）与公共版一致。

## 邮件与 `BASE_URL`

private 镜像继承公共镜像的 `/data/apps/web/templates/`，包含
`acceptInvitation.html`、`passwordReset.html`、`verifyEmail.html`、
`verifyEmailChange.html`。启用邮件需同时设置：

```bash
-e BASE_URL=http://<host>:3000 \
-e EMAIL_FROM=linkwarden@example.com \
-e EMAIL_SERVER=smtp://user:pass@smtp.example.com:587
```

- `BASE_URL` 是站点根（不带 `/api/v1/auth`），邮件正文链接为
  `${BASE_URL}/auth/verify?token=…`；未设置时会生成
  `undefined/auth/verify?...`，流程不可用。
- `NEXTAUTH_URL` 仍须是 `http://<host>:3000/api/v1/auth`。
- `EMAIL_FROM`/`EMAIL_SERVER` 任一缺失时 `emailEnabled=false`，不发验证邮件。

## 测试证据（2026-10-25，Host A / loong64，实际执行）

环境：user-defined network `lwp-net`；`lwp-pg`
（`yunixintel/postgres:loong64`）；`lwp-app`
（`local/linkwarden-private:2.16.3-p1`，`127.0.0.1:14112->3000`，
`--shm-size=1g`，`-v lwp-data:/data/data`，固定 `NEXTAUTH_SECRET`）。
**无浏览器 sidecar，无 /opt/apps/lbrowser 挂载，无 PLAYWRIGHT_WS_URL。**

| 项 | 结果 |
|---|---|
| 全新数据库迁移 | `MIGRATIONS_OK applied_now=99 already=0 recorded=99 folders=99` |
| `/` | HTTP 200；Docker health 转 `healthy` |
| 注册 | `POST /api/v1/users` 201，用户 id=1，`archiveAsScreenshot/PDF/Readable=true` |
| 登录 | NextAuth credentials 200；`/api/v1/users/me` 200，同一用户 |
| 集合 | `POST /api/v1/collections` 200，id=1 |
| 书签 | `POST /api/v1/links` 200，id=1，`https://example.com` |
| 截图 | `/data/data/archives/1/1.jpeg`，62,610 B，magic `ff d8 ff` |
| PDF | `/data/data/archives/1/1.pdf`，92,483 B，magic `%PDF-` |
| Readability | `/data/data/archives/1/1_readability.json`，3,114 B，含 `readability-page-1` 正文 |
| OG preview | `/data/data/archives/preview/1/1.jpeg`，25,310 B，magic `ff d8 ff` |
| Monolith | `unavailable`；日志 `spawn monolith ENOENT`，与公共版一致（镜像未装 monolith） |
| 浏览器路径 | 日志 `Launching browser.`；无 `Connecting to remote browser` |
| 浏览器版本 | `browser.version()` = 138.0.7204.310；`goto` HTTP 200 / title `Example Domain` |
| 进程用户 | `next-server`、`tsx worker.ts`、`lbrowser` 及其子进程均为 UID 1118 |
| 浏览器命令 | `/opt/apps/lbrowser/lbrowser ... --headless --no-sandbox --disable-dev-shm-usage --remote-debugging-pipe` |
| 运行时挂载 | 仅 `lwp-data:/data/data`；`ShmSize=1073741824` |
| 重启 | 迁移 `applied_now=0 already=99`；`/` 200；截图/PDF/Readability/preview 与书签均在 |
| 镜像内版本 | `LBrowser 3.4.2293.2`；`rpm -q perl dpkg` 均未安装 |
| 邮件模板 | `/data/apps/web/templates/` 4 个文件，9006/8761/8301/9459 B |
| 邮件验证（private） | 新库 99 迁移；注册 `priv@example.com` 201；`request-verification-email` 200；mock SMTP 收到 9,403 B，链接 `http://127.0.0.1:13011/auth/verify?token=…` |
| 邮件回调（private） | `/api/v1/auth/callback/email` 302 → `http://127.0.0.1:13011`，Set-Cookie `next-auth.session-token` |
| 验证结果（private） | `/users/me` 200，`emailVerified:"2026-10-25T11:01:59.212Z"`；DB `emailVerified` 非空 |
| 未验证登录 | 公共镜像实测 `callback/credentials` 401（`Email not verified.`）；private 代码相同 |

关键日志（`docker logs -t lwp-app`）：

```text
2026-10-25T10:26:52.107651536Z Launching browser.
2026-10-25T10:26:55.965881810Z Succeeded processing link https://example.com for user 1.
```

即浏览器启动 + 页面加载 + 截图 + PDF + Readability + preview + 入库共约
3.86 s（含首次 Chromium 冷启动）。

独立浏览器冒烟（同一镜像，UID 1118，`--shm-size=1g`）：

```text
browser 138.0.7204.310 status 200 title Example Domain
png 85260
pdf 92419
```

### 复现

```bash
cd images/linkwarden
./test-private.sh        # 会删除并重建 lwp-* 容器/卷，输出到 ./test-output/
```

## 体积与启动开销

```text
local/linkwarden-private  2.16.3-p1  44ac2849982b  2.07 GB   (2,070,824,576 B)
yunixintel/linkwarden     2.16.3      4825ae5e8f23  1.03 GB   (1,027,424,379 B)
delta: 1,043,400,197 B = 995.1 MiB (2.015x)
```

新增层：

| 层 | 大小 |
|---|---|
| `dnf install` 运行库 + 字体 | 656 MB |
| `COPY --from=lbrowser /opt/apps/lbrowser` | 387 MB |
| ENV/LABEL | 0 B |

关于“多约 370MB”：370 MB 是 LBrowser 载荷本身；共享的
`local/lbrowser-runtime` 已经包含那套 GTK/NSS/X11 运行库，所以
embedded 版只比 runtime 版多约 370 MB。公共 Linkwarden 镜像没有这些库，
因此相对公共版的真实增量是 **载荷 ~369 MiB + 运行库/字体 ~625 MiB ≈ 995 MiB**。

启动开销（同一已迁移数据库）：

| 场景 | 到 `/` 200 |
|---|---|
| private 首次启动（含 99 迁移） | 6 s |
| private 重启（迁移幂等） | 5 s |
| 公共镜像同库启动（无浏览器） | 8 s |
| 首次启动到 Docker `healthy` | +26 s（受 30 s healthcheck 间隔影响） |

Next.js 重启日志 `✓ Ready in 684ms`。浏览器不在启动时拉起，只在有链接待
处理时启动，因此常驻启动开销与公共版基本无差异（差异在噪声范围内）。

## 许可证与分发

- LBrowser deb `3.4.2293.2-1.stable` 的 control/payload 中没有
  `LICENSE`、`COPYING`、`copyright`、`NOTICE` 或 EULA；只有上游 Chromium
  组件的 SPDX 表达式，等于没有 Loongson 对整包的再分发授权。
- 因此本镜像**禁止分发**：不 push、不导出给第三方、不作为公开产物发布。
- `build-private.sh` 只接受 `local/*` 镜像名；不要手工
  `docker tag ... yunixintel/...`。
- 本机更新 LBrowser 时必须重新构建镜像（浏览器安全更新不随包管理器走）。

## 未验证

- **Monolith / 单文件 HTML**：镜像未装 monolith，仍为 `unavailable`。
- **`PLAYWRIGHT_WS_URL` sidecar 覆盖**：代码路径与公共版相同，但未在本镜像
  上重测。
- **复杂站点回归**：只测 `example.com`；WebGL、视频、DRM、GPU、大页面、
  长时间多标签、并发归档未验证。
- **`--shm-size` < 1g**：未测；按共享镜像结论至少 512 MB，推荐 1g。
- **Meilisearch**、**AI 打标/摘要**、**RSS 外部源**、**导入 HTML/Pocket/
  Wallabag**：未部署/未逐项跑。
- **Wayback Machine、OAuth/SSO、Stripe**：未配置。
- **改邮箱（verifyEmailChange.html）/ 邀请（acceptInvitation.html）完整链路**：
  模板已随镜像提供，未逐项跑通；邮箱验证与找回密码已在公共镜像实测。
- **上传 PDF/图片类型的书签**、**多用户/邀请/权限**：未测试。
- **非 root、只读根文件系统、SELinux/AppArmor、rootless Docker**：未验证。
- **反向代理后的 `NEXT_PUBLIC_USER_CONTENT_DOMAIN` 归档查看页**：未配置。

## 文件

- `Dockerfile.private`：公共镜像 + 运行库 + `COPY --from` LBrowser 载荷
- `build-private.sh`：只允许 `local/*` 的构建入口，`DOCKER_BUILDKIT=0`
- `test-private.sh`：PostgreSQL + 单镜像的真实归档测试（会重建 `lwp-*` 资源）
