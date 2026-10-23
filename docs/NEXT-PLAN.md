# 下一步计划：应用镜像与平台工作流

制定日期：2026-10-23  
状态：**计划，未开工**。本文件只排期，不代表已构建或已承诺发布日期。  
依据：现有 87 个镜像、[STORE-COVERAGE.md](STORE-COVERAGE.md) 的 8 个阻塞结论、
以及两份独立子代理调研（存储/媒体方向、生产力/自动化方向）。

对应详细设计：[APP-DESIGNS.md](APP-DESIGNS.md)。本文件只排期；具体构建路径与运行时契约在设计稿中。

## 0. 范围

本计划包含：

- **P1–P4 共 26 个应用候选**：全部列明技术栈、LoongArch64 路径、风险和验收标准。
  经 2026-10-23 独立审查后：**21 个可进入后续波次，5 个暂停/暂缓**（Komga、Karakeep、
  Linkwarden、Joplin、wg-easy）。
- **CasaOS 工作流**：P3 收尾、真实盘验收、发布闸门、上游化。
- **OpenMediaVault（OMV）工作流**：Gate 0 可行性调研，不预设一定移植。
- 每个镜像的完成定义（DoD）和执行顺序。

不在本计划内：

- 已判定阻塞的 8 个商店应用（Emby、Plex、MT Photos、UniFi、Immich、PhotoPrism、
  PVE、Ubuntu），见 [BLOCKED-APPS.md](BLOCKED-APPS.md)。
- 闭源、依赖 TensorFlow/ONNX、或明显与现有镜像重复的应用，见第 10 节。

## 1. 优先级定义

| 级别 | 含义 | 进入条件 |
|---|---|---|
| **P1** | 下一批直接做；补真实空白，依赖风险低 | 有源码路径，关键依赖可编，已有同类构建经验 |
| **P2** | 第二批；价值高但多服务或需决策 | P1 完成或并行资源允许 |
| **P3** | 有价值但排后；依赖更重或受众更窄 | P1/P2 完成后按需 |
| **P4** | 待验证/备选；证据不足或优先级低 | 用户明确需要时再做 spike |
| **平台** | CasaOS/OMV，不是单个容器镜像 | 不影响容器构建主线，可并行调研 |

难度是工程量估算，不是日历承诺：

- 低：1 个镜像，Go/PHP/静态为主，1–2 天。
- 中：需要前端 x86 构建、CGO、多服务或原生模块，3–7 天。
- 高：需要改上游代码或多镜像编排，1–2 周。

## 2. P1：建议下一批直接做（5 个）

| ID | 应用 | 价值 | 技术栈 / 关键依赖 | LoongArch64 路径 | 难度 | 主要风险 / 前置 |
|---|---|---|---|---|---|---|
| P1-01 | **Zigbee2MQTT** | Zigbee 网关；已有 Home Assistant + Mosquitto，缺这一环 | Node 24 + `@serialport/bindings-cpp`；TypeScript | 源码编 serialport；Node 24 loong64 镜像已有 | 低中 | 需 USB 协调器透传（`/dev/ttyACM0`）；无协调器时只能验证 UI/MQTT |
| P1-02 | **Scrutiny** | 硬盘 SMART 历史、阈值告警；NAS 刚需 | Go + 纯 Go SQLite；smartctl 7.5 自编；Angular 前端 | 后端无 CGO；smartctl 用 `--without-libcap-ng` 静态编；前端 x86 构建 | 中低 | 需 `/dev/sd*`、udev、`CAP_SYS_RAWIO`；USB 读卡器可能不支持 SMART |
| P1-03 | **SFTPGo** | 带 Web 管理的 SFTP/FTP/WebDAV，补 filebrowser 停止维护后的空缺 | Go + `mattn/go-sqlite3`（CGO）或 PostgreSQL；前端已嵌入 | 复用现有 CGO-sqlite 配方；也可用 Postgres 完全避开 CGO | 低 | 默认配置需改；公网使用必须配 TLS/限权 |
| P1-04 | **BookStack** | Wiki/知识库；当前为零 | PHP 8.3 + Laravel + MariaDB；需 pdo_mysql/gd/zip/dom/mbstring/curl | 纯 PHP，复用现有 nginx/php-fpm + MariaDB 镜像 | 中 | 必须 MariaDB/MySQL；openEuler 可能要补 `php-gd`/`php-zip` |
| P1-05 | **Vikunja** | 任务/项目管理、Kanban、CalDAV；当前为零 | Go 1.27 + Vue；CGO SQLite；Postgres/MySQL 可选 | Go 可编；`sass-embedded` 无 loong64，前端在 x86 构建 | 中 | 无 Redis；迁移随启动执行；前端产物需拷回 |

### P1 验收标准

- P1-01：Web 200；MQTT 能连上 Mosquitto；有协调器时能识别并配对设备；无协调器时文档明确说明。
- P1-02：Web 200；至少一块磁盘出现在 SMART 列表；采集器定时运行；设备直通方式写入 RUNBOOK。
- P1-03：Web 管理 200；创建用户；SFTP 登录；上传/下载；配额生效。
- P1-04：安装/迁移完成；登录；创建书架/章节/页面；全文搜索可用。
- P1-05：注册/登录；创建项目与任务；Kanban 拖动；CalDAV 端点可访问（可选）。
- 所有 P1 镜像：`linux/loong64` + `loong64` / `24.10-la5` 双 tag，健康检查 healthy。

## 3. P2：第二批（6 个）

| ID | 应用 | 价值 | 技术栈 / 关键依赖 | LoongArch64 路径 | 难度 | 主要风险 / 前置 |
|---|---|---|---|---|---|---|
| P2-01 | **Piwigo** | 传统 PHP 相册；照片功能最快落地 | PHP 8.3 + MariaDB + GD/ImageMagick | 复用现有 PHP/MariaDB/nginx 栈 | 低 | UI 较老；必须 MariaDB/MySQL |
| P2-02 | **Ente** | 端到端加密相册；移动端自动备份 | Go `museum` + PostgreSQL + S3/MinIO；Web 端独立 Next.js | 源码可编；Postgres/MinIO 镜像已有 | 中 | 多服务；无 ML 搜索；Web 端需单独构建；镜像可能拆 2–3 个 |
| P2-03 | **Headscale** | 自建 Tailscale 控制面；固件已有 tailscale 客户端 | 纯 Go；现代 SQLite 或 Postgres；内嵌 DERP | `GOARCH=loong64 go build` | 低 | 无 Web UI，CLI/API；密钥与 preauth 配置需文档 |
| P2-04 | **Authelia** | SSO/TOTP/WebAuthn，保护 NPM/Caddy/Gitea | Go + React/Vite；CGO SQLite；Redis 可选 | Go 可编；前端 x86 或 rollup loong64 | 中 | YAML 配置复杂；必须已有反代；误配置会锁住入口 |
| P2-05 | **Backrest** | restic 的 Web UI、调度、快照浏览、恢复 | Go + 纯 Go SQLite；内嵌 React；调用 restic | Go 可编；restic 纯 Go，源码编后设 `BACKREST_RESTIC_COMMAND` | 低中 | restic 无 loong64 发布资产，必须自编；与 Kopia 定位不同 |
| P2-06 | **go2rtc** | 摄像头 RTSP/WebRTC 网关；Frigate 受阻但实时预览可独立用 | 纯 Go 单二进制 | 直接编 | 低 | **两个子代理都未覆盖**，需先验证；与 MediaMTX 二选一 |

### 照片路线决策

- **P2-01 Piwigo 先做**：单应用 + 现有 MariaDB，最快把照片功能从 0 到 1。
- **P2-02 Ente 第二阶段**：需要 PostgreSQL + MinIO + Web 端，集成成本高，但移动端和加密能力是 Piwigo 没有的。
- 不建议同一批同时做两个；先完成 Piwigo，再根据实际使用决定是否上 Ente。

### P2 验收标准

- Piwigo：上传照片、建相册、生成缩略图、用户权限。
- Ente：`museum` 健康；Web 端 200；创建账号；上传/下载一张照片；MinIO 中有对象；文档列明全部服务。
- Headscale：创建用户与 preauth key；用 tailscale 客户端注册一个节点；`headscale nodes list` 可见。
- Authelia：门户 200；TOTP 登录；与 NPM/Caddy 的 forward-auth 示例可用。
- Backrest：UI 200；初始化 restic 仓库；备份并恢复一个小目录。
- go2rtc：Web 200；配置一个测试流（RTSP 或合成源）；播放页可打开。

## 4. P3：有价值但排后（6 个）

| ID | 应用 | 价值 | 技术栈 / 关键依赖 | LoongArch64 路径 | 难度 | 主要风险 |
|---|---|---|---|---|---|---|
| P3-01 | **Komga** | 漫画/PDF/EPUB 服务器，补 Calibre-Web 的漫画场景 | Kotlin/Spring Boot fat jar；Java 17+；`sqlite-jdbc` | jar 跨架构；`sqlite-jdbc` 的 loong64 native 必须自编/注入 | 中 | HEIF/JXL 封面 JNI 不可用；PDFBox/junrar 为纯 Java |
| P3-02 | **Matomo** | 完整网站分析 | PHP + MariaDB | 复用现有 PHP/MariaDB 栈 | 中 | 比 Umami 重；归档 cron；官方镜像仅 amd64/arm64 |
| P3-03 | **MeTube** | yt-dlp Web 队列，归档视频到 NAS | Python 3.13 + Angular + ffmpeg + yt-dlp | Python/Node/ffmpeg 均可编 | 低中 | 上游 extras 含 `curl-cffi`/`deno`，需去掉；用 Node 跑 yt-dlp-ejs |
| P3-04 | **SABnzbd** | Usenet NZB 下载，补 *arr 栈 BT 之外的缺口 | Python + sabctools/CT3 + par2 + unrar | C/Rust 扩展可编；par2 可编 | 中 | `unrar` 是 freeware 许可，分发前需确认；无上游 loong64 镜像 |
| P3-05 | **Autobrr** | 私种 IRC announce → qBittorrent/*arr | Go + `modernc.org/sqlite`（无 CGO）+ React | Go 可编；前端 x86 | 低 | `modernc sqlite` 可能需升到 1.61 才有 loong64 |
| P3-06 | **Woodpecker CI** | 给 Gitea/Gogs 补 CI/CD | Go server/agent + Vue/pnpm；CGO SQLite | 源码可编；发布资产有 riscv64 但无 loong64 | 中 | agent 需 `docker.sock` 和权限；流水线基础镜像需来自本仓库 |

### P3 启动条件

- **审查后：P3-01 Komga 暂停**，`sqlite-jdbc` 无 loongarch64 JNI；先做 native spike，未通过前不排期。
- Matomo 在 BookStack 的 PHP/MariaDB 栈稳定后复用。
- MeTube 先验证 Python 3.13 + yt-dlp PO-token 路径。
- SABnzbd 先确认 `unrar` 许可与打包方式。
- Autobrr 的 modernc sqlite 1.60.1 已含 loong64，无需升级。
- Woodpecker 在 Gitea 镜像稳定后做；需要 Docker socket 的权限模型写入文档。

## 5. P4：待验证 / 备选（9 个）

| ID | 应用 | 定位 | 待验证点 | 启动触发条件 |
|---|---|---|---|---|
| P4-01 | **MediaMTX** | RTSP/WebRTC 流媒体服务器 | 与 go2rtc 二选一；纯 Go，风险低 | go2rtc 不满足多路/协议需求时 |
| P4-02 | **Karakeep** | 书签/知识库 + 自动抓取 | 网页归档需要 Chromium，镜像很大 | 需要完整网页快照时 |
| P4-03 | **Readeck** | 稍后读 + 全文归档 | Go 单二进制；与 Wallabag/Shiori 重叠 | 现有阅读器不满足时 |
| P4-04 | **Linkwarden** | 书签协作 | Next.js + Postgres，多服务 | 需要团队书签时 |
| P4-05 | **Joplin Server** | Joplin 同步服务 | Node + SQLite/Postgres | 有 Joplin 客户端用户时 |
| P4-06 | **wg-easy** | WireGuard 管理 UI | 需宿主内核模块和 `NET_ADMIN` | 需要 WireGuard 时；否则用 Tailscale/Headscale |
| P4-07 | **Registry** | 私有 Docker 镜像仓库 | Go 单二进制，低风险 | 需要本地 registry 时 |
| P4-08 | **Pocket ID** | 轻量 OIDC 提供商 | Authelia 的替代路线，二选一 | Authelia 配置过重时 |
| P4-09 | **Unpackerr** | *arr 解压辅助 | Go 纯二进制 | *arr 栈出现解压需求时 |

P4 不进入当前排期；每项启动前先做 1 天以内的依赖 spike，再决定是否转 P3。

**审查后调整（2026-10-23）：**

- **P4-02 Karakeep 暂停**：sharp/libvips 无 loong64 + Chromium 依赖。
- **P4-04 Linkwarden 暂停**：Prisma engines 无 loong64 + Playwright/Chromium + sharp。
- **P4-05 Joplin Server 暂缓**：sharp/sqlite-vec/sqlite3 无 loong64，先做 native spike。
- **P4-06 wg-easy 暂缓**：libsql 无 loong64 预编译，先证明可从 Rust 源码构建。
- P4 可评估项缩减为：MediaMTX、Readeck、Registry、Pocket ID、Unpackerr。

## 6. CasaOS 工作流

CasaOS 不是容器镜像，而是 Debian/systemd 侧的应用面板。详细构建与运行见
[CASAOS-P3.md](CASAOS-P3.md)。

### 当前状态（2026-10-23）

- P1+P2：7 个 LoongArch 静态 ELF、网关/UI、18 应用商店、memos 安装实测完成。
- P3：A 机 systemd 257 下 7 unit、6 服务 active、CLI 0.4.4、安装/卸载、
  NBD 挂载/卸载/重启自挂/格式化通过。
- 真实 USB 只读测试：`LOONGSONISO` 识别、udevil ro 挂载/卸载通过；
  local-storage 白名单过滤 `usb`；读卡器桥接不支持 SMART；**未写盘、未格式化**。
- 发布闸门：**关闭**；真实盘验收前不发布 CasaOS 镜像/安装包。

### 任务

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| C-01 | 真实 SATA/USB 盘验收（仅用备用盘） | 挂载、写读、卸载、物理拔插、按 UUID 重启自挂、SMART 可读 | 待开工 |
| C-02 | 真实盘格式化/重建文件系统（仅备用盘） | 格式化后重新挂载；旧 UUID 记录不残留；数据丢失仅限测试盘 | 待开工 |
| C-03 | 24h 稳定性与升级路径 | 服务不崩；重启后 6 服务自起；应用安装/卸载正常 | 待开工 |
| C-04 | 发布闸门评审 | 决定是否发布；更新 CASAOS-P3/GAPS/README；关闭或保持闸门 | 待开工 |
| C-05 | 上游 PR/issue | 架构误判、sqlite/gopsutil、helper、格式化记录等补丁提交上游 | 待开工 |
| C-06 | 应用商店同步 | P1/P2 新镜像加入 CasaOS appstore；loong64-only 标注 | 随镜像完成 |

### 安全红线

- 只使用备用盘；不得在用户唯一数据盘上做格式化/写入测试。
- 当前插入的 `LOONGSONISO` U 盘继续保持**只读**，未获明确授权不得写盘。
- CasaOS 与 iStoreOS/OpenWrt 不能同装；生产形态装在 Debian/Loongnix 宿主。

## 7. OMV（OpenMediaVault）工作流

### 现状

OMV 尚未开工。ROADMAP 的现实判断是：SaltStack + PHP + 内核模块链，loong64 上工程量大；
3A6000 家用场景下 ksmbd + 现有方案可能已够用。因此本计划只承诺 **Gate 0 可行性调研**，
不预设移植。

### Gate 0 要回答的问题

1. **基础系统兼容性**：Loongnix 25 的 Debian 基线、glibc、systemd、apt 是否满足
   OMV 7 的要求（OMV 7 面向 Debian 12 Bookworm）。
2. **包依赖闭包**：`openmediavault` 及其依赖（PHP、nginx、SaltStack、rrdcached、
   collectd、smartmontools、mdadm、lvm2、samba、nfs）是否有 loong64 包，缺哪些。
3. **SaltStack 状态**：highstate 是否含架构假设；能否在一次性环境里跑通。
4. **插件可用性**：openmediavault-compose（应为架构无关）、ZFS 插件
   （OpenZFS 2.4.4 已在 Gate 0 验证）、KVM 插件（已封存）、sharerootfs/sftp/rsync。
5. **安装隔离**：只在备用盘/一次性 NBD/VM 中测试；不得写入生产 NAS。
6. **决策**：三种路线选一：
   - A. 完整移植 OMV 宿主包；
   - B. 只做 OMV-compose 集成，用现有 loong64 镜像；
   - C. 判定 no-go，保留 ksmbd + 现有管理方案。

### 任务

| ID | 任务 | 交付物 | 状态 |
|---|---|---|---|
| O-01 | 基线与环境审计 | `docs/OMV-FEASIBILITY.md` 初稿：OS/glibc/systemd/apt 结论 | 待开工 |
| O-02 | 依赖闭包分析 | `openmediavault` 依赖表，标注有/无 loong64 包 | 待开工 |
| O-03 | 一次性环境安装 spike | 备用盘或 NBD 上的安装日志、失败点 | 待开工 |
| O-04 | SaltStack highstate 试跑 | 失败 state 清单与补丁评估 | 待开工 |
| O-05 | 插件评估 | compose/ZFS/KVM 插件结论 | 待开工 |
| O-06 | Go/No-Go 评审 | 选定 A/B/C 路线并记录理由 | 待开工 |
| O-07 | 若 Go：移植计划 | 包清单、补丁、测试矩阵、风险 | 条件触发 |

### 安全红线

- OMV 会改网络、存储、系统服务；**禁止在生产 NAS 上直接试**。
- 只使用备用盘、NBD 或可回滚 VM；测试前做快照。
- ZFS/KVM 插件不与现有 CasaOS/固件实验混在同一台机器上。

## 8. 执行顺序与依赖

### 波次

| 波次 | 内容 | 说明 |
|---|---|---|
| Wave 1 | P1-01..P1-05 | 5 个镜像；先做依赖 spike，再连续构建 |
| Wave 2 | P2-01 Piwigo、P2-06 go2rtc、P2-03 Headscale、P2-04 Authelia、P2-05 Backrest | Ente 视照片决策放 Wave 2 末或 Wave 3 |
| Wave 3 | P2-02 Ente、P3-02..P3-06（P3-01 Komga 暂停） | 多服务与重依赖集中处理 |
| Wave 4 | P4-01..P4-09 | 按需，每项先 spike |
| 并行 | C-01..C-05、O-01..O-06 | 平台工作流不阻塞容器主线 |

### 镜像间依赖

| 应用 | 依赖的现有镜像/能力 |
|---|---|
| Zigbee2MQTT | Mosquitto、Home Assistant、USB 透传 |
| Scrutiny | 磁盘设备直通、smartctl |
| SFTPGo | 无；可选 Postgres |
| BookStack | MariaDB |
| Vikunja | 无；可选 Postgres |
| Piwigo | MariaDB |
| Ente | PostgreSQL、MinIO |
| Authelia | Nginx Proxy Manager 或 Caddy；可选 Redis |
| Backrest | 自编 restic |
| Komga | Java 17+、sqlite-jdbc loong64 native |
| Matomo | MariaDB |
| MeTube | ffmpeg、Node 24 |
| SABnzbd | par2、unrar |
| Autobrr | qBittorrent/*arr |
| Woodpecker | Gitea、docker.sock |

## 9. 每个镜像的完成定义（DoD）

新增或更新镜像必须同时完成：

1. `images/<app>/Dockerfile`、entrypoint、必要的配置模板。
2. `images/<app>/BUILD.md`：上游版本、构建链路、踩坑、运行方式、已知限制。
3. `docs/RUNBOOK.md`：启动命令、端口、挂载、环境变量、健康检查。
4. `images/catalog.json`：名称、大小、验证结论、`architecture: linux/loong64`。
5. `docs/IMAGES.md` 表格行、README/项目大纲的镜像计数。
6. `scripts/push-images.sh` 加入应用名。
7. Docker Hub 描述：`LoongArch64 only` + BUILD/RUNBOOK/catalog 链接。
8. 同时打 `loong64` 与 `24.10-la5`，用 `crane manifest` 校验单架构。
9. 冒烟测试：HTTP/API、健康检查、关键业务路径；多服务应用给 compose 示例。
10. 提交并推送 GitHub；不写入任何密钥、真实节点地址或用户数据。
11. 备份/恢复：列出数据卷、数据库 dump、密钥；至少做一次恢复演练。
12. 升级/回滚：写清停服务、备份、换镜像、迁移、回滚步骤；说明是否支持降级。
13. 可观测性：健康端点/Gatus 监控项、日志位置、资源基线（内存/CPU/磁盘）。

## 10. 明确不做

### 证据否决

- **Photoview**：CGO 依赖 dlib/go-face、ImageMagick、ffmpeg；已有 Ente/Piwigo。
- **Kavita**：`Docnet.Core` 的 PDFium、`NetVips.Native` 无 loong64，PDF/封面会坏。
- **Umami**：Prisma 7 的 `@prisma/engines` 无 loong64，迁移会失败。
- **n8n**：Sustainable Use License，不是 OSI 开源，镜像重。
- **Beszel**：与 Prometheus + Grafana + node-exporter 重叠。
- **Dockge**：与 Portainer/Dpanel 重复。
- **Docmost**：BookStack 覆盖同样需求且更轻。
- **Tandoor / Grocy**：与 Mealie/HomeBox 重叠。
- **Forgejo**：与 Gitea 重复。
- **WordPress**：与 Typecho 重叠。
- **cAdvisor**：与 Prometheus 体系重叠。
- **Healthchecks**：与 Gatus/Uptime Kuma 重叠。
- **Semaphore**：需携带 Ansible/Terraform 工具链，比 Woodpecker 重。
- **Copyparty**：与 SFTPGo/FileBrowser 重复。
- **Suwayomi**：与 LANraragi 重叠，且依赖第三方扩展。
- **ErsatzTV**：与 xteve 重叠，且 .NET + ffmpeg 较重。
- **Speedtest Tracker**：依赖闭源 Ookla CLI，仅 x86/ARM。
- **CrowdSec**：需要 `NET_ADMIN`/nftables，误配置可能锁死 NAS，适合宿主机安装。
- **ESPHome**：运行期下载各平台固件工具链，龙芯上不可控。

### 平台阻塞

- **Immich**：ONNX Runtime + VectorChord，完整版无 loong64。
- **PhotoPrism**：TensorFlow C 库 + libvips 编译期依赖。
- **Frigate**：OpenCV + TensorFlow/ONNX + Coral。
- **Ollama**：CPU 版理论可编，但 llama.cpp LoongArch 优化与模型兼容性未验证，列为实验。
- **Emby / Plex / MT Photos**：闭源，无源码。
- **UniFi**：应用闭源 + MongoDB 无 loong64。
- **PVE**：x86 虚拟化栈。
- **Ubuntu**：Kasm 镜像仅 amd64，KasmVNC 无 loong64。

## 11. 风险与决策记录

| 风险 | 影响 | 缓解 |
|---|---|---|
| 上游版本漂移 | 构建脚本/依赖 pin 失效 | 每项开工前用 `crane manifest` + release/tag 复核，BUILD.md 记精确版本 |
| 子代理证据未全部 registry 实测 | 误判可行性 | 每项先做 1 天以内 spike；Docker Hub 不可达时以源码/Dockerfile 为准 |
| 镜像构建磁盘不足 | 构建中断/镜像丢失 | 构建前保留 ≥15GB；**不要在构建进行中执行 `docker image prune -a`**；基础镜像丢失用 `crane pull` 恢复 |
| 多服务应用被当成单镜像 | 用户部署失败 | Ente/BookStack/Authelia/Woodpecker 等明确写 compose 依赖，不承诺单容器 |
| 原生模块无 loong64 | 运行期崩溃 | Komga sqlite-jdbc、Z2M serialport、Scrutiny smartctl 单独 spike |
| 许可问题 | 不能公开分发 | n8n 已排除；SABnzbd 的 unrar、Ente 等开工前复核许可证 |
| CasaOS/OMV 破坏性操作 | 用户数据丢失 | 只用备用盘/NBD/VM；USB 保持只读；测试前快照 |
| 平台工作流拖慢主线 | 镜像交付延迟 | CasaOS/OMV 与容器波次并行，不占同一台测试机 |

## 12. 进度总表

### 应用

- [ ] P1-01 Zigbee2MQTT
- [ ] P1-02 Scrutiny
- [ ] P1-03 SFTPGo
- [ ] P1-04 BookStack
- [ ] P1-05 Vikunja
- [ ] P2-01 Piwigo
- [ ] P2-02 Ente（多服务）
- [ ] P2-03 Headscale
- [ ] P2-04 Authelia
- [ ] P2-05 Backrest
- [ ] P2-06 go2rtc
- [ ] P3-01 Komga（暂停：sqlite-jdbc 无 loong64 JNI，待 spike）
- [ ] P3-02 Matomo
- [ ] P3-03 MeTube
- [ ] P3-04 SABnzbd
- [ ] P3-05 Autobrr
- [ ] P3-06 Woodpecker CI
- [ ] P4-01 MediaMTX
- [ ] P4-02 Karakeep（暂停：sharp/Chromium 无 loong64）
- [ ] P4-03 Readeck
- [ ] P4-04 Linkwarden（暂停：Prisma/Playwright/sharp）
- [ ] P4-05 Joplin Server（暂缓：sharp/sqlite-vec）
- [ ] P4-06 wg-easy（暂缓：libsql）
- [ ] P4-07 Registry
- [ ] P4-08 Pocket ID
- [ ] P4-09 Unpackerr

### 平台

- [ ] C-01 CasaOS 真实盘验收
- [ ] C-02 CasaOS 真实盘格式化/重建
- [ ] C-03 CasaOS 24h 稳定性
- [ ] C-04 CasaOS 发布闸门评审
- [ ] C-05 CasaOS 上游 PR/issue
- [ ] C-06 CasaOS 应用商店同步
- [ ] O-01 OMV 基线审计
- [ ] O-02 OMV 依赖闭包
- [ ] O-03 OMV 安装 spike
- [ ] O-04 OMV SaltStack 试跑
- [ ] O-05 OMV 插件评估
- [ ] O-06 OMV Go/No-Go
- [ ] O-07 OMV 移植计划（条件触发）
