# Karakeep 0.34.1 private 单镜像（内嵌 LBrowser）构建与测试记录

## 结论

- 镜像：**`local/karakeep-private:0.34.1-p1`**（仅本地，未推送）
- 镜像 ID：`sha256:6aa246e41c7b03273c687efe68095fb3face7ab0b0883428c6453b4489bfc3de`
- 架构：`linux/loong64`；本地大小 **2,338,654,386 B（2.34 GB）**
- 基础镜像：`yunixintel/karakeep:0.34.1`（`a8970acd868f`）
- 浏览器来源：`local/lbrowser-embedded:3.4.2293.2-local`（`1c9c0235e531`，LBrowser `3.4.2293.2`）
- 形态：**单容器**。同一容器内运行无头 LBrowser（127.0.0.1:9223）+ CDP 代理
  （127.0.0.1:9222）+ Karakeep web/workers（0.0.0.0:3000）；无 sidecar，
  无宿主 bind mount，只发布应用端口。
- 实测通过：健康检查、注册/登录、Wikipedia 抓取（截图 + PDF + HTML + banner）、
  重启持久化、重启后继续抓取、优雅停止、容器隔离、进程用户分离。
- 许可证：**LBrowser 再分发许可不明确，本镜像仅供本机使用，禁止分发/推送。**

## 与公共版 `yunixintel/karakeep:0.34.1` 的差异

| 项 | 公共版 | private 单镜像 |
|---|---|---|
| 浏览器 | 无；需外部 sidecar + 宿主挂载 | `/opt/apps/lbrowser` 烘进镜像 |
| 浏览器运行库 | 无 | 增加 GTK2/GTK3、NSS、CUPS、ALSA/Pulse、X11/AT-SPI、字体等 |
| entrypoint | `/entrypoint.sh` | `/entrypoint.private.sh` 包裹原 entrypoint |
| 对外端口 | 3000 | 3000；9222/9223 仅监听 127.0.0.1 |
| `BROWSER_WEB_URL` | 由用户设置 | entrypoint 内导出 `http://127.0.0.1:9222` |
| 截图/PDF | 需 sidecar | 原生支持，无需额外容器 |
| 体积 | 1.45 GB | 2.34 GB（+0.89 GB） |
| 分发 | 可推送 | **禁止推送** |

镜像层增量（`docker history`，近似）：

- 运行库/字体：499 MB（其中 CJK 字体占比较大）
- LBrowser 载荷：387 MB（`du` 370 MB）
- entrypoint / proxy：< 10 kB

## 文件

| 文件 | 说明 |
|---|---|
| `Dockerfile.private` | 基于公共镜像安装运行库、复制 LBrowser、注册 private entrypoint |
| `entrypoint.private.sh` | 启动浏览器 → 等 9223 → 启动代理 → 等 9222 → 导出 `BROWSER_WEB_URL` → 交给原 `/entrypoint.sh` |
| `cdp-proxy.mjs` | 与 `images/lbrowser/cdp-proxy.mjs` 逐字节相同（SHA-256 `c226311d59f285f7e195ec25729278b6c723c2efb04744646e1b71442a7314a2`） |
| `build-private.sh` | 本地构建脚本 |
| `BUILD-private.md` | 本文件 |

`Dockerfile.private` 只从 `local/lbrowser-embedded` 复制 `--from`，不使用
`dpkg`/Perl，不下载 deb，也不在构建时访问 LBrowser 分发地址。

## 构建

前置镜像：

```text
yunixintel/karakeep:0.34.1
local/lbrowser-embedded:3.4.2293.2-local
```

```bash
cd images/karakeep
./build-private.sh
# 等价于：
DOCKER_BUILDKIT=0 docker build --network=host \
  -f Dockerfile.private \
  -t local/karakeep-private:0.34.1-p1 .
```

- 构建上下文仍是 `images/karakeep/`；不需要 `artifacts/`。
- 首次构建（含 dnf 下载）约 **2 分 38 秒**；层缓存命中后约 **23 秒**。
- 构建机：Loongson-3A6000-HV（8 核）、Loongnix 25、内核
  `6.6.52-loong64`、Docker `26.1.5`。
- **不要**给镜像打 `yunixintel/*` tag，也不要执行任何 `push`。

## 运行

```bash
docker run -d --name karakeep-private \
  -p 3000:3000 \
  --shm-size=1g \
  -v karakeep-data:/data \
  -e NEXTAUTH_URL=http://<host>:3000 \
  -e CRAWLER_STORE_PDF=true \
  local/karakeep-private:0.34.1-p1
```

- `--shm-size=1g` 必须；浏览器与 Karakeep 共用该 shm。
- `/data` 用命名卷或 bind mount 均可；镜像本身不依赖宿主路径。
- `CRAWLER_STORE_PDF` 默认 false，**镜像不强制**；需要 PDF 时在运行时设置。
  实测确认镜像 `Config.Env` 不含该变量。
- 9222（CDP 代理）与 9223（LBrowser DevTools）只绑定 `127.0.0.1`，不要发布。
- 首个注册用户自动成为 admin；创建后建议设 `DISABLE_SIGNUPS=true`。

### 启动与退出流程

1. 启动 `/opt/apps/lbrowser/lbrowser --headless=new --remote-debugging-port=9223
   --remote-debugging-address=127.0.0.1 --no-sandbox --disable-dev-shm-usage
   --remote-allow-origins=* --user-data-dir=/tmp/lbrowser-profile about:blank`。
2. 轮询 `http://127.0.0.1:9223/json/version`，最多 60 秒。
3. 启动 `node /usr/local/lib/lbrowser/cdp-proxy.mjs`，监听 `127.0.0.1:9222`，
   上游 `127.0.0.1:9223`；轮询 9222。
4. `export BROWSER_WEB_URL=http://127.0.0.1:9222`，启动原 `/entrypoint.sh`。
5. 原 entrypoint 不变：生成/读取 `NEXTAUTH_SECRET`、迁移、以 UID/GID 1116
   启动 web + workers。
6. **不直接 `exec` 原 entrypoint**：`exec` 会丢掉本脚本的 trap，PID 1 无法在
   退出时回收浏览器/代理。这里以子进程方式运行并转发 TERM/INT；原 entrypoint
   仍负责 app/workers 的完整生命周期。退出顺序：app → CDP 代理 → LBrowser。
7. `docker stop` 退出码 0；容器内其余进程随 PID 1 退出被回收。

## 测试证据（Host A，实际执行）

测试容器：`--shm-size=1g`、命名卷 `karakeep-private-test-data:/data`、
`-p 127.0.0.1:13001:3000`、`NEXTAUTH_URL=http://127.0.0.1:13001`、
`CRAWLER_STORE_PDF=true`。**无 sidecar、无宿主 bind mount。**

| 项 | 结果 |
|---|---|
| 冷启动到 `/api/health` 200 | **6,861 ms**（最终镜像首次运行） |
| 健康检查 | 200 `{"status":"ok","message":"Web app is working"}`；Docker health=`healthy` |
| 首次注册 | `POST /api/auth/sign-up/email` → 200；首个用户 `role=admin` |
| 登录 | `POST /api/auth/sign-in/email` → 200；`get-session` → 200，同一用户 |
| Wikipedia 抓取 | `crawlStatus=success` |
| 截图日志 | `Captured the screenshot (211990 bytes)` → `Stored the screenshot` |
| PDF 日志 | `Captured the PDF (545208 bytes)` → `Stored the PDF` |
| 截图资产 | JPEG 1440×900，211,990 B，落盘 `.../asset.bin` |
| PDF 资产 | PDF 1.4，8 页，545,208 B，落盘 `.../asset.bin` |
| 其他资产 | HTML 277,148 B；banner WebP 1200×800，214,870 B |
| 重启 | `docker stop` 931 ms，容器退出码 **0**；日志有 `Cleanup done (exit 0)` |
| 重启后健康 | `/api/health` 200，用时 5,525 ms |
| 重启后持久化 | `NEXTAUTH_SECRET` SHA-256 不变；1 个书签、4 个资产仍在 |
| 重启后抓取 | `example.com` → `success`；PDF 92,459 B、截图 65,594 B；最终 2 书签/6 资产 |
| 隔离 | `HostConfig.Binds` 仅命名卷；无宿主路径；`ShmSize=1073741824`；bridge 网络 |
| 端口 | 仅 `3000/tcp → 127.0.0.1:13001`；9222/9223 为容器内 loopback |
| 进程用户 | `next-server`、`node dist/index.js` 为 `karakeep`（1116）；浏览器/代理为 root |
| 环境传递 | worker 进程 `/proc/<pid>/environ` 含 `BROWSER_WEB_URL=http://127.0.0.1:9222`、`CRAWLER_STORE_PDF=true` |
| 浏览器连接 | 日志 `Connecting to existing browser instance: http://127.0.0.1:9222/` |
| 端口监听 | `127.0.0.1:9223`（lbrowser）、`127.0.0.1:9222`（node cdp-proxy） |

说明：第一次抓取时 Wikimedia 缩略图返回 403（外部防盗链），属站点侧问题；
最终镜像复测时 banner 已正常落盘（WebP 214,870 B）。截图/PDF 不受影响。

## 许可证警告（必读）

- LBrowser deb 包**没有 LICENSE / COPYING / copyright 文件**，再分发许可不明确。
- 因此本镜像**只能在本机使用**：
  - 不要 `docker push`，不要推到 Docker Hub、私有 registry 或任何远端；
  - 不要打 `yunixintel/*` tag，不要把镜像分发给第三方；
  - 不要把 `/opt/apps/lbrowser` 或包含它的镜像层导出后公开。
- 公共版 `yunixintel/karakeep:0.34.1` 不含浏览器字节，不受此限制。

## 未验证

- **推送/分发**：按要求完全未执行；无 registry digest、无 `docker save`。
- **基础镜像 digest 固定**：`FROM` 使用 tag `0.34.1`，未改成 `@sha256:...`。
- **x86_64 / arm64 / 多架构**：仅构建并测试 `linux/loong64`。
- **Docker Compose 部署**：只用 `docker run` 验证；未跑 compose 文件。
- **非 root / 只读根文件系统 / rootless Docker / SELinux / AppArmor**：未验证；
  当前浏览器与代理以 root 运行，Karakeep 以 1116 运行。
- **长时间稳定性 / 内存增长**：仅短时抓取测试，未做 24h 压测。
- **并发抓取 / 多浏览器上下文**：仅单任务串行验证。
- **全文/语义搜索**：未配 Meilisearch。
- **全页单文件归档 / 视频下载 / OCR / PDF 文本提取 / AI 打标**：未验证。
- **S3 / Redis / Restate / 外部队列**：未验证。
- **多用户、邀请、邮件验证、OAuth**：未逐项验证。
- **LBrowser WebGL / 视频 / DRM / GPU**：未验证（当前为 SwiftShader 软件渲染）。
- **CDP 代理的 WebSocket 长连接压力**：仅实际抓取路径验证。
- **镜像体积优化**：CJK 字体与 GTK 运行库未裁剪，2.34 GB 为当前结果。

## 复现与清理

```bash
# 构建（仅本地）
cd images/karakeep && ./build-private.sh

# 测试容器/卷在证据采集后已清理：
docker rm -f karakeep-private-test
docker volume rm karakeep-private-test-data
```

镜像本身保留在 Host A 的本地 Docker daemon 中；测试结束后未推送、未导出。
