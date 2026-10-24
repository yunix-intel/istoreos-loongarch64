# P1–P4 应用与平台详细设计（28 个工作项）

制定日期：2026-10-23  
状态：**设计稿，未开工**。所有版本号、依赖和行为在开工前都要用上游源码与最小构建 spike 复核。  
对应计划：[NEXT-PLAN.md](NEXT-PLAN.md)。现有镜像：[IMAGES.md](IMAGES.md)。

本文件回答“每个工作项具体怎么造”：26 个应用镜像 + CasaOS + OMV，共 **28 个工作项**。
它不替代 `images/<app>/BUILD.md`（构建完成后的事实记录）。
商店接入（CasaOS 私人商店 / iStore 私人版 p1 / 公开版 la5）不在逐应用设计中展开，
统一放到所有应用完成后的 [NEXT-PLAN.md](NEXT-PLAN.md) §9.5。

---

## 0. 统一设计约定

### 0.1 基础镜像

| 用途 | 基础镜像 | 说明 |
|---|---|---|
| 原生服务（Go/Rust/C/PHP） | `openeuler/openeuler:24.03` | glibc 2.38；仓库现有默认 |
| Node 应用 | `yunixintel/node:24.22.1` | 已内置 Node 24 + npm；**该基础镜像不含 curl**，每个 Node 应用必须在自己的 Dockerfile 里显式安装 `curl` 或改用 `wget`/Node 健康检查 |
| Java 应用 | `openeuler/openeuler:24.03` + `java-21-openjdk-headless` | JDK 21 已验证可跑 Java 21 字节码 |
| Python 3.11 应用 | `openeuler/openeuler:24.03` + `python3` | openEuler 自带 3.11 |
| Python 3.14 应用 | 复用 Mealie 的 3.14.8 前缀或重新编 | 仅 Hermes 这类硬要求 3.14 的应用 |
| PHP 应用 | `openeuler/openeuler:24.03` + PHP 8.3 + nginx/php-fpm | 复用 nextcloud/typecho 的既有模式 |

> 所有运行时镜像都必须显式安装健康检查/排障所需的 `curl`（或 `wget`）、`ca-certificates`、`tzdata`。`openeuler:24.03` 最小镜像不保证带 curl；`yunixintel/node:24.22.1` 已确认不带 curl。

### 0.2 命名与标签

- 仓库：`yunixintel/<app>`
- 固定标签：`loong64`、`24.10-la5`
- 建议额外打精确版本标签（如 `2.14.2`），便于回滚；是否公开由发布时决定。
- 所有镜像必须 `linux/loong64` 单架构，构建后用 `crane manifest` 校验。
- OCI labels：`org.opencontainers.image.source`、`.version`、`.licenses`、`.title`。

### 0.3 用户、UID 与权限

每个应用分配固定 UID/GID，写入 RUNBOOK；不默认用 root 跑业务进程。新应用使用 **1101–1123** 段，避开仓库已有的 33、472、911、995、998、1000、1001、1002、1026、6553、9001。

| 应用 | UID/GID | 说明 |
|---|---|---|
| Zigbee2MQTT | 1101 | 需 `dialout` 组 |
| Scrutiny | 1102 | 需设备权限 |
| SFTPGo | 1103 | |
| BookStack | 33 | www-data，PHP-FPM |
| Vikunja | 1104 | |
| Piwigo | 33 | www-data，PHP-FPM |
| Ente server/web | 1105 | 两个镜像同 UID |
| Headscale | 1106 | |
| Authelia | 1107 | |
| Backrest | 1108 | |
| go2rtc | 1109 | |
| Komga | 1110 | |
| Matomo | 33 | www-data，PHP-FPM |
| MeTube | 1111 | |
| SABnzbd | 1112 | |
| Autobrr | 1113 | |
| Woodpecker server/agent | 1114 | 两个镜像同 UID |
| MediaMTX | 1115 | |
| Karakeep | 1116 | |
| Readeck | 1117 | |
| Linkwarden | 1118 | |
| Joplin Server | 1119 | |
| wg-easy | 1120 | 需 `NET_ADMIN` |
| Registry | 1121 | |
| Pocket ID | 1122 | |
| Unpackerr | 1123 | |

规则：

- 需要写卷的目录在 entrypoint 启动时 `chown`，但只 chown 明确的数据目录。
- **entrypoint 必须以 root 启动，再用 `runuser`/`gosu` 降权**；直接 `--user` 会因无法 chown 失败。
- 对媒体库/下载目录只做顶层 `install -d -o UID -g GID`，**不做递归 chown**，避免误改用户已有文件。
- 需要设备权限的应用（Zigbee、Scrutiny）通过 `--device` / `--group-add` 解决，不默认 `--privileged`。
- 仅 wg-easy 需要 `NET_ADMIN`；Woodpecker agent 需要 `docker.sock`；其余不给额外 capability。

### 0.4 运行时契约

- 时区默认 `TZ=Asia/Shanghai`。
- 日志走 stdout/stderr；应用强制写文件的，日志目录挂卷或软链到 stdout。
- 每个镜像必须有 `HEALTHCHECK`，优先使用应用自身健康端点；没有端点的用首页 200。无 HTTP 端点的（Unpackerr）用 `pgrep` 并安装 `procps-ng`，并在 RUNBOOK 说明。
- 所有运行时镜像显式安装 `curl`（或 `wget`）用于健康检查；不假设基础镜像自带。
- 每个镜像声明 `VOLUME`，但文档同时给出显式 `-v` 示例。
- **禁止把单个文件路径声明为 VOLUME**（如 `.env`、`config.php`）。命名卷不支持文件；绑定挂载会把不存在的文件创建成目录，遮蔽真实配置。配置文件应由 entrypoint 从环境变量生成到容器可写层或目录卷内。
- 首次启动逻辑放 entrypoint：生成配置、生成密钥、等待数据库、执行迁移，然后 `exec` 主进程。
- **生成的密钥必须持久化**到数据卷（如 `/config`、`/db`、`/secrets`），权限 0600；不得每次启动重新生成，否则会话/加密数据会失效。
- entrypoint 必须处理 SIGTERM，不吞信号；多进程应用用 `wait -n` + trap 清理，以 root 启动后 `runuser` 降权。

### 0.5 构建上下文

- 仓库不提交大体积源码与前端产物；`images/<app>/` 只放 Dockerfile、entrypoint、配置模板、少量静态文件。
- 前端在 x86 WSL2 构建时，记录 Node/pnpm 版本、命令和产物目录；`dist/` 与架构无关。
- 源码版本在 BUILD.md 记录 tag + commit + sha256；构建脚本不依赖浮动 `latest`。
- 需要代理的构建（GitHub、npm、Go modules）统一走 `http://127.0.0.1:17890`，不写入镜像。

### 0.6 多服务应用

- Penpot、Ente、BookStack、Authelia、Woodpecker 等不是单容器应用；设计里明确列出依赖服务与 compose 示例。
- 不把“需要 PostgreSQL/Redis/S3”的应用伪装成单镜像；catalog 的 notes 必须写明。
- 依赖服务优先复用已发布镜像：`postgres`、`redis`、`mariadb`、`minio`、`nginx-proxy-manager`、`gitea`。

### 0.7 安全底线与默认认证

- 镜像不内置任何真实密钥、token、节点地址、用户数据。
- 默认监听容器内端口；对外发布由用户显式 `-p`。
- 默认无认证的应用必须在 RUNBOOK 标注“仅限可信内网”，公网必须加反代认证。
- 有命令执行/文件访问能力的面板默认只绑定回环地址，或强制由反代加认证。
- 需要宿主设备的应用写清设备路径和权限，不默认 privileged。

| 应用 | 默认认证 | 处理 |
|---|---|---|
| Zigbee2MQTT | 无 | RUNBOOK 写“仅内网”；反代加认证 |
| Scrutiny | 无 | 仅内网；反代加认证 |
| SFTPGo | 有（Web/SFTP） | 首次启动生成管理员密码；强制首登修改 |
| BookStack | 有 | 管理员账号首启创建 |
| Vikunja | 有 | 关闭公开注册或管理员审核 |
| Piwigo | 有 | 安装向导创建管理员 |
| Ente | 有 | 端到端加密；密钥必须持久化 |
| Headscale | API key/CLI | 无 Web UI；私钥不入镜像 |
| Authelia | 有 | 门户 + forward-auth；密钥文件 0600 |
| Backrest | 需显式启用 | 默认要求 Basic 认证；仓库凭据在卷内 |
| go2rtc | 无 | **Web/API 默认只绑 127.0.0.1**；`exec:` 源等于命令执行 |
| Komga | 有 | 首启管理员；库权限 |
| Matomo | 有 | 安装向导创建管理员 |
| MeTube | 无 | 仅内网；反代加认证 |
| SABnzbd | 需配置 | 首启设置用户名/密码；仅内网 |
| Autobrr | 有 | 首启管理员 |
| Woodpecker | 有（Gitea OAuth） | agent 的 docker.sock 等同宿主 root，只跑受信流水线 |
| MediaMTX | 无 | 9997 API 默认只绑回环；`runOnInit` 等于命令执行 |
| Karakeep | 有 | 首启管理员；抓取服务单独限权 |
| Readeck | 有 | 首启管理员 |
| Linkwarden | 有 | 首启管理员 |
| Joplin Server | 有 | 管理员 + 用户 |
| wg-easy | 有 | 必须设置 `PASSWORD_HASH` |
| Registry | 默认匿名 | 默认启用 htpasswd；TLS 由反代/证书 |
| Pocket ID | 有 | 管理员首启 |
| Unpackerr | 无 UI | 仅 API 凭据；不暴露端口 |

### 0.8 版本锁定表

“调研值”只用于估算，开工前必须在 BUILD.md 锁定 tag + commit + sha256；“待锁定”表示本设计阶段尚未确定。

| 应用 | 调研时版本 | 状态 |
|---|---|---|
| Zigbee2MQTT | v2.14.2 | 调研值，待复核 |
| Scrutiny | v0.9.5 | 调研值，待复核 |
| SFTPGo | v2.7.6 | 待复核 |
| BookStack | v26.09.2 | 调研值，待复核 |
| Vikunja | v2.7.1 | 调研值，待复核 |
| Piwigo | 未记录 | 待锁定 |
| Ente | 未记录 | 已锁定：`ente-io/ente` commit `1353a65`；server master 同期 |
| Headscale | v0.29.5 | 调研值，待复核 |
| Authelia | v4.39.28 | 调研值，待复核 |
| Backrest | 未记录 | 待锁定 |
| go2rtc | 未记录 | 待锁定 |
| Komga | 1.29.1 | 调研值，待复核 |
| Matomo | 未记录 | 待锁定 |
| MeTube | 未记录 | 已锁定：tag `2026.10.23`，commit `0f3fc1d` |
| SABnzbd | 未记录 | 待锁定 |
| Autobrr | 未记录 | 待锁定 |
| Woodpecker | v3.19.0 | 调研值，待复核 |
| MediaMTX | 未记录 | 待锁定 |
| Karakeep | 未记录 | 待锁定 |
| Readeck | 未记录 | 待锁定 |
| Linkwarden | 未记录 | 待锁定 |
| Joplin Server | 未记录 | 待锁定 |
| wg-easy | 未记录 | 待锁定 |
| Registry | 未记录 | 待锁定 |
| Pocket ID | 未记录 | 待锁定 |
| Unpackerr | 未记录 | 待锁定 |

---

## 1. P1 应用设计

### P1-01 Zigbee2MQTT（已发布）

**状态：已构建并推送。** 版本 2.14.2，digest `sha256:8d998996…039e2`；构建记录见
[../images/zigbee2mqtt/BUILD.md](../images/zigbee2mqtt/BUILD.md)。

**目标**：Zigbee 设备通过 MQTT 接入 Home Assistant / Node-RED。

| 项 | 设计 |
|---|---|
| 上游 | `Koenkk/zigbee2mqtt`，构建时 pin 到具体 tag（调研时为 v2.14.2） |
| 镜像 | `yunixintel/zigbee2mqtt` |
| 基础 | `yunixintel/node:24.22.1` |
| 构建 | release/source 包 → `corepack pnpm install --frozen-lockfile` → `pnpm run build` → `pnpm prune --prod`；`@serialport/bindings-cpp` 用 `pnpm rebuild --build-from-source` 编 loong64。上游只有 `pnpm-lock.yaml`，**不能用 `npm ci`** |
| 构建依赖 | `python3 make g++`（node-gyp）；UI 由 npm 包 `zigbee2mqtt-frontend` / `windfront` 提供，**不需要单独在 x86 构建前端** |
| 运行用户 | `zigbee2mqtt` UID/GID 1101 |
| 端口 | 8080（Web UI） |
| 卷 | `/app/data`（configuration.yaml、database.db、devices.yaml、log） |
| 设备 | `/dev/ttyACM0` 或 `/dev/ttyUSB0`；`--group-add dialout`（以宿主实际 GID 为准） |
| 环境 | `TZ`、`ZIGBEE2MQTT_DATA=/app/data` |
| entrypoint | 若 `configuration.yaml` 不存在，从 example 复制，并用 `MQTT_SERVER`/`MQTT_USER`/`MQTT_PASSWORD` 环境变量写入 `mqtt.server` 等字段（若上游支持 `ZIGBEE2MQTT_CONFIG_*` 则优先用上游机制）；确保 data 目录可写；`exec node index.js` |
| 依赖 | Mosquitto（`mqtt://mosquitto:1883`）；Home Assistant 可选 |
| 健康检查 | `curl -fsS http://127.0.0.1:8080/`；启动日志必须确认 MQTT connected，否则 UI 200 不代表可用 |
| 测试 | Web 200；MQTT 连接成功；有协调器时识别并配对；无协调器时文档说明 |
| 风险 | 构建宿主没有 Zigbee 协调器，只能验证 UI/MQTT；serialport 源码编需工具链；默认配置的 MQTT 指向 localhost，必须由 entrypoint 覆盖 |
| 估算 | 镜像约 300–400MB；1–2 天 |

**配置策略**：不在镜像内放具体设备配置；只放 `configuration.example.yaml`。`permit_join`、网络密钥由用户首次配置生成。

### P1-02 Scrutiny（SQLite 补丁，已发布）

**目标**：硬盘 SMART 历史、阈值告警、设备健康页面。

**状态：已构建并推送。** 子代理实现 SQLite metrics 补丁（`smart_metrics`/`temp_metrics`），移除 InfluxDB 依赖，API/前端不变；原生 loong64 已验证。digest `sha256:72885303…db71`，构建记录见 [../images/scrutiny/BUILD.md](../images/scrutiny/BUILD.md)。`smartctl_exporter` 保留为轻量指标替代。

| 项 | 设计 |
|---|---|
| 上游 | `AnalogJ/scrutiny`（调研时为 v0.9.5） |
| 镜像 | `yunixintel/scrutiny` |
| 基础 | `openeuler/openeuler:24.03` |
| 构建 | 两阶段：Angular 13 前端**必须用 Node 16.20.x 在 x86 构建**（Node 17+ 的 OpenSSL/md4 会失败）；Go 后端 `CGO_ENABLED=0`（modernc SQLite 1.44.3 已含 loong64）；smartctl 优先用 openEuler OS 仓库的 smartmontools，缺失才源码编 |
| 前端路径 | 前端产物复制到 `/opt/scrutiny/web`；设置 `SCRUTINY_WEB_SRC_FRONTEND_PATH=/opt/scrutiny/web`，后端没有 `go:embed` |
| 运行用户 | `scrutiny` UID/GID 1102 |
| 端口 | 8080 |
| 卷 | `/scrutiny/config`（SQLite、配置） |
| 设备 | `/dev/sd*` / `/dev/nvme*`；`--cap-add SYS_RAWIO --cap-add SYS_ADMIN`；`-v /run/udev:/run/udev:ro`（NVMe 管理命令需要） |
| 环境 | `SCRUTINY_WEB_LISTEN_HOST=0.0.0.0`、`SCRUTINY_WEB_LISTEN_PORT=8080`、`SCRUTINY_WEB_DATABASE_TYPE=SQLITE`、`SCRUTINY_WEB_DATABASE_PATH=/scrutiny/config/scrutiny.db`、`SCRUTINY_COLLECTOR_CRON_SCHEDULE`、`SCRUTINY_COLLECTOR_RUN_STARTUP=true` |
| entrypoint | 创建 config 目录；**collector 必须实际启动**（否则 SMART 验收永远不通过）；web 与 collector 同容器时用 `wait -n` 管理 |
| 健康检查 | `curl -fsS http://127.0.0.1:8080/api/health` |
| 测试 | UI 200；collector 日志出现设备；至少一块盘有 SMART 记录；USB 读卡器不支持时明确报错 |
| 风险 | 容器内 udev/设备名变化；NVMe/SATA 直通方式不同；USB 桥接可能不支持 SMART |
| 估算 | 镜像约 150–250MB；2–3 天 |

**设备策略**：文档给 SATA/NVMe 两种 `--device` 示例；不建议 `--privileged`，**禁止 `-v /dev:/dev`**。多盘用户逐个列 `--device`，或使用 compose `devices` 列表。

### P1-02b smartctl_exporter（已发布）

**状态：已构建并推送。** 替代 Scrutiny，补磁盘 SMART 指标；版本 v0.15.0，
digest `sha256:be3f0b58…fbda`，构建记录见
[../images/smartctl-exporter/BUILD.md](../images/smartctl-exporter/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `prometheus-community/smartctl_exporter` v0.15.0 |
| 镜像 | `yunixintel/smartctl-exporter` |
| 基础 | `openeuler/openeuler:24.03` + `smartmontools` |
| 构建 | Go 1.27.2，`CGO_ENABLED=0 go build` |
| 运行用户 | 容器 root（smartctl ioctl）；只读指标，无写操作 |
| 端口 | 9633 |
| 设备 | `/dev/sd*` 或 `/dev/nvme*`；`SYS_RAWIO`，NVMe 建议 `SYS_ADMIN` + `/run/udev:ro` |
| 参数 | `--smartctl.device=/dev/nvme0`（可重复）；不传则由 exporter 扫描 |
| 指标 | `/metrics` 暴露 `smartctl_device_*` |
| 依赖 | Prometheus 抓取；Grafana 出图 |
| 测试 | `/metrics` 200；NVMe 型号/固件/序列号/SMART 可读；healthy |
| 风险 | 容器只看到显式 `--device` 的盘；USB 桥接可能不支持 SMART |
| 估算 | 已完成；镜像约 123MB |

### P1-03 SFTPGo（已发布）

**状态：已构建并推送。** v2.7.6，digest `sha256:6e35b029…8919`；构建记录见 [../images/sftpgo/BUILD.md](../images/sftpgo/BUILD.md)。

**目标**：SFTP/FTP/WebDAV + Web 管理、配额、多用户、多种后端。

| 项 | 设计 |
|---|---|
| 上游 | `drakkan/sftpgo`，pin 到 **v2.7.6** |
| 镜像 | `yunixintel/sftpgo` |
| 基础 | `openeuler/openeuler:24.03` |
| 构建 | Go + CGO sqlite（`-tags sqlite`）；或构建时选 Postgres 驱动、运行期用 Postgres；**运行镜像必须带 `templates/`、`static/`、`openapi/`、`sftpgo.json`**，否则 UI 空白 |
| 构建依赖 | `gcc make sqlite-devel`；Go 1.26+ |
| 运行用户 | `sftpgo` UID/GID 1103 |
| 端口 | 8080（Web/API）、2022（SFTP）；可选 2121（FTP）、10080（WebDAV） |
| 卷 | `/srv/sftpgo`（数据/密钥）、`/var/lib/sftpgo`（SQLite） |
| 环境 | `SFTPGO_DATA_PROVIDER__DRIVER=sqlite`、`SFTPGO_DATA_PROVIDER__NAME=/var/lib/sftpgo/sftpgo.db`、`SFTPGO_HTTPD__BINDINGS__0__PORT=8080`、`SFTPGO_SFTPD__BINDINGS__0__PORT=2022` |
| entrypoint | 首次启动生成默认管理员密码或从环境读取；确保卷可写；`exec sftpgo serve` |
| 健康检查 | `curl -fsS http://127.0.0.1:8080/` |
| 测试 | Web 200；创建用户；SFTP 登录；上传/下载；配额生效；重启后数据仍在 |
| 风险 | 默认管理员密码必须首次输出/强制修改；FTP 明文默认关闭 |
| 估算 | 镜像约 120–200MB；1–2 天 |

### P1-04 BookStack（已发布）

**状态：已构建并推送。** v26.09.2，digest `sha256:20304871…efba`；构建记录见 [../images/bookstack/BUILD.md](../images/bookstack/BUILD.md)。

**目标**：书籍/章节/页面结构的 Wiki，带权限、搜索、附件。

| 项 | 设计 |
|---|---|
| 上游 | `BookStackApp/BookStack`（调研时为 v26.09.2） |
| 镜像 | `yunixintel/bookstack` |
| 基础 | `openeuler/openeuler:24.03` + PHP 8.3 + nginx/php-fpm |
| 构建 | 使用 release tarball（含 vendor/public 资产）；安装 PHP 扩展 `pdo_mysql gd zip dom mbstring curl xml fileinfo`；nginx + php-fpm 由 entrypoint 启动 |
| 构建门禁 | **先 spike `php-mysqlnd`/`pdo_mysql`**：openEuler 24.03 的 loong64 仓库覆盖不明确；现有 PHP 镜像都是 SQLite。若 dnf 没有，回退到 firefly-iii/heimdall 的源码 PHP 配方（`--with-pdo-mysql`）；Piwigo/Matomo 共用同一门禁 |
| 运行用户 | `www-data` UID/GID 33 |
| 端口 | 80 |
| 卷 | `/var/www/bookstack/public/uploads`、`/var/www/bookstack/storage`（`storage/app.key` 存 APP_KEY） |
| 依赖 | MariaDB/MySQL（复用 `yunixintel/mariadb`） |
| 环境 | `APP_URL`、`APP_KEY`（可选；未提供则首启生成并写入 `storage/app.key`）、`DB_HOST`、`DB_PORT`、`DB_DATABASE`、`DB_USERNAME`、`DB_PASSWORD` |
| entrypoint | 等待 DB；从环境变量生成 `.env`（**不把 `.env` 作为卷**）；无 `APP_KEY` 时读取/生成 `storage/app.key`；`php artisan migrate --force`；`php artisan config:cache`；启动 php-fpm + nginx |
| 健康检查 | `curl -fsS http://127.0.0.1/login` |
| 测试 | 安装/迁移；登录；建书/章/页；上传图片；搜索；权限角色 |
| 风险 | `php-gd`/`php-zip` 在 openEuler 可能需自编；必须外接 MariaDB |
| 估算 | 镜像约 500–700MB；3–5 天 |

**多服务说明**：BookStack 不是单容器应用；RUNBOOK 必须给 MariaDB 的 compose 示例和持久化卷。

### P1-05 Vikunja（已发布）

**状态：已构建并推送。** v2.7.1，digest `sha256:25333510…20a0a3`；构建记录见 [../images/vikunja/BUILD.md](../images/vikunja/BUILD.md)。

**目标**：项目/任务/Kanban/CalDAV/提醒。

| 项 | 设计 |
|---|---|
| 上游 | `go-vikunja/vikunja`（调研时为 v2.7.1） |
| 镜像 | `yunixintel/vikunja` |
| 基础 | `openeuler/openeuler:24.03` |
| 构建 | 前端 Vue 在 x86 构建（`sass-embedded` 无 loong64）；Go 后端 CGO sqlite；把 `frontend/dist` 放进 embed 路径后 `go build` |
| 构建依赖 | Go 1.27+、gcc、sqlite-devel、Node/pnpm（仅 x86 前端） |
| 运行用户 | `vikunja` UID/GID 1104 |
| 端口 | 3456 |
| 卷 | `/app/vikunja/files`、`/db` |
| 环境 | `VIKUNJA_DATABASE_TYPE=sqlite`、`VIKUNJA_DATABASE_PATH=/db/vikunja.db`、`VIKUNJA_SERVICE_JWTSECRET`（未提供时首启生成并写入 `/db/jwt.secret`，0600）、`VIKUNJA_SERVICE_PUBLICURL` |
| entrypoint | 确保 files/db 可写；读取/生成 JWT secret；启动时自动迁移；`exec /app/vikunja` |
| 健康检查 | `curl -fsS http://127.0.0.1:3456/api/v1/info` |
| 测试 | 注册/登录；建项目/任务；Kanban 拖动；CalDAV 端点；重启后数据 |
| 风险 | 前端构建依赖 x86；JWT secret 必须持久化，否则重启登录失效 |
| 估算 | 镜像约 200–300MB；3–5 天 |

---

## 2. P2 应用设计

### P2-01 Piwigo（已发布）

**状态：已构建并推送。** 16.4.0，digest `sha256:289fca6c…f8b9`；构建记录见 [../images/piwigo/BUILD.md](../images/piwigo/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `Piwigo/Piwigo`，pin 到稳定 tag |
| 镜像 | `yunixintel/piwigo` |
| 基础 | `openeuler/openeuler:24.03` + PHP 8.3 + nginx |
| 构建 | release tarball；PHP 扩展 `gd mysqli pdo_mysql mbstring xml zip exif` |
| 运行用户 | `www-data` UID/GID 33 |
| 端口 | 80 |
| 卷 | `/var/www/html/local`、`/var/www/html/upload`、`/var/www/html/_data` |
| 依赖 | MariaDB/MySQL |
| 环境 | `PIWIGO_DB_HOST`、`PIWIGO_DB_USER`、`PIWIGO_DB_PASSWORD`、`PIWIGO_DB_NAME`（entrypoint 可生成 `local/config/database.inc.php`） |
| entrypoint | 等待 DB；生成 `database.inc.php`（若未提供）；启动 php-fpm + nginx |
| 健康检查 | `curl -fsS http://127.0.0.1/` |
| 测试 | 安装向导/自动安装；上传照片；建相册；缩略图；用户权限 |
| 风险 | UI 较老；必须 MariaDB；首次安装向导需可写 `local/` |
| 估算 | 镜像约 400–500MB；2–3 天 |

### P2-02 Ente（server + web 均已发布）

**状态：ente-server 已构建并推送；ente-web 未完成。** server digest `sha256:bfac0212…9d7e`；构建记录见 [../images/ente-server/BUILD.md](../images/ente-server/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `ente-io/ente` |
| 镜像 | `yunixintel/ente-server`、`yunixintel/ente-web`（必要时拆两个） |
| 基础 | server：openEuler + Go 静态二进制；web：Node 24 构建（10 个 Next 应用），产物为静态/standalone |
| 构建 | server：Go `CGO_ENABLED=0`，构建上下文需带 `configurations/ migrations/ mail-templates/ web-templates/`；web：上游 `web/Dockerfile` 会构建 **10 个 Next 应用**并安装 Rust + `wasm32-unknown-unknown`，必须在 x86 完成 |
| 迁移 | museum 启动时自动执行迁移（`cmd/museum/main.go`）；Q-03 关闭 |
| 运行用户 | `ente` UID/GID 1105 |
| 端口 | server 8080；web 3000 |
| 卷 | museum 配置/数据目录；`/secrets`（`ENTE_JWT_SECRET`、`ENTE_KEY_ENCRYPTION`、`ENTE_KEY_HASH`）；PostgreSQL 与 MinIO 使用各自镜像的卷 |
| 依赖 | PostgreSQL、MinIO/S3；minio bucket 由一次性 init job 创建 |
| 环境 | DB：`ENTE_DB_HOST/PORT/NAME/USER/PASSWORD`；S3：`ENTE_S3_BUCKET/REGION/ENDPOINT/ACCESS_KEY/SECRET_KEY/USE_PATH_STYLE`；**三个密钥 `ENTE_JWT_SECRET`、`ENTE_KEY_ENCRYPTION`、`ENTE_KEY_HASH` 必须持久化，任一重新生成都会导致历史数据无法解密**；其余以 upstream config 为准 |
| entrypoint | 等待 DB/S3；启动 server（museum 自动迁移）；不需要单独 migration job |
| Web | 构建期固定 `NEXT_PUBLIC_ENTE_ENDPOINT`；compose 运行期不能改；文档要求构建前确定对外 URL |
| 健康检查 | server `/ping` 或 `/health`（以源码为准）；web `/` |
| 测试 | 创建账号；上传/下载一张照片；MinIO 有对象；Web 端能登录；重建容器后仍能解密旧照片 |
| 风险 | 多服务、配置项多；Web 端需 10 个 Next 应用 + Rust WASM 构建；无 ML 搜索 |
| 估算 | 2–4 个镜像；5–8 天 |

**设计决策**：先做 server + web + 文档化 compose；不把 Ente 伪装成单镜像。

### P2-03 Headscale（已发布）

**状态：已构建并推送。** v0.29.5，digest `sha256:603650be…b3fb`；构建记录见 [../images/headscale/BUILD.md](../images/headscale/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `juanfont/headscale`（调研时为 v0.29.5） |
| 镜像 | `yunixintel/headscale` |
| 基础 | openEuler + Go 静态二进制 |
| 构建 | `CGO_ENABLED=0 go build`；**`go.mod` 要求 Go 1.27.3，高于现有 1.27.2 工具链**：先升级 Go 或 pin 到兼容的旧版 Headscale，禁用 `GOTOOLCHAIN=local` 的隐式拒绝 |
| 运行用户 | `headscale` UID/GID 1106 |
| 端口 | 8080（HTTP/API）、9090（metrics，可选） |
| 卷 | `/etc/headscale`（config.yaml、private key）、`/var/lib/headscale`（SQLite） |
| 环境 | 主要通过 `config.yaml`；`HEADSCALE_CONFIG=/etc/headscale/config.yaml` |
| entrypoint | 无 config 时生成最小模板；`exec headscale serve` |
| 健康检查 | `curl -fsS http://127.0.0.1:8080/health` |
| 测试 | `headscale users create`；生成 preauth key；tailscale 客户端注册；`nodes list` 可见 |
| 风险 | 无 Web UI；密钥/域名/DERP 配置需文档；不要把私钥打进镜像 |
| 估算 | 镜像约 80–120MB；1–2 天 |

### P2-04 Authelia（已发布）

**状态：已构建并推送。** v4.39.28，digest `sha256:e05a03ac…d83a`；构建记录见 [../images/authelia/BUILD.md](../images/authelia/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `authelia/authelia`（调研时为 v4.39.28） |
| 镜像 | `yunixintel/authelia` |
| 基础 | openEuler + Go（CGO sqlite） |
| 构建 | **前端必须单独构建**：源码树里的 `internal/server/public_html/index.html` 只是占位；在 x86 用 Node ≥22.22 + pnpm 12 + Vite 8.3.4 构建 `web/`，把 `web/dist` 复制到 `public_html` 后再 `go build`（CGO sqlite） |
| 运行用户 | `authelia` UID/GID 1107 |
| 端口 | 9091 |
| 卷 | `/config`（configuration.yml、users_database.yml、secrets） |
| 依赖 | 已有反代（NPM/Caddy）；Redis 可选 |
| 环境 | `AUTHELIA_CONFIG=/config/configuration.yml`；其余从配置文件读 |
| entrypoint | 校验配置存在；`authelia validate-config --config /config/configuration.yml` 预检；`exec authelia --config /config/configuration.yml` |
| 健康检查 | `curl -fsS http://127.0.0.1:9091/api/health` |
| 测试 | 门户 200；TOTP 登录；forward-auth 与 NPM/Caddy 示例；未认证跳转 |
| 风险 | YAML 配置复杂；密钥文件权限；误配置可能锁死入口 |
| 估算 | 镜像约 100–150MB；3–5 天 |

### P2-05 Backrest（已发布）

**状态：已构建并推送。** v1.14.1，digest `sha256:955cae89…79eb`；构建记录见 [../images/backrest/BUILD.md](../images/backrest/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `garethgeorge/backrest`，pin tag |
| 镜像 | `yunixintel/backrest` |
| 基础 | openEuler + Go 静态二进制 + 自编 restic |
| 构建 | Go 后端（纯 Go SQLite，无 CGO）；`webui` 用 Vite 8，必须在 x86 构建；restic pin 到具体版本并从源码编 loong64 |
| 运行用户 | `backrest` UID/GID 1108 |
| 端口 | 9898 |
| 卷 | `/config`（config.json）、`/data`（restic 缓存/索引） |
| 环境 | `BACKREST_DATA=/data`、`BACKREST_CONFIG=/config/config.json`、`BACKREST_RESTIC_COMMAND=/usr/local/bin/restic` |
| entrypoint | 确保卷可写；`exec backrest` |
| 健康检查 | `curl -fsS http://127.0.0.1:9898/` |
| 测试 | UI 200；初始化仓库；备份一个目录；浏览快照；恢复文件 |
| 风险 | restic 无 loong64 release，必须源码编；恢复测试要隔离目录 |
| 估算 | 镜像约 150–250MB；2–4 天 |

### P2-06 go2rtc（已发布）

**状态：已构建并推送。** 1.9.14，digest `sha256:03aa0422…3def`；构建记录见 [../images/go2rtc/BUILD.md](../images/go2rtc/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `AlexxIT/go2rtc`，pin tag |
| 镜像 | `yunixintel/go2rtc` |
| 基础 | openEuler + Go 静态二进制 |
| 构建 | `CGO_ENABLED=0 go build`；无前端构建 |
| 运行用户 | `go2rtc` UID/GID 1109 |
| 端口 | 1984（Web/API）、8554（RTSP）、8555（WebRTC） |
| 卷 | `/config`（go2rtc.yaml） |
| 环境 | 无强制；配置从 `/config/go2rtc.yaml` 读 |
| entrypoint | 无配置时复制最小示例；`exec go2rtc -config /config/go2rtc.yaml` |
| 健康检查 | `curl -fsS http://127.0.0.1:1984/` |
| 测试 | Web 200；配置一个测试流（合成/RTSP）；播放页可打开；重启后配置保留 |
| 风险 | 两个代理均未覆盖，需先验证上游配置格式；WebRTC 需要正确公布宿主 IP/端口 |
| 估算 | 镜像约 50–100MB；1–2 天 |

---

## 3. P3 应用设计

### P3-01 Komga（审查后：暂停，BLOCKER）

**状态：暂停，不进入当前波次。** 1.29.1 的 `sqlite-jdbc 3.53.4.0` 只带 x86_64/aarch64/arm/ppc64/riscv64 的 JNI native，没有 loongarch64；`org.sqlite.lib.path` 不能解决缺失的 JNI wrapper。必须先做 xerial `native/` 的 loong64 编译 spike，否则 Komga 无法打开数据库。`nightmonkeys` 的 HEIF/JXL/WebP native 也只有 x86/ARM，WebP 封面同样会坏。

| 项 | 设计 |
|---|---|
| 上游 | `gotson/komga`（调研时为 1.29.1） |
| 镜像 | `yunixintel/komga` |
| 基础 | openEuler + `java-21-openjdk-headless` |
| 构建 | 使用官方 fat jar；**BLOCKER：必须先把 xerial `sqlite-jdbc` 的 loongarch64 JNI 编出来**；PDFBox/junrar 纯 Java |
| 运行用户 | `komga` UID/GID 1110 |
| 端口 | 25600 |
| 卷 | `/config`、`/data`（漫画库） |
| 环境 | `JAVA_OPTS`、`TZ`；库路径由 UI 配置 |
| entrypoint | 确保 config/data 可写；`exec java -jar komga.jar` |
| 健康检查 | `curl -fsS http://127.0.0.1:25600/` |
| 测试 | UI 200；建库；扫描一本 CBZ/PDF；阅读页；重启后数据 |
| 风险 | sqlite-jdbc native 是硬门槛；HEIF/JXL 封面不可用 |
| 估算 | 镜像约 400–600MB；4–6 天 |

### P3-02 Matomo（已发布）

**状态：已构建并推送。** 5.14.2，digest `sha256:b1e7baec…1bc2`；构建记录见 [../images/matomo/BUILD.md](../images/matomo/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `matomo-org/matomo`，pin tag |
| 镜像 | `yunixintel/matomo` |
| 基础 | openEuler + PHP 8.3 + nginx |
| 构建 | release tarball（含 vendor）；PHP 扩展 `pdo_mysql mysqli gd mbstring xml zip dom curl`；先过 BookStack 的 `php-mysqlnd` 门禁 |
| 运行用户 | `www-data` UID/GID 33 |
| 端口 | 80 |
| 卷 | `/var/www/html/config`、`/var/www/html/tmp`、`/var/www/html/plugins` |
| 依赖 | MariaDB/MySQL |
| 环境 | DB 配置由安装向导写入 `config/config.ini.php` |
| entrypoint | 启动 php-fpm + nginx；归档 cron 用单独 sidecar 或宿主 cron 执行 `console core:archive`，文档给出命令 |
| 健康检查 | `curl -fsS http://127.0.0.1/` |
| 测试 | 安装向导；跟踪测试页；报表可见；执行归档命令后报表更新 |
| 风险 | 比 Umami 重；归档 cron 需要文档化；官方镜像仅 amd64/arm64 |
| 估算 | 镜像约 500–700MB；3–5 天 |

### P3-03 MeTube ✅ 已实现（2026-10-24）

| 项 | 设计 |
|---|---|
| 上游 | `alexta69/metube`，pin tag |
| 镜像 | `yunixintel/metube` |
| 基础 | openEuler + **Python 3.13**（上游 `requires >=3.13`，3.11 无效）+ Node（仅构建前端）+ 仓库自编 ffmpeg |
| 构建 | Angular 前端 x86 构建；按 `uv.lock` 安装（不是裸 `pip install`）；去掉 `curl-cffi`/`deno` extras；yt-dlp 用 Node 作为 JS runtime |
| 构建门禁 | YouTube 需要 PO token：上游 `bgutil-pot` 只有 amd64/arm64 资产；需自编 loong64 或配置远程 PO-token provider，否则部分视频下载失败 |
| 运行用户 | `metube` UID/GID 1111 |
| 端口 | 8082（避开 CasaOS 8081） |
| 卷 | `/downloads`（下载文件与状态） |
| 环境 | `DOWNLOAD_DIR=/downloads`、`STATE_DIR=/downloads/.metube`、`TZ` |
| entrypoint | 确保 downloads 可写；`exec python3 app.py` |
| 健康检查 | `curl -fsS http://127.0.0.1:8082/` |
| 测试 | 添加一个短视频 URL；下载完成；文件出现；队列/历史可用 |
| 风险 | yt-dlp 频繁变动；curl-cffi/deno 无 loong64；网络受限时只能验证 UI |
| 估算 | 镜像约 300–500MB；2–3 天 |

### P3-04 SABnzbd ✅ 已实现（2026-10-24）

| 项 | 设计 |
|---|---|
| 上游 | `Sabnzbd/sabnzbd`，pin tag |
| 镜像 | `yunixintel/sabnzbd` |
| 基础 | openEuler + Python 3.11 |
| 构建 | `pip install -r requirements.txt`；sabctools/CT3、cryptography、httptools、**orjson 3.12.0、ujson 6.0.0** 需编译；par2 源码编；unrar 单独打包（openEuler 树中没有） |
| 运行用户 | `sabnzbd` UID/GID 1112 |
| 端口 | 8080 |
| 卷 | `/config`、`/downloads` |
| 环境 | `SABNZBD_CONFIG=/config`、`TZ` |
| entrypoint | 首次启动生成默认配置；`exec sabnzbdplus --config-file /config/sabnzbd.ini` |
| 健康检查 | `curl -fsSL http://127.0.0.1:8080/`（5.x 根路径 303→`/wizard/`） |
| 测试 | UI 200；配置新闻服务器（可用假地址验证保存）；添加 NZB；par2/unrar 可执行 |
| 风险 | `unrar` 是 freeware，许可需复核；无 loong64 预编译包 |
| 估算 | 镜像约 400–600MB；4–6 天 |

### P3-05 Autobrr（已发布）

**状态：已构建并推送。** digest `sha256:32f91a31…dcf7`；构建记录见 [../images/autobrr/BUILD.md](../images/autobrr/BUILD.md)。

| 项 | 设计 |
|---|---|
| 上游 | `autobrr/autobrr`，pin tag |
| 镜像 | `yunixintel/autobrr` |
| 基础 | openEuler + Go 静态二进制 |
| 构建 | Go（`modernc.org/sqlite` 无 CGO；**1.60.1 已含 `lib/sqlite_linux_loong64.go`，不需要升 1.61**）；React 前端 x86 构建 |
| 运行用户 | `autobrr` UID/GID 1113 |
| 端口 | 7474 |
| 卷 | `/config` |
| 环境 | `TZ`；配置在 `/config` |
| entrypoint | 确保 config 可写；`exec autobrr --config /config` |
| 健康检查 | `curl -fsS http://127.0.0.1:7474/api/healthz` |
| 测试 | UI 200；配置 IRC 网络（假值）；建 filter；连接 qBittorrent API（可选） |
| 风险 | modernc sqlite 版本；IRC 真实测试需凭据，不进镜像 |
| 估算 | 镜像约 100–150MB；1–3 天 |

### P3-06 Woodpecker CI（server + agent）✅ 已实现（2026-10-24）

| 项 | 设计 |
|---|---|
| 上游 | `woodpecker-ci/woodpecker`（调研时为 v3.19.0） |
| 镜像 | `yunixintel/woodpecker-server`、`yunixintel/woodpecker-agent` |
| 基础 | openEuler + Go（CGO sqlite） |
| 构建 | Vue/pnpm 前端 x86；Go server/agent 分别编；发布资产有 riscv64 无 loong64 |
| 运行用户 | `woodpecker` UID/GID 1114 |
| 端口 | server 8000（HTTP）、9000（gRPC）；agent 无对外端口 |
| 卷 | server `/var/lib/woodpecker`；agent `/var/lib/woodpecker`（可选） |
| 环境 | server：`WOODPECKER_HOST`、`WOODPECKER_GITEA=true`、`WOODPECKER_GITEA_URL`、`WOODPECKER_GITEA_CLIENT`、`WOODPECKER_GITEA_SECRET`、`WOODPECKER_AGENT_SECRET`、`WOODPECKER_ADMIN`、`WOODPECKER_DATABASE_DRIVER=sqlite3`、`WOODPECKER_DATABASE_DATASOURCE=/var/lib/woodpecker/woodpecker.sqlite`；agent：`WOODPECKER_SERVER=woodpecker-server:9000`、`WOODPECKER_AGENT_SECRET`、`WOODPECKER_BACKEND=docker`、`WOODPECKER_MAX_WORKFLOWS` |
| entrypoint | server 启动迁移；agent `exec woodpecker-agent`；compose 用 `depends_on` 保证 server 先起；`WOODPECKER_AGENT_SECRET` 必须持久化在 compose env/secret，不得每次随机 |
| 健康检查 | server `/api/healthz`（204）；agent `:3000/healthz` |
| 测试 | server UI 200；OAuth 连接 Gitea；agent 上线；跑一个 echo 流水线 |
| 风险 | agent 挂载 `docker.sock` 等同宿主 root；只运行受信流水线和镜像；多镜像交付 |
| 估算 | 2 个镜像；5–8 天 |

---

## 4. P4 候选设计（进入开发前先 spike）

### P4-01 MediaMTX ✅ 已实现（2026-10-24）

- 上游 `bluenviron/mediamtx`；Go 静态二进制；openEuler 运行。
- 端口 8554/tcp（RTSP）、8888/tcp（HLS）、8889/tcp（WebRTC HTTP）、8189/udp（WebRTC ICE）、9997/tcp（API，默认只绑回环）；配置 `/mediamtx.yml`；UID 1115。
- 健康检查首页/API；`runOnInit` 等于命令执行，文档必须警示；与 go2rtc 二选一。
- 风险：WebRTC 公布地址；与 go2rtc 功能重叠。估算 1–2 天。

### P4-02 Karakeep（审查后：暂缓，BLOCKER）

**状态：暂缓。** `apps/web/package.json` 依赖 `sharp ^0.35.5`，sharp 的 libvips 没有 loong64 预编译；加上网页归档需要 Chromium。除非先解决 sharp + Chromium，否则不做。

- 上游 `karakeep-app/karakeep`；Node 24 + SQLite/Postgres；Chromium 用于网页归档；搜索可能依赖 Meilisearch（`MEILI_*`），开工前确认。
- 端口 3000；`/data`；`NEXTAUTH_SECRET`、`NEXTAUTH_URL`、`DATABASE_URL`；浏览器/搜索服务按 compose 拆分。
- 风险：Chromium loong64 可用性；sharp/libvips 无 loong64；Meilisearch 依赖；镜像体积大。估算 4–7 天（若依赖解决）。

### P4-03 Readeck

- 上游 `readeck/readeck`（Codeberg）；Go **CGO_ENABLED=1** + `make -C web build`，不是“纯 Go 单二进制”。
- 端口 8000；`/data`；UID 1117；健康检查 `/`。
- 风险：前端构建依赖 Node；与 Wallabag/Shiori 重叠。估算 2–4 天。

### P4-04 Linkwarden（审查后：暂缓，BLOCKER）

**状态：暂缓。** `apps/web/package.json` 依赖 Prisma、Playwright 1.57（`postinstall: playwright install --with-deps chromium`）和 sharp 0.35；Prisma engines 没有 loong64，和 Umami 被排除的原因相同。除非改用无 Prisma/Playwright 的构建路径，否则不做。

- 上游 `linkwarden/linkwarden`；Next.js + PostgreSQL；搜索/归档可能依赖 Meilisearch；Node 24。
- 端口 3000；`DATABASE_URL`、`NEXTAUTH_SECRET`、`NEXTAUTH_URL`；按上游 compose 增加 Meilisearch（若需要）。
- 风险：Prisma/Playwright/sharp 无 loong64；多服务；浏览器归档依赖。估算 4–7 天（若依赖解决）。

### P4-05 Joplin Server（审查后：暂缓，待 native spike）

**状态：暂缓。** `packages/lib/package.json` 依赖 `sharp 0.35.0`、`sqlite-vec 0.1.9`、`sqlite3 5.1.6`，均无 loong64 预编译；server 是 yarn workspace + gulp 构建。先做 sharp/sqlite-vec 的源码编译 spike，再决定。

- 上游 `laurent22/joplin` 的 server 部分；Node + SQLite/Postgres。
- 端口 22300；`/data`；`APP_BASE_URL`、`APP_ADMIN_EMAIL`、`DB_CLIENT`、`POSTGRES_*`。
- 风险：Node 原生模块；迁移方式；多阶段构建。估算 3–5 天（若依赖解决）。

### P4-06 wg-easy（审查后：暂缓，待 libsql spike）

**状态：暂缓。** 上游 Dockerfile 复制单独构建的 `libsql` `node_modules`，libsql 没有 loong64 预编译；需要先证明能从 Rust 源码构建 libsql。AmneziaWG 的 Go/C 部分可交叉编译。

- 上游 `wg-easy/wg-easy`；Node + WireGuard tools。
- 端口 51821/tcp（Web）+ 51820/udp（WireGuard）；`/etc/wireguard`；`WG_HOST`、`PASSWORD_HASH`；`NET_ADMIN`；`sysctl net.ipv4.conf.all.src_valid_mark=1`；必要时挂 `/lib/modules`。
- 风险：宿主内核 WireGuard 模块；libsql 无 loong64；权限模型；与 Headscale/Tailscale 重叠。估算 2–4 天（若依赖解决）。

### P4-07 Registry

- 上游 `distribution/distribution`；Go 静态二进制；openEuler。
- 端口 5000；`/var/lib/registry`；配置 `config.yml`；TLS 由反代或证书挂载。
- 健康检查 `/v2/`；估算 1 天。

### P4-08 Pocket ID

- 上游 `pocket-id/pocket-id`；Go + SvelteKit；**前端需在 x86 构建**，不能用“纯 Go 单二进制”假设。
- 端口 1411；`/data`；`APP_URL`、`ENCRYPTION_KEY`；UID 1122。
- 健康检查 `/health`；与 Authelia 二选一。估算 2–4 天。

### P4-09 Unpackerr

- 上游 `Unpackerr/unpackerr`；Go 单二进制。
- 无 Web 端口；`/config`；`UN_*` 环境变量指向 *arr API。
- 无 HTTP 健康检查，安装 `procps-ng` 后用 `pgrep -f unpackerr`；RUNBOOK 说明这只是进程存活检查。估算 1 天。

---

## 5. 平台工作流设计（CasaOS / OMV）

CasaOS 与 OMV 不是容器镜像，但它们是计划内的两个独立工作项。加上 P1–P4 的 26 个应用，
本计划共 **28 个工作项**。平台工作流不套用镜像模板，但同样要有版本、构建/安装路径、
运行时契约、安全边界和验收标准。

### 5.1 CasaOS（宿主 Debian/systemd 平台）

**定位**：Loongnix/Debian + systemd 上的应用面板，提供应用商店、容器管理、文件与磁盘管理。
**不能与 iStoreOS/OpenWrt 同装**；生产形态是宿主安装，不是容器。

#### 5.1.1 组件与版本

| 组件 | 版本 | 形态 |
|---|---|---|
| casaos | v0.4.15 | Go 静态 ELF |
| gateway | v0.4.9-alpha4 | Go 静态 ELF |
| message-bus | v0.4.4-3-alpha2 | Go 静态 ELF |
| user-service | v0.4.8 | Go 静态 ELF |
| app-management | v0.4.10-alpha2 | Go 静态 ELF |
| local-storage | v0.4.4 | Go 静态 ELF |
| CLI | v0.4.4-3-alpha1 | Go 静态 ELF |
| UI | v0.4.25 | 架构无关静态资源 |
| AppStore | v0.4.5 | 架构无关静态资源 |

7 个 Go 组件均 `CGO_ENABLED=0` 编为 LoongArch 静态 ELF；UI/AppStore 直接复用 linux-all 包。

#### 5.1.2 构建与补丁

| 补丁 | 目的 |
|---|---|
| `modernc.org/sqlite → v1.30.0` | 旧版 `modernc.org/libc v1.22` 缺 loong64 syscall/asm |
| `gopsutil v3 → v4` | v3 host 包缺 loong64 utmp |
| `CASAOS_CONFIG_PATH` | 控制 `gateway.ini` 初建位置，支持前缀安装，避免写宿主 `/etc` |
| `get.casaos.io` 安装脚本 arch 分支 | `loongarch64` 会被 `*64*` 误判为 amd64 |
| `local-storage DeleteMountPointFromDB` | 格式化后按 `mount_point` 删除旧 UUID 记录 |
| P3 安装包补 `share/shell/local-storage-helper.sh` | 缺失时挂载/格式化报 `exit 127 do_mount` |
| **设备白名单下沉到写操作** | `IsDiskSupported` 只过滤列表；`POST/PUT /v1/storage` 仍可传 `/dev/loop0`、`/dev/nbd0`。必须在 mutating handler 和 helper 里再次校验，并拒绝不在服务端派生磁盘集合中的路径 |
| **首次管理员注册限制** | 首个管理员存在前，只接受来自 `127.0.0.1` 的注册；`install.sh` 在控制台打印一次性 token，或要求 SSH 隧道完成首启 |

构建产物布局：

```text
casaos-p3-0.1.0/
  bin/         7 个 LoongArch ELF
  www/         CasaOS UI v0.4.25
  appstore/    loong64-only 商店 + 镜像覆盖
  conf/        gateway.ini / 各服务 conf
  share/shell/ 磁盘/USB 脚本（含 local-storage-helper.sh）
```

#### 5.1.3 安装布局与运行契约

| 项 | 设计 |
|---|---|
| 安装前缀 | `/opt/casaos-p3`（业务文件避免污染宿主 `/etc`、`/usr`；systemd unit 例外） |
| 宿主前置 | Docker ≥20 + containerd、`rclone`（local-storage 需要，自编 v1.71.2）、`samba cifs-utils net-tools unzip` |
| 配置 | 前缀内 `conf/`；通过 `CASAOS_CONFIG_PATH` 指向；其余服务各自的 `*.conf` 路径见 5.1.4 路径表 |
| 数据 | `/var/lib/casaos`（应用/用户/商店状态）、应用自身卷 |
| systemd | 7 个 unit，`systemd-analyze verify` 必须 0 错误；6 个常驻服务；unit 需 `After=docker.service` 或 `Requires=docker.service` |
| 用户 | 平台服务按上游要求运行；**CasaOS 管理员等同宿主 root**，app-management 持有 `docker.sock`，必须在文档中明示 |
| 端口 | **固定 gateway 8081/tcp**；冲突时只允许显式改配置，不做静默 first-free；80 保留给宿主 Web；端口分配见 5.1.5 |
| 存储依赖 | `udev smartmontools parted ntfs-3g mergerfs udevil`（Loongnix 源均有 loong64） |
| 磁盘白名单 | 允许 `sata/nvme/sas/spi/virtio/mmc`；`usb`、`loop`、`dm`、`nbd` 在列表和**写操作**两层都被拒绝 |
| 升级 | 替换前缀包；保留 `/var/lib/casaos` 与用户应用卷；升级前备份（见 5.1.6） |
| 卸载 | `uninstall.sh --system`；不删除用户数据卷，除非显式确认；卸载前列出孤儿容器 |

#### 5.1.4 路径与端口契约

**路径表（前缀安装必须逐项验证）：**

| 路径 | 用途 | 迁移方式/例外 |
|---|---|---|
| `/opt/casaos-p3/conf/gateway.ini` | gateway 配置 | `CASAOS_CONFIG_PATH` |
| `/opt/casaos-p3/conf/*.conf` | 其余服务配置 | 各服务的 config flag 或补丁；不能只改 gateway |
| `/var/lib/casaos` | 用户/应用/商店状态 | 数据目录，升级保留 |
| `/var/run/casaos` | 运行时 socket/pid | 由 tmpfiles 或 unit `RuntimeDirectory=` 创建 |
| `/opt/casaos-p3/share/shell/local-storage-helper.sh` | 磁盘 helper | 补丁让 local-storage 从前缀查找，或建兼容符号链接 |
| `/etc/systemd/system/casaos*.service` | systemd unit | **明确例外**：`--system` 必须写这里 |
| `/usr/share/casaos/...` | 上游默认资源路径 | 若无法重定向，明确列出并接受；不能声称“宿主 /etc /usr 完全未动” |

验证方法：安装前后记录 `find /etc /usr -xdev -newer <timestamp>`，把新增路径写入 CASAOS-P3；未解释的路径视为失败。

**端口表：**

| 服务 | 端口 | 说明 |
|---|---|---|
| CasaOS gateway/UI | **8081/tcp** | 固定值；冲突时显式改配置，不静默漂移 |
| 宿主 Web | 80/443/tcp | 保留；CasaOS 不占用 |
| MeTube（P3-03） | **8082/tcp** | 从 8081 移开，避免与 CasaOS 冲突 |
| Dashy（已有镜像） | 8081/tcp | 与 CasaOS 冲突；同机部署时必须改 Dashy 或 CasaOS 映射 |
| 其他新应用 | 见各自设计 | 新增镜像不得占用 8081 |

#### 5.1.5 安全与边界

- **首次管理员注册**：首个管理员存在前，只接受来自 `127.0.0.1` 的注册；安装脚本在控制台打印一次性 token，或要求 SSH 隧道完成首启。管理员存在后才允许局域网登录。
- **管理员等同宿主 root**：gateway/app-management 以高权限运行并持有 `docker.sock`；文档必须明示“CasaOS 管理员 = 宿主 root”，并建议只在受信内网使用。
- **设备白名单必须在写操作生效**：`IsDiskSupported` 只负责列表；`POST/PUT /v1/storage` 与 `local-storage-helper.sh` 都要再次校验，拒绝不在服务端派生磁盘集合中的路径。增加负向测试：对 `/dev/loop0` 发起挂载/格式化必须返回 4xx。
- **USB 只读是策略不是属性**：`iso9660 ro` 是文件系统自身只读，不代表 udevil 一定 ro 挂载。必须明确：不启用 `USBAutoMount`，udevil 配置为只读或禁用，并用可写 U 盘做负向测试。
- 只在可信内网使用；网关不得直接暴露公网。
- 不能与 iStoreOS/OpenWrt 同装；容器形态只用于演示。

#### 5.1.6 验收（对应 NEXT-PLAN C-01..C-06）

| ID | 验收 |
|---|---|
| C-01 | **SATA 盘**：挂载、写读、卸载、按 UUID 重启自挂、SMART 可读。SMART 判定标准：至少能读取 `health`、`temperature`、`power_on_hours`、`reallocated_sector_ct`；任一项读不到则记录为“该盘不支持”，不算通过 |
| C-01b | **USB 盘（独立项）**：udevil 识别、只读挂载、卸载、物理拔插；明确“USB 不进入 local-storage 管理”，不做格式化验收 |
| C-02 | 备用盘格式化/重建文件系统后重新挂载，旧 UUID 记录不残留；**前置条件：`DeleteMountPointFromDB` 补丁已打入安装包并记录 sha256** |
| C-03 | 24h 稳定性：6 服务不崩；重启后自起；应用安装/卸载正常；记录 CPU/内存/日志 |
| C-04 | 发布闸门评审：C-01/C-01b/C-02/C-03 全部通过，附带命令输出与安装包 sha256 |
| C-05 | 上游 PR/issue：架构误判、sqlite/gopsutil、helper、格式化记录；记录 issue/PR 链接，**不作为发布闸门** |
| C-06 | 应用商店同步：P1/P2 新镜像加入 appstore，标注 loong64-only；**不作为发布闸门** |

**发布闸门**：C-01、C-01b、C-02、C-03、C-04 全部通过前，CasaOS 镜像和安装包不发布。

#### 5.1.7 运维契约

- **systemd unit**：统一包含 `Restart=on-failure`、`RestartSec=5`、`StartLimitIntervalSec`/`StartLimitBurst`；按需加 `ProtectSystem=strict`、`NoNewPrivileges=yes`、`MemoryMax`。unit 模板写入 CASAOS-P3。

```ini
[Unit]
Description=CasaOS <service>
After=network-online.target docker.service
Requires=docker.service
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=simple
ExecStart=/opt/casaos-p3/bin/<service>
Restart=on-failure
RestartSec=5
RuntimeDirectory=casaos
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/var/lib/casaos /var/run/casaos

[Install]
WantedBy=multi-user.target
```
- **备份**：`/var/lib/casaos`、`/opt/casaos-p3/conf`、应用 compose/卷清单；备份前停服务，恢复后做一次登录/应用启动验证。
- **升级/回滚**：保留上一版前缀包与配置；升级失败可按包版本回滚；不覆盖用户数据卷。
- **日志/监控**：6 个服务日志进入 journald；给出 `journalctl -u` 命令；C-03 记录资源基线。
- **mergerfs**：至少验收建池、加盘、移除盘、单盘故障四个场景；不能只声明依赖。
- **产物锚定**：安装包、每个补丁、每个二进制都记录 sha256；设计/验收引用同一份哈希。

### 5.2 OpenMediaVault（宿主 Debian 平台，先做 Gate 0）

**定位**：Debian 上的 NAS 管理平台（存储、共享、插件、Web UI）。
**当前不承诺移植**；先做 Gate 0 可行性，回答“完整移植 / 只做 compose 集成 / no-go”。

#### 5.2.1 目标形态

| 项 | 设计假设（待 Gate 0 验证） |
|---|---|
| 目标版本 | **先确认 OMV 7（bookworm）还是 OMV 8（trixie）**，不能预设 OMV 7。宿主已知事实：glibc 2.41、systemd 257、16K 页、kernel 6.6.52；这些更接近 Debian 13，而非 bookworm 的 glibc 2.36 / systemd 252 |
| 基线证据 | `/etc/os-release`（`VERSION_CODENAME`）、`/etc/debian_version`、`dpkg --print-architecture`、`ldd --version`、`systemctl --version`、`getconf PAGE_SIZE`、PHP 版本/模块、Python、`apt policy`（php/nginx/salt/samba/mdadm/lvm2/nfs/smartmontools）、内核配置、bootloader/ESP、Loongnix 是否为真正 Debian 派生 |
| 核心 | `openmediavault` 包、PHP、nginx、SaltStack、rrdcached、collectd、smartmontools、mdadm、lvm2、samba、nfs |
| Web | 80/443；首次安装设置 admin 密码 |
| 数据 | `/etc/openmediavault`、`/var/lib/openmediavault`、`/srv`；用户数据盘独立 |
| 插件 | `openmediavault-compose`（应架构无关）、ZFS（需引用或重跑证据）、KVM（**已封存，移除**）、sharerootfs/sftp/rsync |
| 安装方式 | 宿主包安装，不是容器；禁止在生产 NAS 上直接试 |

#### 5.2.2 三条路线

| 路线 | 内容 | 适用条件 |
|---|---|---|
| A. 完整移植 | 打齐 `openmediavault` 及依赖的 loong64 包，跑通 Salt highstate 与插件 | 硬依赖闭包无不可修补缺口；highstate 失败仅限已命名且可补的 state 集合；安装→重启→共享→回滚全部通过 |
| B. 只做 compose 集成 | 不装 OMV 核心；在现有 Debian/Loongnix 上用 compose 管理本仓库镜像，并写清与 OMV 的边界 | 用户真正需要的是容器编排，不是 OMV 存储栈；1–2 天可交付，不叫“OMV-compose” |
| C. No-Go | 保留 ksmbd + 现有方案 | 依赖缺口超过约定数量、插件不可用、无人维护 |

**决策规则（必须在 O-03 之前预注册）：**

- A 只在“硬 Depends 闭包零不可修补缺口 + highstate 失败可枚举修补 + 端到端验收通过”时成立。
- B 是独立可交付路线，不依赖 A 的结论；O-07 也要覆盖 B。
- C 在缺口数量超过阈值或没有维护者时成立。
- 不允许用“补丁量可接受”这类无法证伪的判据；O-06 必须引用具体清单和数字。

#### 5.2.3 Gate 0 任务与交付物

| ID | 任务 | 交付物 | 退出条件 |
|---|---|---|---|
| O-01 | 目标版本与基线审计 | 先判定 OMV 7（bookworm）还是 OMV 8（trixie）；再记录 os-release/debian_version/arch/glibc/systemd/page size/PHP/Python/apt policy/kernel/bootloader | `OMV-FEASIBILITY.md` 明确“目标 OMV 版本 + 宿主是否匹配” |
| O-02 | 依赖闭包 | 递归 `apt-cache depends --recurse`，区分 `arch:all` 与 `binary-loong64`；检查 OMV 仓库是否有 loong64 Packages；缺则评估 `apt-ftparchive -a loong64` 重建索引 | 硬 Depends/Recommends 缺口表；**禁止直接添加 bookworm 源**（在 trixie 时代基线上是部分升级事故） |
| O-03 | 一次性环境安装 spike | **QEMU TCG loong64 VM**（x86 构建机上运行）或等价的完全隔离环境；不用 NBD 做 OMV 管理根盘 | 能进入 OMV 首次配置，或明确失败点 |
| O-04 | SaltStack highstate | 先 `test=True`；对 `/etc`、`/boot`、unit 文件做前后 checksum diff；预置 network/ssh deny-list；离线恢复点 | 失败 state 可枚举、可补；不依赖网络恢复 |
| O-05 | 插件评估 | compose（架构无关）、ZFS（引用或重跑 OpenZFS 2.4.4 + 16K 页证据）、sharerootfs/sftp/rsync；**KVM 已封存，移出评估** | 明确可用插件与前置条件 |
| O-06 | Go/No-Go | 按 5.2.2 预注册规则选 A/B/C；记录依赖缺口数量、highstate 失败集合、维护者 | 决策可复现、可证伪 |
| O-07 | 若 A 或 B：交付计划 | A：包清单/补丁/测试矩阵；B：compose 集成与边界说明 | 可排期 |
| O-08 | 许可、卸载与回滚 | OMV 名称/Logo 商标与插件许可；卸载残留（`/etc/openmediavault`、fstab、samba 用户）；配置备份/恢复 | 许可结论 + 可执行回滚步骤 |
| O-09 | 状态同步 | 更新 GAPS/ROADMAP/OMV-FEASIBILITY；记录 no-go 或进入 A/B | 文档与决策一致 |

#### 5.2.4 测试环境与安全

- **指定环境：QEMU TCG loong64 VM**（在 x86 构建机上运行），或等价的完全隔离机器；KVM 已封存、A 机无空闲物理盘，不能用“备用盘/NBD”当默认方案。
- **不要用 NBD 作为 OMV 的管理根盘**：OMV 会把 `/dev/nbd*` 当作存储枚举并写 fstab/mount unit。
- 测试前备份 `/boot`、grub 配置、`/etc/fstab`、`/etc/network`；准备不依赖网络的串口/控制台救援流程。
- 禁止在生产 NAS 上直接安装/改网络/改存储。
- ZFS/KVM 插件不与 CasaOS/固件实验混在同一台机器。
- 安装脚本可能修改网络、fstab、服务；必须有离线回滚方案。

#### 5.2.5 验收

- O-01..O-06、O-08、O-09 全部有书面结论；O-06 明确 A/B/C，并引用具体依赖缺口数与 highstate 失败集合。
- 若选 A：至少完成一次安装、一次重启、一次共享创建、一次配置恢复、一次回滚。
- 若选 B：给出 compose 集成方案、与 OMV 的边界说明、卸载/回滚步骤。
- 若选 C：在 GAPS/ROADMAP 记录 no-go 理由和前置条件，不再反复评估。
- 无论 A/B/C：记录 OMV 名称/Logo/插件许可结论；不把未验证的 ZFS/KVM 写成“可用”。

---

## 6. 开放问题清单

| ID | 问题 | 影响应用 | 处理方式 |
|---|---|---|---|
| Q-01 | openEuler 24.03 是否有 `php-gd`/`php-zip`/`php-exif` 包 | BookStack、Piwigo、Matomo | 构建 spike；缺则源码编扩展 |
| Q-02 | `sqlite-jdbc` loong64 native 如何重编/注入 | Komga | **BLOCKER，已暂停**；专项 spike 通过前不排期 |
| Q-03 | Ente museum 的迁移命令与最小环境变量 | Ente | **已关闭**：museum 启动时自动迁移；最小环境变量仍以源码 config 为准 |
| Q-04 | Scrutiny 在容器内识别 `/dev/sd*` 的稳定方式 | Scrutiny | SATA/NVMe 两种真机测试 |
| Q-05 | Z2M serialport 在 Node 24 下的源码编参数 | Zigbee2MQTT | 构建 spike |
| Q-06 | SABnzbd 的 unrar 许可与分发方式 | SABnzbd | 法务/许可复核后再做 |
| Q-07 | MeTube 去掉 curl-cffi/deno 后 yt-dlp 的 JS runtime 行为 | MeTube | **已关闭**：默认 `YTDL_OPTIONS` 指定 Node 24；实测下载成功 |
| Q-08 | Woodpecker agent 的 docker.sock 权限模型 | Woodpecker | 安全评审 + compose 示例 |
| Q-09 | Karakeep 所需 Chromium 在 loong64 的可用性 | Karakeep | 先验证浏览器，失败则不做 |
| Q-10 | OMV 的 Debian 基线是否匹配 Loongnix 25 | OMV | Gate 0 O-01 |

---

## 7. 独立审查记录

两个独立审查代理在 2026-10-23 完成，只读设计稿与仓库，不改文件：

- **审查 A（构建可行性）**：逐个核对上游 `go.mod`、`package.json`、Dockerfile、release 资产、jar/nupkg 内容。
- **审查 B（运行时/安全/一致性）**：核对端口、UID、卷、健康检查、密钥、多服务依赖和 DoD。

### 7.1 审查结论摘要

**BLOCKER（已从当前波次移除）**

| 应用 | 结论 | 原因 |
|---|---|---|
| Komga | 暂停 | `sqlite-jdbc 3.53.4.0` 无 loongarch64 JNI；`org.sqlite.lib.path` 无解；nightmonkeys 的 WebP/HEIF/JXL native 也只有 x86/ARM |
| Linkwarden | 暂停 | Prisma engines 无 loong64；Playwright 1.57 安装 Chromium；sharp 0.35 无 loong64 |
| Karakeep | 暂停 | sharp/libvips 无 loong64；网页归档需要 Chromium |

**MAJOR（已修正设计）**

| 应用/章节 | 原问题 | 修正 |
|---|---|---|
| Zigbee2MQTT | 上游只有 `pnpm-lock.yaml`，`npm ci` 会失败；UI 由 npm 包提供，不需要单独 x86 构建 | 改为 `corepack pnpm install --frozen-lockfile` + `pnpm run build` + `pnpm prune --prod` |
| Scrutiny | Angular 13 需要 Node 16；UI 不在 Go embed 中；collector 未明确启动 | x86 用 Node 16.20 构建；产物放 `/opt/scrutiny/web` 并设 `SCRUTINY_WEB_SRC_FRONTEND_PATH`；collector 必须启动 |
| BookStack/Piwigo/Matomo | `php-mysqlnd`/`pdo_mysql` 在 openEuler loong64 仓库覆盖不明 | 增加前置门禁；缺失则回退源码 PHP `--with-pdo-mysql` |
| Headscale | `go.mod` 要求 Go 1.27.3，现有工具链 1.27.2 | 先升级 Go 或 pin 旧版 Headscale |
| Authelia | 源码树 `public_html` 是占位，前端未嵌入 | 强制 x86 Vite 8.3 构建，复制 `web/dist` 后再 `go build` |
| Ente | Web 端被低估；迁移方式不明 | Web 构建 10 个 Next 应用 + Rust WASM；server 上下文补齐 4 个目录；确认 museum 启动自动迁移 |
| MeTube | Python 3.11 不满足 `>=3.13`；PO token 资产只有 amd64/arm64 | 用 Python 3.13 + `uv.lock`；自编 bgutil-pot 或配置远程 PO-token provider |
| Joplin / wg-easy | sharp/sqlite-vec、libsql 无 loong64 | 暂缓，先做 native spike |
| SFTPGo | 运行镜像缺 `templates/ static/ openapi/ sftpgo.json` | 补运行资产；pin v2.7.6 |
| SABnzbd | 漏了 orjson/ujson；unrar/par2 不在 openEuler 树 | 补 Rust/编译依赖；unrar 单独打包并复核许可 |
| Backrest / Readeck / Pocket ID | 前端/构建方式被低估 | Backrest 的 Vite 8 x86 构建；Readeck 需 CGO + `make -C web build`；Pocket ID 需 SvelteKit 构建 |
| 全部 Node 镜像 | `yunixintel/node` 不含 curl | 每个 Node 镜像显式安装 curl；0.1/0.4 已写明 |
| UID | 新应用统一 1000，与现有镜像冲突 | 新增 1101–1123 分配表；root 启动后 `runuser` 降权，禁止递归 chown |
| 认证 | 多个默认无认证面板未标注 | 新增 0.7 默认认证矩阵；go2rtc/MediaMTX API 默认只绑回环 |
| DoD | 缺备份/升级/可观测性 | NEXT-PLAN §9 和 APP-SYNC-CHECKLIST 增加备份/恢复、升级/回滚、监控项 |

**审查带来的“减负”修正**

- `modernc.org/sqlite` 1.60.1（Autobrr）和 1.44.3（Scrutiny）**已经包含 loong64 实现**，不需要升级。
- `smartmontools` 在 openEuler OS 仓库中，Scrutiny 不必默认源码编。
- Ente museum 是真正的 CGO-free，server 构建比原先估计简单。

### 7.2 审查后范围

| 类别 | 数量 | 说明 |
|---|---|---|
| P1 可开工 | 5 | 全部保留；Z2M/Scrutiny 构建配方已修正 |
| P2 可开工 | 6 | Ente 移到 Wave 3；Headscale/Authelia 需先过工具链/前端门禁 |
| P3 可开工 | 5 | Komga 暂停；其余 5 个保留 |
| P4 可评估 | 5 | MediaMTX、Readeck、Registry、Pocket ID、Unpackerr |
| 暂停/暂缓 | 5 | Komga、Karakeep、Linkwarden、Joplin、wg-easy |
| 合计 | 26 | 21 个应用可进入后续波次，5 个等待依赖 spike |

加上 CasaOS 与 OMV 两个平台工作项，计划总数为 **28 个工作项**。平台审查记录见 7.5。

### 7.3 开工前剩余门禁

1. `php-mysqlnd`/`pdo_mysql` 在 openEuler loong64 的可用性（BookStack/Piwigo/Matomo）。
2. Z2M `@serialport/bindings-cpp` 在 Node 24 下的源码编。
3. Scrutiny 的 SATA/NVMe 设备直通与 SMART 读取。
4. Headscale 的 Go 1.27.3 工具链或旧版 pin。
5. Ente 的 10 个 Next 应用 + Rust WASM 构建，以及三密钥持久化。
6. MeTube 的 Python 3.13 + PO-token 路径。
7. SABnzbd 的 unrar 许可与打包。
8. Komga `sqlite-jdbc` loong64 JNI（未通过前不排期）。
9. Karakeep/Joplin/Linkwarden 的 sharp/libvips；wg-easy 的 libsql。
10. OMV Gate 0 的 Debian 基线审计。
11. CasaOS 的设备白名单下沉、首启认证、端口固定、路径审计；C-01..C-04 全过才解禁。
12. OMV 的目标版本判定（7 vs 8）、QEMU TCG 隔离、依赖闭包方法与 A/B/C 阈值。

### 7.4 审查方法说明

- 审查 A 的证据来自上游仓库文件与发布资产，不是 Docker Hub manifest；个别版本可能已漂移，开工前仍需 `crane manifest` + 构建 spike。
- 审查 B 的部分运行时参数来自上游 Dockerfile/compose 推断，尤其是 Ente、BookStack、Woodpecker；实现时以启动日志和官方 compose 为准。
- 两个审查都不替代真机验证；设计稿通过审查只表示“没有明显找死路”，不表示“必然构建成功”。

### 7.5 平台工作项审查（CasaOS / OMV）

CasaOS/OMV 的详细设计补充后，另开两个独立审查代理，只读、不改文件。结论如下。

#### CasaOS 审查

| 严重度 | 发现 | 处理 |
|---|---|---|
| BLOCKER | `IsDiskSupported` 只过滤列表；`POST/PUT /v1/storage` 仍可对 `/dev/loop0`、`/dev/nbd0` 挂载/格式化 | 白名单下沉到 mutating handler 和 helper；5.1.2 新增补丁；验收加负向测试 |
| BLOCKER | 端口口径矛盾：CASAOS-P3 默认 8081、CASAOS-PLAN 80–89/8080–8089、MeTube/Dashy 也占 8081；first-free 会静默漂移 | 固定 CasaOS 8081；MeTube 改 8082；新增 5.1.4 端口表；first-free 只作显式 fallback |
| BLOCKER | 首个管理员注册可被局域网抢先；管理员等同宿主 root；docker.sock | 首管理员前只接受 localhost 注册 + 一次性 token；文档明示 root 等价；建议限制 docker.sock |
| MAJOR | 前缀安装只重定向 gateway.ini，其他服务/helper/runtime socket 路径未覆盖 | 新增 5.1.4 路径表；`/etc/systemd/system` 为明确例外；安装前后做 `/etc` `/usr` 新增路径审计 |
| MAJOR | 缺 Docker/containerd、rclone、samba/cifs-utils/net-tools/unzip；unit 无 docker 依赖 | 5.1.3 增加宿主前置；unit 加 `After=/Requires=docker.service` |
| MAJOR | C-01 要求 USB 盘可被 local-storage 管理，但设计明确过滤 usb；C-02 依赖的补丁未入包 | 拆成 C-01 SATA + C-01b USB 只读；C-02 前置补丁 sha256 |
| MAJOR | “USB 只读”是策略不是属性 | 明确关闭 USBAutoMount/udevil ro；用可写 U 盘做负向测试 |
| MAJOR | 发布闸门只覆盖 C-01/C-02，跳过 24h 稳定性和评审 | 闸门改为 C-01/C-01b/C-02/C-03/C-04；C-05/C-06 非闸门 |
| MINOR | 版本字符串不一致、无 systemd 运维契约、无平台备份/恢复、mergerfs 无验收、产物哈希未锚定 | 5.1.6/5.1.7 增加 unit 模板、备份/回滚、mergerfs 四场景、sha256 锚定 |

**CasaOS 结论：保持发布闸门关闭，不发布。** 必须完成上述 BLOCKER 修复和 C-01..C-04 后才能解禁。

#### OMV 审查

| 严重度 | 发现 | 处理 |
|---|---|---|
| BLOCKER | 原设计预设 OMV 7/Debian 12，但宿主 glibc 2.41/systemd 257/16K 页更接近 Debian 13；可能应评估 OMV 8 | 5.2.1 改为“先判定 OMV 7 还是 8”；O-01 先定目标版本再审计宿主 |
| BLOCKER | 原隔离方案“备用盘/NBD/VM”不可执行：A 机无空闲盘、KVM 已封存、快照未定义 | 指定 QEMU TCG loong64 VM；备份 `/boot`/grub/fstab/network；准备离线救援；禁止 NBD 做管理根盘 |
| MAJOR | O-02 依赖闭包方法太薄，漏 Recommends、arch:all、OMV 仓库无 loong64、插件链、PHP/Salt 依赖 | 改为递归 Depends/Recommends + `apt-ftparchive -a loong64` 评估；禁止加 bookworm 源 |
| MAJOR | SaltStack highstate 风险被低估，可能改网络/ssh/fstab/服务 | O-04 增加 `test=True`、checksum diff、network/ssh deny-list、离线恢复点 |
| MAJOR | A/B/C 不互斥、B 被误称为 OMV-compose、A 无可证伪阈值 | 重写 5.2.2：B 是独立 compose 集成；A 需硬依赖零缺口 + 可枚举 highstate 失败 + 端到端通过 |
| MAJOR | KVM 已封存却仍在插件评估；ZFS “已验证”无仓库证据 | O-05 移除 KVM；ZFS 需引用或重跑 OpenZFS 2.4.4 + 16K 页证据；修正 ROADMAP |
| MINOR | 缺许可/商标、卸载/回滚、配置备份、OMV 7→8 升级、监控冲突、状态同步 | 新增 O-08/O-09；5.2.5 增加许可与回滚验收 |

**OMV 结论：Gate 0 方向正确，但必须先修目标版本、隔离环境、依赖方法和决策规则，否则 O-06 无法给出可辩护的 A/B/C。**

### 7.6 平台审查后的总状态

- **28 个工作项**：26 个应用镜像 + CasaOS + OMV。
- 应用：Scrutiny 经 SQLite 补丁发布；P1-02b smartctl_exporter 作为轻量替代；其余 21 个可推进，5 个暂停/暂缓。
- 平台：CasaOS 保持闸门关闭；OMV 只做 Gate 0，先修审查发现的 BLOCKER。
- 本设计稿不承诺发布日期；每个工作项开工前仍需依赖 spike 和真机验证。
