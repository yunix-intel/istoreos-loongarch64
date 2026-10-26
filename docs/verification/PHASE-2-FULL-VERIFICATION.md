# 第二阶段完整计划：CasaOS 闸门、iStore 真机与全量功能验证

日期：2026-10-26  
状态：待批准执行  
关联：[NEXT-PLAN](../NEXT-PLAN.md)、[CASAOS-P3](../CASAOS-P3.md)、
[verify-casaos-store](../research/verify-casaos-store.md)、
[verify-istore](../research/verify-istore.md)

## 0. 目标与判定

本阶段不只验证“能安装”，而是验证三件事：

1. **CasaOS 发布闸门**：24h 稳定性、重启自启、干净安装、115 个商店定义、升级/卸载/数据保留。
2. **iStore 真机**：la5 公开版与 p1 私人版各一台（Host A U 盘启动），public/private feed 分离，商店可见、可装、可用。
3. **全量功能矩阵**：115 个应用 × 各自功能清单 × CasaOS/iStore 环境，逐项留证据；不能只写“首页 200”。

### 0.1 四个交付判定

| 判定 | 通过条件 | 失败处理 |
|---|---|---|
| **G1 CasaOS 闸门** | C-03 24h 无异常；C-04 重启后 6 个服务 + casaos.target 自起；0.1.3 包干净安装；商店 115 个可见；升级/卸载/数据保留通过 | 任一项失败即 BLOCKED，不得发布 |
| **G2 iStore 真机** | la5 与 p1 都能从自定义 feed 安装；115 个 app-meta 可见；public/private 镜像不混用；商店点击安装可用 | 固件/硬件阻塞需给出证据，不能算 PASS |
| **G3 全量功能矩阵** | 115 个应用卡全部执行；无“未解释失败”；已知限制有负向测试证据 | 未测项必须标记 NOT TESTED，不能默认通过 |
| **G4 OMV Gate 0（子代理）** | O-01/O-02/O-03 报告，含依赖闭包与 QEMU 结论 | O-04~O-09 不在本阶段 |

### 0.2 本阶段不做

- 不新做应用镜像；不重新设计商店。
- 不做 OMV O-04~O-09、不发布 OMV。
- 不把 `local/*`、LBrowser 字节或真实凭据推送到公开 registry。
- 不格式化 Host A 的 2TB SATA SSD（`/dev/sda`，已有约 525GB 用户数据）。
- 58G `LOONGSONISO` U 盘已获用户授权用于 iStoreOS 写盘；写前记录原 ISO 文件并在写后校验目标镜像。

## 1. 环境矩阵

| ID | 硬件/系统 | 商店/镜像 | 用途 |
|---|---|---|---|
| **E0** | Host A，Loongnix 25，内部 NVMe，CasaOS P3 | CasaOS public 115 个定义 + `yunixintel/*:24.10-la5` | CasaOS 公开版全量矩阵 |
| **E1** | Host A，同上 | CasaOS private overlay（`store/casaos-private`）+ `local/*` | CasaOS 私人版功能（Linkwarden/Karakeep） |
| **E2** | Host A 从 U 盘启动 iStoreOS **la5 公开版** | public feed 115 个 app-meta；public 镜像 | iStore 公开版真机 + 全量矩阵 |
| **E3** | Host A 从 U 盘启动 iStoreOS **p1 私人版** | private feed 115 个 app-meta；Linkwarden/Karakeep 用 `local/*` | iStore 私人版真机 + 全量矩阵 |
| **E4** | 独立浏览器主机（Windows 本机） | 访问 E0/E2/E3 的 Web UI | UI 截图、LuCI/CasaOS 商店点击回归 |
| **E5** | B 机 `172.16.100.66` 的 `/dev/sdb`（476.9G）或 QEMU 干净 rootfs | CasaOS 0.1.3-store115 包 | S-C4 干净安装；sdb 上的 `rpool`/LoongNAS Gate 0 测试环境会被清除，sda 不动 |

> E5 的硬件已由用户指定为 B 机 sdb；但仍需 **Loongnix 25 安装 ISO**（A/B 当前都没有，
> 计划从官方镜像下载并校验 SHA256）。sdb3 当前是 `rpool`/LoongNAS Gate 0 测试环境，
> 使用前会再次确认可丢弃；sda 是 B 机系统盘，绝不触碰。若拿不到安装 ISO，S-C4 只能判
> PARTIAL/NOT TESTED，不能拿 Host A 的“已装环境”冒充干净安装。

## 2. 版本矩阵：先固化，再测试

### 2.0 已知基线（执行时逐项复核）

| 项 | 公开版 | 私人版 / 测试机 |
|---|---|---|
| 固件 | iStoreOS `24.10-la5`，基线 `24.10.8 r0-fb97140` | `personal-p1-20261019`，同基线 + 私人预置 |
| 镜像文件 | GitHub Release `img.gz` + `sha256sums` | `/build/firmware/personal-p1-20261019.img.gz`（381MB） |
| Host A 系统 | Loongnix GNU/Linux 25 | 内核 `6.6.52-loong64`，页大小 16384 |
| CasaOS 包 | `0.1.3-store115`（sha256 `7262d39c…50426`） | `0.1.2-appmgr410` 作为 soak/回退基线 |
| CasaOS 组件 | casaos `v0.4.15`、gateway `v0.4.9-alpha4`、message-bus `v0.4.4-3-alpha2`、user-service `v0.4.8`、app-management `v0.4.10-alpha2`、local-storage `v0.4.4`、CLI `v0.4.4-3-alpha1`、UI `v0.4.25`、AppStore `v0.4.5` | 同左 |
| Host A 容器运行时 | Docker `26.1.5+dfsg1`、API 1.45、containerd `1.7.24`、runc `1.1.15` | iStoreOS 版本以刷机后实测为准 |
| 应用镜像 | 115 个 app + `node`/`node-sharp`/`lbrowser-runtime` | Linkwarden/Karakeep 额外 `local/*` |

> 这张表是“预期基线”，不是“已证明”。执行时由 `collect_versions.sh` 采集实际值，
> 差异写入 VERSION-MATRIX，不能直接抄本表当验收结果。

### 2.1 必须采集的版本

| 层 | 字段 | 采集方式 |
|---|---|---|
| 固件 | la5/p1 镜像 SHA256、`version.buildinfo`、`/etc/openwrt_release`、kernel、Docker/Podman | 刷机后 SSH/串口采集 |
| Host A | `os-release`、`uname -a`、glibc、systemd、页大小、CPU/内存 | `scripts/phase2/collect_versions.sh` |
| CasaOS | casaos v0.4.15、gateway v0.4.9-alpha4、message-bus v0.4.4-3-alpha2、user-service v0.4.8、app-management v0.4.10-alpha2、local-storage v0.4.4、CLI v0.4.4-3-alpha1、UI v0.4.25、AppStore v0.4.5 | 包内 `docs/DEPENDENCIES.md` + 二进制 SHA256 + `/opt/casaos-p3/VERSION` |
| 容器运行时 | Docker、containerd、runc、Podman/crun/conmon/netavark | `docker version`、`containerd --version`、`podman version` |
| 应用镜像 | 115 个 app + `node`/`node-sharp`/`lbrowser-runtime`，repo digest、架构、大小、label | `docker image inspect` + `crane config` |
| Sidecar | PostgreSQL 15.18、MariaDB 10.x、Redis 7.2.14、MinIO release、LBrowser 3.4.2293.2、Node 24.22.1 | 镜像内 `--version` / label |
| 商店 | CasaOS 定义 115、iStore app-meta 115+1、feed SHA256 | `validate_definitions.py`、`validate.py` |

### 2.2 版本一致性的硬规则

- 每个应用定义里的 `image` tag 必须是 `24.10-la5` 或明确允许的 `loong64`；
  私人定义必须是 `local/*`。
- `catalog.json`、`store/loong64-descriptions.json`、CasaOS 定义、iStore app-meta
  四处的应用集合必须完全一致（115）。
- 镜像 digest 与 `catalog.json`/`BUILDLOG.md` 不一致时，先查是否重新推送过；
  以 `docker image inspect` 的实际 digest 为准，并回写文档。
- 固件 `la5` 与 p1 的 `version.buildinfo` 必须记录；p1 必须证明“同一基线 +
  私人预置”，不得混入公开镜像或凭据。

### 2.3 产物

- `docs/verification/VERSION-MATRIX.md`：预期值、实际值、差异、结论。
- `docs/verification/VERSION-MATRIX.json`：机读版，供测试脚本做前置检查。
- `docs/verification/evidence/<env>/versions/`：原始命令输出。

## 3. 判定、证据与红线

### 3.1 单项判定

| 判定 | 含义 |
|---|---|
| **PASS** | 有命令/截图/日志证据，结果与预期一致 |
| **PARTIAL** | 主路径通过，但明确列出未覆盖功能或环境限制 |
| **BLOCKED** | 上游/硬件/依赖阻塞，附复现命令与根因 |
| **NOT TESTED** | 没跑；必须写原因，不能算通过 |

### 3.2 红线

1. 不能把“首页 200”写成“功能全通过”。
2. 不能把“dry-run 通过”写成“真机安装通过”。
3. 不能把“手动点击成功一次”写成“全部功能回归”。
4. 未验证的已知限制必须做负向测试（例如 Karakeep 未配 Meilisearch 应返回 500），
   不能只抄描述。
5. 私人版测试不得使用公开镜像替代 `local/*`；公开版测试不得出现 `local/*`。
6. 任何测试数据/密码不得进 Git；测试账号统一放 `/build/verify-secrets`（0600）。

### 3.3 证据目录

```text
docs/verification/
  PHASE-2-FULL-VERIFICATION.md   # 本计划
  VERSION-MATRIX.md / .json
  cards/<app>.yaml               # 115 个测试卡
  results/<env>/<app>.json       # 机读结果
  reports/PHASE-2-FINAL.md       # 最终报告
  evidence/<env>/<app>/          # 关键截图、HTTP 头、日志摘录
```

原始大日志放 `/build/verify-evidence/`，仓库只放摘要与关键证据，避免仓库膨胀。

## 4. 测试卡：把“所有功能”变成可执行清单

### 4.1 每张卡的结构

```yaml
id: joplin-server
title: Joplin Server
image: yunixintel/joplin-server:24.10-la5
upstream_version: 3.7.21
dependencies: [postgres]
ports: [22300]
volumes:
  - /data
accounts:
  admin: {user: admin@localhost, secret_ref: joplin_admin}
checks:
  - id: install
    type: install
    expect: running
  - id: ping
    type: http
    path: /api/ping
    expect_status: 200
    expect_body: '"status":"ok"'
  - id: admin_login
    type: http
    method: POST
    path: /api/login
    body: {email: admin@localhost, password: "${secret:joplin_admin}"}
    expect_status: 200
  - id: create_note
    type: http
    method: POST
    path: /api/items/root:/...
    expect_status: 200
  - id: share_page
    type: http
    path: /shares/...
    expect_status: 200
  - id: restart_persistence
    type: restart
    then: [ping, admin_login]
  - id: known_limit_sqlite_vec
    type: log
    expect_contains: "vector search disabled"
  - id: uninstall_keep_data
    type: uninstall
    expect: data_dir_exists
```

### 4.2 功能覆盖来源

每个应用按以下顺序建立清单，避免“拍脑袋”：

1. 上游官方文档的功能菜单/API 文档；
2. 镜像 `BUILD.md` 的已验证项与限制；
3. CasaOS/iStore 卡片描述里的“缺失功能/额外依赖”；
4. 实际 UI 路由/README 功能列表；
5. 本阶段新增的集成场景（数据库、S3、SMTP、OIDC、*arr、浏览器）。

每张卡必须有 `feature_inventory` 字段，列出“本次覆盖”和“明确不覆盖”，
并在 `results` 里引用证据。

### 4.3 分类重点

| 分类 | 数量 | 重点检查 |
|---|---:|---|
| Media | 17 | 库扫描、元数据、播放/转码限制、字幕、权限 |
| Developer | 18 | 仓库/CI、Webhook、数据库迁移、代码浏览、插件 |
| Productivity | 15 | 注册登录、CRUD、分享、导入导出、附件、全文搜索 |
| Utilities | 17 | 安装/健康、配置持久化、API、限流/认证 |
| Networking | 11 | 反代、DNS、端口冲突、TLS、host 网络 |
| Downloaders | 10 | 下载器连接、队列、路径映射、完成通知 |
| Cloud | 9 | 对象存储、S3 API、bucket、权限、数据持久化 |
| Monitoring | 9 | 指标、告警规则、数据源、历史保留 |
| Backup | 3 | 仓库创建、快照、恢复、调度、权限 |
| Home Automation | 3 | 设备发现、MQTT、USB 直通、配对 |
| Security | 3 | 登录、TOTP/WebAuthn、forward-auth、密钥持久化 |

### 4.4 25 个 manual 应用

`store/istore/validate.py` 标出的 25 个应用不跳过，而是用“前置条件 + 可执行部分”：

- 需要 forge/外部服务的：Woodpecker、Authelia、Headscale、Pocket ID、Ente；
- 需要设备的：Zigbee2MQTT、Scrutiny、smartctl-exporter、wg-easy；
- 需要首次 Web 向导的：Matomo、BookStack、Piwigo、Typecho、Wallabag、phpMyAdmin；
- 需要 host 网络的：Pi-hole、AdGuard Home、mihomo、easytier、go2rtc、MediaMTX；
- 需要外部路径的：Unpackerr、Backrest、Kopia、WebVirtCloud、rest-server。

对每项写清：`前置条件`、`可自动验证部分`、`必须人工/设备的部分`、`未测原因`。

## 4.5 平台功能矩阵（CasaOS / iStoreOS）

应用测试不能替代平台测试。平台侧按“模块 × 功能 × 失败路径”逐项验收，公开版与
私人版分别执行。

### CasaOS（E0/E1）

| 模块 | 必测功能 | 方法 |
|---|---|---|
| 认证/用户 | 首次管理员、登录/登出、token、用户增删改、普通用户权限；LAN 直接访问 UserService 必须 403；伪造 `X-Forwarded-For`/`X-Real-IP` 不得绕过 | API + 浏览器 + 负向 curl |
| 应用商店 | 115 个列表、分类、图标、搜索、详情、龙芯版说明、安装/升级/卸载、端口/卷/env 编辑、日志、终端 | UI + `/v2/app_management/*` |
| 应用管理 | dry-run、端口冲突、sidecar 健康、启动/停止/重启、compose 解析、安装异步状态、失败回滚 | API + 容器状态 |
| 本地存储 | 磁盘/分区列表、挂载/卸载、格式化确认与密码、白名单（只允许 `/dev/sdX` 整盘）、USB 只读、SMART、`/DATA` 持久化 | local-storage API + 真实盘/空盘；不碰 2TB 数据盘 |
| 文件/共享 | 文件浏览/上传/下载/重命名/删除、Samba/NFS 共享、权限 | UI + `smbclient`/`showmount` |
| 系统 | 仪表盘、CPU/内存/磁盘/网络、事件/通知、设置、电源/重启、版本信息 | UI + API |
| 事件总线 | message-bus 事件投递、AppManagement HTTP-only（不再依赖 `/tmp/message-bus.sock`）、断线重连 | 事件订阅 + 日志 |
| 安全 | 未授权格式化、未授权用户创建、容器逃逸面、docker.sock 应用白名单 | 负向测试 |
| 升级/回滚 | P3 0.1.2 → 0.1.3 升级、配置保留、卸载残留、回滚到备份 | 包升级 + 备份恢复 |

### iStoreOS（E2/E3）

| 模块 | 必测功能 | 方法 |
|---|---|---|
| 固件 | la5/p1 版本、`version.buildinfo`、kernel、页大小、启动日志 | SSH/串口 |
| 网络 | WAN/LAN、DHCP、DNS、防火墙、端口转发；host 网络应用 53/80/8123 冲突检查 | LuCI + `uci` + `ss` |
| 包管理 | `opkg update/install/remove`、自定义 feed、签名开关、依赖解析 | SSH |
| 容器运行时 | dockerd/containerd/runc、podman/crun/conmon/netavark 版本与基本运行 | `docker run`/`podman run` |
| 存储 | 磁盘/分区、挂载、共享、`/srv` 数据目录、USB | LuCI + `lsblk`/`mount` |
| iStore 商店 | 115 卡片、分类、图标、详情、安装/升级/卸载、日志、端口/卷展示 | LuCI + `/usr/libexec/istorec/*.sh` |
| app-meta | `opkg install app-meta-*`、JSON/runtime/conf 一致性、sidecar 启动顺序 | SSH + 解包 |
| 系统 | 用户/密码、终端、日志、备份、重启、sysupgrade（有条件） | LuCI + SSH |
| 公私隔离 | public feed 无 `local/*`；p1 私人预置/镜像/源不进入公开版 | grep + 安装验证 |

### 平台测试的判定

- 平台功能失败时，应用矩阵暂停，先修平台；否则会把平台问题误记成“应用问题”。
- CasaOS 的 local-storage 测试必须区分“空盘”和“2TB 数据盘”；后者只读，
  不允许格式化/写测试。
- iStoreOS 的 sysupgrade 只在有第二块可回退介质时做；否则标 NOT TESTED。

## 5. 阶段 A：CasaOS 闸门（G1）

### A0. 冻结与备份（执行前 30 分钟）

```bash
# Host A
sudo tar czf /build/backup-casaos-p3-$(date +%F).tar.gz \
  /opt/casaos-p3/conf /opt/casaos-p3/apps /opt/casaos-p3/appstore /opt/casaos-p3/data
sha256sum /build/backup-casaos-p3-*.tar.gz
```

- 记录 `/opt/casaos-p3/VERSION`、各二进制 SHA256、systemd unit 列表。
- 确认 2TB `/dev/sda` 不参与任何格式化/挂载写测试。

### A1. C-03 24h soak 分析（2026-10-26 21:06 后）

- 等待 `/tmp/casaos-soak-24h.csv` 达到 1440 个采样点（6 服务 × 1440 行）。
- 统计每个服务：alive 比例、HTTP 码分布、PID 是否变化、RSS 首末/峰值。
- 预期：gateway/message-bus/user-service/app-management/casaos 全 200；
  local-storage 401 是未带认证的预期值，需与基线对比，不能直接当失败。
- 产物：`docs/verification/reports/C03-SOAK.md`。

### A2. 商店 UI 115 个（S-C6 / C-06）

```bash
kill "$(cat /opt/casaos-p3/run/app-management.pid)"
sleep 2
/opt/casaos-p3/scripts/start.sh
curl -s http://127.0.0.1:8081/v2/app_management/apps \
  | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["data"]["list"]))'
```

- 预期 115；若仍 18，检查 `/opt/casaos-p3/appstore/default/Apps` 是否有 115 个
  compose、日志是否有 parse error。
- 浏览器打开 CasaOS UI，验证分类、图标、卡片“龙芯版说明”、搜索、详情页。

### A3. C-04 重启与 systemd 自启

- 记录当前 PID/端口；`sync` 后 `systemctl reboot`。
- 重启后检查：
  - `systemctl is-active casaos.target` 及 6 个服务 unit；
  - 8081/14500 等端口；
  - `/DATA` 挂载；
  - AppManagement API 返回 115；
  - 安装/卸载一个代表性应用（joplin-server 或 gatus）。
- 若 systemd 未自起，回退到 `scripts/start.sh` 并记录 BLOCKED 证据。

### A4. S-C4 干净安装（E5）

- 在 B 机 `/dev/sdb` 安装 Loongnix 25（需官方 ISO，A/B 当前都没有；sda 不动），
  或 QEMU TCG 干净 rootfs。
- 安装前备份 B 机 sdb 上需要保留的 LoongNAS 产物；`rpool`/Gate 0 测试环境按用户
  授权可清除。
- 安装 `casaos-p3-loong64-0.1.3-store115.tar.gz`，sha256
  `7262d39c…50426`。
- 验收：安装后 AppManagement 直接返回 115；无手工复制定义；商店可安装至少
  5 个不同类别应用；重启后仍 115。
- 没有安装 ISO 或介质时标 PARTIAL/NOT TESTED，不能拿 Host A 冒充。

### A5. S-C5 升级/卸载/数据保留

- 选 6 个代表性应用：单容器、PostgreSQL、MariaDB、对象存储、host 网络、设备类。
- 流程：安装 → 写测试数据 → 重启 → 升级镜像（同 tag 重建）→ 数据仍在 →
  卸载 → 数据目录保留 → 重装 → 数据仍在。
- 记录 CasaOS 卸载是否删除 `/DATA/AppData/<id>`；若删除，写清策略。

### A6. C-05 上游 PR/issue（非闸门）

- 整理 6 类补丁：架构误判、sqlite/gopsutil、helper、格式化记录、消息总线、
  AppManagement socket。
- 先做 issue/PR 清单，不阻塞 G1。

## 6. 阶段 B：CasaOS 全量功能矩阵（E0/E1）

### B1. 执行顺序

1. 基础层：node、node-sharp、lbrowser-runtime 版本与依赖；
2. 数据库/缓存/对象存储：postgres、mariadb、redis、minio；
3. 单容器工具类：先跑 40 个低风险应用；
4. 多服务应用：joplin、linkwarden、bookstack、matomo、penpot、ente、paperless；
5. 设备/网络类：wg-easy、pihole、adguardhome、zigbee2mqtt、scrutiny；
6. 私人 overlay：Linkwarden/Karakeep。

### B2. 单应用流程

```text
安装 → 健康 → 首启/认证 → 功能清单逐项 → 重启持久化
→ 升级 → 卸载（保留数据）→ 重装 → 数据验证 → 清理
```

每步写 `results/<env>/<app>.json`，失败立即停止该应用并记录，不继续“猜”。

### B3. 并发与资源

- 同时最多 2 个应用（数据库类独占）。
- 每应用结束清理容器/临时数据；`/var` 与 `/build` 低于 2GB 时暂停。
- 测试数据目录优先 `/build/verify-data`；空间不足时申请使用
  `/mnt/Data/istore-verify`（2TB 盘上的独立目录，绝不格式化）。

## 7. 阶段 C：iStoreOS la5 公开版真机（G2 / E2）

### C0. 前置

- 使用已授权的 58G `LOONGSONISO` U 盘；写前用 `lsblk -o NAME,SIZE,SERIAL,MODEL`
  确认设备，记录原 ISO 文件名；写盘会清空该 U 盘。
- 从 GitHub Release 下载 la5 `img.gz` 与 `sha256sums`，校验 SHA256。
- 另一台机器（Windows）作为 HTTP feed 服务器与测试控制端。
- Docker Hub 已实测可匿名拉取（`joplin-server`/`linkding`/`postgres` 等 manifest 200），
  无需登录。注意 `lbrowser-runtime` 只有 `loong64`/`3.4.2293.2`，没有 `24.10-la5`；
  `node-sharp` 只有 `loong64`/`24.22.1`。

### C1. 写盘与启动

```bash
# 在 Linux 上，确认 /dev/sdX 是目标 U 盘后再执行
sudo dd if=istoreos-...img.gz of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

- Host A 断电/重启，F7/F11 选 U 盘；不修改内部 NVMe。
- 启动后记录 IP（DHCP/串口/LuCI），SSH 开启。
- 采集固件版本：`cat /etc/openwrt_release`、`uname -a`、`docker version`。

### C2. feed 部署

```bash
# Windows，仓库根目录
python -m http.server 8000 --directory store/istore/feed
# 设备上 /etc/opkg/customfeeds.conf：
src/gz istore-loong64-meta http://192.168.8.<PC>:8000/public/all/meta
src/gz istore-loong64-luci http://192.168.8.<PC>:8000/public/all/nas_luci
option check_signature 0
```

```sh
opkg update
opkg install luci-app-istore-loong64
opkg install app-meta-joplin-server
/usr/libexec/istorec/joplin-server.sh install
```

### C3. 公开版全量矩阵

- 先验证商店 UI 能看到 115 个卡片、描述、分类、图标。
- 按第 6 节同样流程跑 115 个应用；iStore 侧用 `opkg install app-meta-<id>` +
  `/usr/libexec/istorec/<id>.sh install`。
- 重点验证：public feed 不含 `local/*`；Linkwarden/Karakeep 的 LBrowser sidecar
  需要 `/opt/apps/lbrowser`，没有则必须报 BLOCKED 而不是假 PASS。
- 重启后验证容器自启、数据保留、商店仍可用。

### C4. 恢复 Host A

- 关机，拔 U 盘，内部 NVMe 启动；确认 CasaOS 无损、soak 数据仍在。
- 记录 iStore 测试期间的网络/IP/端口，避免与 CasaOS 冲突。

## 8. 阶段 D：iStoreOS p1 私人版真机（G2 / E3）

### D0. 私人镜像预载

```bash
# Host A，内部系统启动时
docker save local/linkwarden-private:2.16.3-p1 \
            local/karakeep-private:0.34.1-p1 \
  -o /build/private-images.tar
sha256sum /build/private-images.tar
```

- 把 tar 放到 p1 U 盘的数据分区或通过局域网传输；**不推 Hub**。
- p1 启动后 `docker load -i private-images.tar`，确认两个 image 存在。

### D1. private feed

- 使用 `feed/private`，`isfeeds.conf` 指向 private 目录。
- 验证 Linkwarden/Karakeep 的 app-meta `default_variant=private`，
  渲染/安装命令引用 `local/*`，且不出现 LBrowser sidecar。
- 其余 113 个应用允许使用公开镜像，但 store URL 指向私人源。

### D2. 私人版全量矩阵

- 115 个应用同样跑；Linkwarden/Karakeep 重点验证内置浏览器：
  注册/登录、书签/归档、截图、PDF、重启持久化、无宿主挂载。
- 公共镜像应用按公开矩阵执行；不得因为“私人版”跳过。

### D3. 隔离审计

```bash
grep -R "local/" store/istore/feed/public || echo public-clean
grep -R "yunixintel/.*24.10-la5" store/istore/feed/private
grep -R "dckr_pat\|password\|secret" store/istore/feed || true
```

- public feed 不得含 `local/*`/私人 URL/凭据；
- private feed 不得含真实 token、节点地址、用户密码。

## 9. 阶段 E：全量功能矩阵的统一执行

### E1. 115 张卡生成

- 从 `store/loong64-descriptions.json` 自动生成基础卡；
- 人工补 25 个 manual 应用的前置条件；
- 从 `docs/LOONG64-QUIRKS.md` 自动注入“已知限制”负向检查；
- 所有卡必须通过 `verify/phase2/validate_cards.py`（字段齐全、引用存在）。

### E2. 执行批次

| 批次 | 应用数 | 内容 |
|---|---:|---|
| B0 | 3 | 基础层 + DB/缓存/对象存储 |
| B1 | 40 | 单容器工具类、低风险 |
| B2 | 30 | 媒体/下载/网络 |
| B3 | 20 | 多服务/数据库/浏览器 |
| B4 | 15 | 设备/安全/manual |
| B5 | 7 | 私人 overlay + 复测 |

每批结束出 `reports/BATCH-Bn.md`；失败项不跨批重试，先定位。

### E3. “所有功能”的量化口径

- 每个应用至少覆盖：安装、健康、首启/认证、3 个核心功能、持久化、重启、
  升级、卸载/数据保留、已知限制；
- UI 类应用至少抓 2 张关键页面截图（登录后首页 + 核心功能页）；
- API 类应用至少验证 3 个端点；
- 集成类应用验证 1 条真实集成路径；
- 不覆盖项必须在卡片 `not_covered` 写明原因，最终报告汇总。

## 10. 阶段 F：OMV 子代理（O-01~O-03）

### F1. 范围

- O-01：目标版本与基线审计（OMV 7/bookworm vs 8/trixie，loong64 依赖）。
- O-02：依赖闭包（arch:all vs binary-loong64，禁止直接加 bookworm 源）。
- O-03：QEMU TCG loong64 安装 spike，不碰 Host A 内部盘、不碰 CasaOS。
- O-04~O-09 不在本阶段。

### F2. 约束

- 只用 Host A `/build/omv-gate0` 与 QEMU；不改 `/opt/casaos-p3`。
- 资源与 CasaOS/iStore 测试错峰；QEMU 跑之前检查内存/磁盘。
- 产物：`docs/research/omv-gate0-{baseline,deps,qemu}.md` + 原始日志路径。
- 结论必须给“可行/不可行/证据不足”，不能给无证据的乐观结论。

## 11. 时间表（估算）

| 时间 | 工作 | 产出 |
|---|---|---|
| D0 | 计划批准；生成测试卡/版本脚本；备份 | 计划、卡片骨架、版本矩阵脚本 |
| D1 21:06 后 | C-03 soak 分析；A2 商店 115；A3 重启 | C03 报告、G1 初步 |
| D2 | A4/A5 干净安装、升级/卸载；CasaOS 批次 B0-B2 | G1 结论、批次报告 |
| D3-D5 | CasaOS B3-B5 全量矩阵 | CasaOS 全量报告 |
| D6 | 准备 la5 U 盘/feed；E2 启动 | iStore la5 基线 |
| D7-D9 | la5 115 应用矩阵、重启/升级 | la5 报告 |
| D10 | 准备 p1/私人镜像；E3 启动 | p1 基线 |
| D11-D12 | p1 115 应用矩阵、隔离审计 | p1 报告 |
| D13-D14 | 汇总、复测失败项、最终报告 | G2/G3 结论 |
| 并行 | OMV O-01~O-03 子代理 | OMV 报告 |

实际日历取决于：USB 启动是否顺利、B 机 Loongnix 安装 ISO 是否可得、
25 个 manual 应用的外部依赖是否可用。失败项按“阻塞证据”处理，不无限重试。

## 12. 风险与回退

| 风险 | 影响 | 处理 |
|---|---|---|
| Host A U 盘启动失败/无显示 | iStore 真机阻塞 | iKVM/显示器；改 QEMU 仅作补充，不冒充真机 |
| Docker Hub 镜像 tag 不全 | 基础层/浏览器镜像拉取失败 | 按 `lbrowser-runtime:3.4.2293.2`、`node-sharp:24.22.1` 使用；版本矩阵列出实际 tag |
| `/var`、`/build` 空间不足 | 测试中断 | 每应用清理；申请 `/mnt/Data` 独立目录；不格式化 2TB 盘 |
| 25 个 manual 应用缺外部服务 | 无法全通过 | 标 PARTIAL/BLOCKED，附前置条件与证据 |
| 私人镜像误入公开 feed | 隐私/合规事故 | 每次 build 后跑隔离审计；发现即阻断发布 |
| OMV QEMU 抢占资源 | CasaOS/iStore 测试变慢 | 错峰；限制 QEMU CPU/内存 |
| 测试数据/密码进 Git | 安全事故 | `.gitignore`、`/build/verify-secrets`、提交前 secret 扫描 |

## 13. 交付物

1. 本计划 + 执行日志。
2. `docs/verification/VERSION-MATRIX.md` 与 JSON。
3. 115 张测试卡 + 运行器 + 结果 JSON。
4. CasaOS G1 报告：C-03/C-04/S-C4/S-C5/C-06。
5. iStore la5 G2 报告、p1 G2 报告、隔离审计。
6. 全量功能矩阵报告（按分类/按应用/失败清单）。
7. OMV O-01~O-03 报告。
8. 更新 `NEXT-PLAN`、`GAPS`、`CASAOS-P3`、`verify-*`，最终 commit。

## 14. 批准后第一批动作

1. 生成 `verify/phase2/` 骨架、版本采集脚本、115 张卡的基础版。
2. 等 21:06 soak 结束，执行 A1/A2/A3；失败即停。
3. 启动 OMV 子代理做 O-01/O-02（只读），O-03 QEMU 错峰。
4. 备份 Host A、确认 USB 设备与 la5 镜像 SHA256。
5. 按 D1-D5 推进 CasaOS 全量矩阵，再进 iStore。
