# iStore 龙芯（loong64）app-meta 源

本目录为 115 个 `linux/loong64` 应用生成 iStore app-meta ipk、一个通用安装器
LuCI 包，以及 public / private 两套可部署 feed。所有镜像只支持龙芯
3A5000/3A6000（LoongArch64），x86/ARM 无法运行。

- app-meta 包：115 个，`arch: ["all"]`
- 通用安装器：`luci-app-istore-loong64`，1 个
- feed：`feed/public/`、`feed/private/`，各自包含 `Packages*` 与 `isfeeds.conf`
- 未在真实 OpenWrt/iStoreOS 上执行安装回归；见“已验证/未验证”

## 目录

```text
store/istore/
  README.md                 本文件
  gen_istore.py             从描述/端口/镜像 Dockerfile/人工覆盖生成 115 个源码包
  build-feed.sh             一次构建 public + private 两套 feed
  validate.py               静态校验 JSON、runtime 投影、ipk 结构、Packages 索引
  data/
    runtime-overrides.json  端口/卷/env/sidecar/设备/人工限制的唯一人工覆盖表
    build-manifest.json     生成结果清单（自动化等级、端口/卷/sidecar 数量）
  src/
    generic/                通用安装器 LuCI 包源码
    app-meta/<id>/          115 个 app-meta 源码
  tools/
    mkipk.py                确定性 ipk 打包（固定 mtime/uid/gid，gzip mtime=0）
    mkindex.py              Packages / Packages.gz / Packages.manifest / Packages.sig
    mkvariant.py            public/private feed 的 JSON/conf/UCI 变体转换
  feed/
    public/                 公开商店 feed
    private/                私人商店 feed
```

`feed/` 由构建生成，可以整体复制到 Web 服务器；源码在 `src/` 与 `data/`。

## 通用安装器方案

只生成 **一个** LuCI 包 `luci-app-istore-loong64`，不生成 115 个
`luci-app-<id>`。每个 app-meta 包自带：

- `/usr/lib/opkg/meta/<id>.json`：元数据与 `loong64` 扩展字段
- `/usr/libexec/istorec/<id>.sh`：两行 wrapper，转调通用脚本
- `/usr/share/istore-loong64/apps/<id>.conf`：JSON 的 shell 投影（jsonfilter
  不可用时的兜底）
- `/etc/config/<id>`：UCI 覆盖项，作为 conffile 保留

通用入口：

```text
/usr/libexec/istorec/loong64.sh <id> <action>
```

它优先用 `jsonfilter` 读取 `.loong64.runtime`（由结构化 JSON 生成并校验一致），
再渲染 `docker run`。sidecar（PostgreSQL/MariaDB/Redis/MinIO/LBrowser）先启动并
等待健康状态，再启动主容器。首次安装生成随机 secret 并持久化到
`/etc/istore-loong64/secrets/<id>.env`（0600），升级复用同一份。

LuCI 页面：

```text
/admin/services/istore-loong64                 应用列表 + 状态
/admin/services/istore-loong64/app?app=<id>    详情、配置、操作、端口/卷/sidecar
```

app-meta 的 `entry` 指向上述详情页。

### loong64 扩展字段

`/usr/lib/opkg/meta/<id>.json` 的 `loong64` 对象包含：

```json
{
  "schema": 1,
  "image": "yunixintel/gogs:24.10-la5",
  "default_variant": "public",
  "variants": [{"name": "public", "image": "...", "store_url": "..."}],
  "ports": [{"name": "http", "container": 3000, "host": 18010,
             "proto": "tcp", "primary": true}],
  "volumes": [{"name": "data", "host": "/srv/gogs/data",
               "container": "/data", "mode": "rw", "owner": "",
               "primary": true, "type": "dir", "seed": ""}],
  "env": [{"key": "APP_URL", "value": "${PUBLIC_URL}", "required": true,
           "variants": ""}],
  "sidecars": [{"full_name": "joplin-server-pg", "image": "...",
                "enabled_variants": ["public", "private"],
                "health": {"cmd": "pg_isready ...", "retries": 30},
                "env": [], "volumes": [], "ports": []}],
  "needs_host_network": false,
  "needs_docker_sock": false,
  "docker_sock_ro": true,
  "devices": [], "cap_add": [], "group_add": [], "sysctls": [],
  "shm_size": "", "user": "", "command": [], "restart": "unless-stopped",
  "network_group": "", "requires_app": "",
  "review": {"automation": "auto|needs_config|manual",
             "manual": [], "notes": []},
  "runtime": "APP_ID='...'\n...（shell 投影，供 ash 读取）"
}
```

占位符：`${PUBLIC_URL}`、`${HOST_IP}`、`${PRIMARY_PORT}`、`${APP_ID}`、
`${SECRET:name[:len]}`。`required: true` 且值为空时安装器会拒绝启动并提示写入
`/etc/istore-loong64/env/<id>.env`。

## 构建

要求 Python 3（仅标准库），不需要网络、Docker 或 OpenWrt SDK。

```bash
cd store/istore
sh build-feed.sh
```

可选环境变量：

| 变量 | 作用 |
|---|---|
| `FEED_BASE_URL` | 写入 `isfeeds.conf` 的 HTTP 根地址，默认 `http://<your-feed-host>/istore-loong64` |
| `PUBLIC_STORE_URL` | public feed 的 store URL |
| `PRIVATE_STORE_URL` | private feed 的 store URL |
| `USIGN_KEY` | 设置后用 `usign -S` 生成真实 `Packages.sig`；未设置时文件为空 |
| `SKIP_VALIDATE=1` | 跳过构建后的 `validate.py` |
| `NO_GEN=1` | 不重新生成 `src/app-meta/`，直接打包 |

构建是确定性的：ipk 内 mtime 固定，uid/gid 0，gzip `mtime=0`，文件顺序稳定。
输出：

```text
feed/public/all/meta/          115 个 app-meta ipk + Packages*
feed/public/all/nas_luci/      luci-app-istore-loong64 + Packages*
feed/public/isfeeds.conf
feed/private/all/meta/         115 个 app-meta ipk + Packages*
feed/private/all/nas_luci/     luci-app-istore-loong64 + Packages*
feed/private/isfeeds.conf
```

两个 feed 的 `Packages` 各 115 个 meta + 1 个 LuCI 包。`Packages.gz` 与未压缩
`Packages` 完全一致；`Packages.sig` 未设置 `USIGN_KEY` 时为 0 字节。

`isfeeds.conf` 不写构建机绝对路径。部署时：

1. 把 `feed/public/` 或 `feed/private/` 放到 `FEED_BASE_URL` 对应目录；
2. 在设备上把 `isfeeds.conf` 内容加入 `/etc/opkg/customfeeds.conf`；
3. `opkg update`。

本地临时测试也可以把 `isfeeds.conf` 的 URL 改成 `file:///...`，但不要提交。

## 安装

```sh
opkg update
opkg install luci-app-istore-loong64          # 通用安装器（app-meta 依赖它）
opkg install app-meta-gogs                    # 或从 feed 安装任意 app-meta
```

或直接安装本地 ipk（先装通用包）：

```sh
opkg install ./luci-app-istore-loong64_1.0.0-r20261025_all.ipk
opkg install ./app-meta-gogs_1.0.0-r20261025_all.ipk
```

安装 app-meta 只安装元数据、wrapper 和 UCI 配置，不会自动拉镜像。首次安装：

```sh
/usr/libexec/istorec/gogs.sh install
```

也可以从 LuCI 页面点击 install/upgrade。

### 动作

```text
install | upgrade     拉取镜像、创建网络、启动 sidecar、重建主容器
rm                    删除主容器和 sidecar，保留数据与 secrets
purge                 rm；仅当 ISTORE_PURGE_DATA=1 时删除 /srv/<id>
start | stop | restart 启停主容器与 sidecar
status                主容器状态：running/exited/not-installed
status-all            主容器 + 所有 sidecar 状态
port                  主端口
ports                 所有端口映射：name host container proto primary
url                   主 URL
logs [n]              主容器日志末 n 行
sidecars              sidecar 容器名与状态
render                只打印生成的 docker 脚本，不执行
config                打印解析后的镜像/变体/端口/网络
pull                  只拉镜像
list                  列出已安装的 LoongArch64 app-meta
```

`rm` 不删除 `/srv/<id>`；`purge` 默认也不删除，必须显式
`ISTORE_PURGE_DATA=1 /usr/libexec/istorec/<id>.sh purge`。

### UCI 覆盖

`/etc/config/<id>`：

```uci
config main 'main'
    option enabled '1'
    option variant 'public'          # public | private
    option image ''                  # 显式镜像，优先于 variant
    option host_port '18010'         # 主端口覆盖
    option data_path '/srv/gogs/data'# 主数据目录覆盖
    option env_file '/etc/istore-loong64/env/gogs.env'
```

`env_file` 每行 `KEY=VALUE`，覆盖 JSON 中同名 env；secret 仍由安装器生成。
升级前修改 `host_port`/`data_path` 会重建主容器，数据卷不变。

## 公开与私人 feed

两套 feed 由同一个 `build-feed.sh` 一次生成，指向不同镜像/商店：

### `feed/public/`

- 每个 app-meta 的 `variants` **只保留 public**，`default_variant: public`
- 镜像：`yunixintel/<id>:24.10-la5`
- `store_url` 与 `website` 指向公开仓库
- Linkwarden/Karakeep 的 LBrowser sidecar 只在 public 变体启用

### `feed/private/`

- Linkwarden、Karakeep 默认 `default_variant: private`，镜像为
  `local/linkwarden-private:2.16.3-p1`、`local/karakeep-private:0.34.1-p1`
- 这两个应用的 private 变体是**单镜像**，不启动 LBrowser sidecar
- 没有私人镜像的应用仍使用公开镜像，但 `store_url`/`website` 指向私人源
- private feed 的 `local/*` 镜像**不会被本脚本推送、复制或上传**；部署前必须在
  目标机预加载：

```sh
docker load -i linkwarden-private-2.16.3-p1.tar
docker load -i karakeep-private-0.34.1-p1.tar
# 或 docker tag + 本地构建产物
docker image inspect local/linkwarden-private:2.16.3-p1
```

- 安装器遇到 `local/*` 或标记 `preload: true` 的 sidecar 时只做
  `docker image inspect`，不会 `docker pull`。`local/*` 缺失时安装失败并提示预加载。
- LBrowser 运行时（`yunixintel/lbrowser-runtime:3.4.2293.2`）在 Docker Hub 公开，
  安装器会自动 pull；但宿主 `/opt/apps/lbrowser` 的浏览器字节仍需预置，public 变体
  的 Linkwarden/Karakeep 才能截图/PDF。private 变体不需要 LBrowser sidecar。
- 私人源部署方式：把 `feed/private/` 放到私人 `FEED_BASE_URL` 下，设备使用私人
  `isfeeds.conf`；不要把 `local/*` 推到公开 registry。
- 私人 feed 的 app-meta 版本为 `1.0.0-r20261025-p1`，public 为
  `1.0.0-r20261025`；在同一设备切换 feed 时 opkg 会视为升级。`/etc/config/<id>`
  是 conffile，切换后可能保留旧 `option variant`；需要手工改成 `private` 或先
  删除该 conffile。

`store/private/links.json` 与 `store/private/compose/*.yml` 仍是镜像引用和
compose 的人工来源；`gen_istore.py` 只读取其中的镜像/版本/compose 路径。

## sidecar

安装器会先启动 sidecar，等待健康检查后再启动主容器：

| 应用 | sidecar 容器名 | 说明 |
|---|---|---|
| `joplin-server` | `joplin-server-pg` | PostgreSQL，主容器用 `POSTGRES_*` |
| `miniflux` | `miniflux-pg` | PostgreSQL，唯一支持的数据库 |
| `jellystat` | `jellystat-pg` | PostgreSQL |
| `linkwarden` | `linkwarden-pg`、`linkwarden-lbrowser` | PG 必需；LBrowser 仅 public |
| `karakeep` | `karakeep-lbrowser` | LBrowser 仅 public；private 单镜像 |
| `bookstack` | `bookstack-db` | MariaDB，必须 |
| `piwigo` | `piwigo-db` | MariaDB，必须 |
| `matomo` | `matomo-db` | MariaDB，必须；Web 安装向导填库 |
| `ente-server` | `ente-pg`、`ente-minio` | PostgreSQL + MinIO；bucket 需手工创建 |
| `penpot-backend` | `penpot-postgres`、`penpot-redis` | 与 frontend 共用 `istore-penpot` 网络 |

共享网络组：`penpot-backend`/`penpot-frontend` 使用 `istore-penpot`；
`ente-server`/`ente-web` 使用 `istore-ente`；`woodpecker-server`/
`woodpecker-agent` 使用 `istore-woodpecker`。单独安装其中一个时，另一个的
`requires_app` 检查只会告警，不会自动安装。

## 端口与数据

- 主端口默认取 `store/casaos/port-plan.json` 的分配；固定端口应用（Caddy
  80/443、NPM 管理口 81、registry 5000、wg-easy 51820/51821、syncthing
  22000/21027、sftpgo 2022、go2rtc 8554/8555 等）保留固定值。
- 次要端口从 20000 起按应用确定分配，避免与 18001–18199 冲突。
- 固定端口冲突时后出现的应用自动改用高位端口，并在 `review.notes` 记录。
- 数据目录默认 `/srv/<id>/...`；媒体目录映射到 `/mnt/media`、`/mnt/music`、
  `/mnt/books`、`/mnt/downloads`、`/mnt/movies`、`/mnt/tv`、`/mnt/audiobooks`、
  `/mnt/comics`、`/mnt/files`。
- host 网络应用：`mihomo`、`easytier`、`adguardhome`、`pihole`、
  `homeassistant`、`homebridge`、`owntone`、`node-exporter`。它们直接占用宿主
  53/80/8123 等端口，不能与其它应用重复监听。
- Docker socket：`watchtower`、`dozzle`、`portainer`、`dpanel`、
  `woodpecker-agent`。这些容器可控制宿主 Docker，只应安装可信应用。

## 已验证（静态）

已执行并通过 `validate.py`：

- 115 个 app-meta + 1 个 LuCI 包，public/private 各 115 + 1
- 每个 `Packages` 索引 115/1 条；`Packages.gz` 解压后与 `Packages` 逐字节一致；
  `Size`/`SHA256sum` 与 ipk 实际文件一致
- ipk 外层为 `debian-binary` + `data.tar.gz` + `control.tar.gz`；内层含
  `control`、`postinst`、`prerm`、`conffiles`（app-meta）与 meta JSON/wrapper/
  conf/UCI 配置
- meta JSON 必有 `name/title/title_en/entry/author/website/version/release/
  arch/description/description_en/tags/depends/loong64`；`arch == ["all"]`；
  description 含“龙芯版说明”，英文含 “LoongArch notes”
- `loong64.runtime` 与结构化 ports/volumes/env/sidecars 一致
- ipk 中 `.sh`/`.conf`/`control` 无 CRLF（`\r` 即失败）
- 代表性应用端到端解包检查：`gogs`、`joplin-server`、`linkwarden`
- 用 stub docker/uci 复测：`joplin-server install` → `status-all`（主 + sidecar
  均 running）→ `sidecars` → `rm`，`/srv/joplin-server` 数据保留
- Host A（3A6000）真实运行：最终安装器 `joplin-server install` → 健康检查/
  `/api/ping` 200 → `status-all` 双 running → `rm` 保留 `/srv` 数据
- `render` 抽查：public Linkwarden 的 LBrowser 为
  `'yunixintel/lbrowser-runtime:3.4.2293.2' 'serve'`（镜像名在命令之前）；
  private Linkwarden 无 LBrowser 行、无 `PLAYWRIGHT_WS_URL`，镜像为
  `local/linkwarden-private:2.16.3-p1`；private Karakeep 含
  `CRAWLER_STORE_PDF=true`、无 LBrowser 行、镜像为
  `local/karakeep-private:0.34.1-p1`
- `loong64.sh` 的主机 IP 探测顺序：`uci network.lan.ipaddr` →
  `hostname -I` → `ip route get 1.1.1.1`，避免代理/VPN 把 `${PUBLIC_URL}`
  渲染成 198.18.0.1

## 未验证 / 已知限制

- **没有在真实 OpenWrt/iStoreOS 上执行 `opkg install` 或 LuCI 点击回归**。
  Host A（3A6000）上已用最终安装器真实执行 `joplin-server install`、健康检查/
  `/api/ping` 200、`status-all` 双 running、`rm` 保留 `/srv` 数据；其余 114 个
  应用未逐项真机运行。
- `Packages.sig` 默认空。生产 feed 应设置 `USIGN_KEY`，或在 opkg 中关闭签名校验；
  空签名不等于已签名。
- 未生成应用图标（`/www/luci-static/resources/app-icons/<id>.png`）；iStore 可能
  显示默认图标。
- 未为每个应用生成独立 `luci-app-<id>` CBI；统一使用
  `luci-app-istore-loong64` 页面。iStore 上游的 `taskd` 异步任务未接入，安装/升级
  在 LuCI 中以后台 shell 方式执行，日志在 `/tmp/istore-<id>.log`。
- 固定端口/host 网络应用存在部署冲突：Caddy 与 NPM 都想要 80/443（Caddy 保留，
  NPM 自动改高位）；go2rtc 与 mediamtx 都想要 8554（先出现的保留）；pihole 与
  adguardhome 都想要 53/80，不能同时用 host 网络运行。
- 部分应用需要真实设备或外部服务：见下表。它们的 `install` 可能成功但功能不可用，
  或因为 required env 为空而拒绝安装。
- 数据库 sidecar 使用默认口令生成和宿主机目录；未做备份/迁移工具集成。
- LBrowser 与 private 单镜像受许可证/分发限制，公开 registry 不提供；
  `local/*` 必须预加载。
- app-meta 只带元数据与安装定义，不带应用本体；所有镜像需另行拉取/预加载。

### 无法完全自动化的应用（25）

这些应用在 `review.automation == "manual"`，安装前需人工准备：

| 类别 | 应用 |
|---|---|
| 配置文件/密钥 | `mihomo`、`easytier` |
| DNS/端口冲突 | `adguardhome`、`pihole` |
| 首次 UI/CLI 建管理员或仓库 | `kopia`、`typecho`、`wallabag`、`rest-server`、`backrest`、`bookstack`、`matomo` |
| 外部数据库 | `phpmyadmin` |
| 设备相关 | `zigbee2mqtt`、`smartctl-exporter`、`scrutiny` |
| 流/摄像头配置 | `go2rtc`、`mediamtx` |
| 域名/HTTPS/OAuth/外部服务 | `headscale`、`authelia`、`woodpecker-server`、`woodpecker-agent`、`ente-server`、`ente-web`、`wg-easy`、`unpackerr` |

另有 7 个 `needs_config`：`caddy`、`prometheus`、`gatus`、`alertmanager`、
`penpot-frontend`、`linkwarden`、`karakeep`。它们能安装，但默认配置只保证启动，
真实使用需替换配置、预加载 LBrowser 或与 companion 应用一起部署。

其余 83 个标记为 `auto`：安装器可完成镜像拉取、端口/卷、sidecar、重启策略和状态
查询；这不等于业务功能已在龙芯上逐项回归。

## 与 CasaOS 的差异

| 维度 | CasaOS | 本 iStore feed |
|---|---|---|
| 包格式 | `docker-compose.yml` + `x-casaos` | ipk（control/data）+ `/usr/lib/opkg/meta/<id>.json` |
| 安装 | CasaOS 解析 compose | opkg 安装 app-meta；通用 shell 渲染 `docker run` |
| 多服务 | compose services 原生 | `loong64.sidecars`，安装器先起 sidecar 并等健康 |
| 配置 | compose env/volumes | UCI `/etc/config/<id>` + env 文件 + secrets 文件 |
| UI | CasaOS 商店 | iStore 列表 + 通用 LuCI 详情页 |
| 端口 | compose ports | `port-plan.json` + 固定端口/自动次要端口 |
| 私人镜像 | compose 文件替换 | 独立 `feed/private`，默认 private + `local/*` 预加载 |
| 说明字段 | `x-casaos.description` | `description`（中文 HTML，含“龙芯版说明”）/`description_en` |
| 图标 | 应用图标 | 未生成，使用默认图标 |
| 自动化 | compose 即定义 | 83 auto / 7 needs_config / 25 manual |

CasaOS 的 18 个已有定义仍是端口规划的来源；本 feed 不修改
`store/casaos/`，只读取 `port-plan.json`。

## 新增/修改应用

1. 在 `images/<id>/` 提供 Dockerfile（`EXPOSE`/`VOLUME` 会被自动读取），或在
   `data/runtime-overrides.json` 写 `ports`/`volumes`。
2. 在 `store/loong64-descriptions.json` 与
   `store/exports/istore-descriptions.json` 提供文案；description 必须含
   “龙芯版说明”。
3. 在 `runtime-overrides.json` 增加 sidecar、host 网络、设备、固定端口、private
   variant 或 `review.manual`。
4. 运行：

```bash
python3 gen_istore.py
sh build-feed.sh
python3 validate.py
```

5. 若新增 private 单镜像，更新 `store/private/links.json`；私有镜像只能放在
   `local/*` 或私人 registry，禁止推到公开源。

## 快速校验

```bash
cd store/istore
python3 -I validate.py

# ipk 结构
tar tzf feed/public/all/meta/app-meta-gogs_1.0.0-r20261025_all.ipk
mkdir -p /tmp/ipk && tar xzf feed/public/all/meta/app-meta-gogs_1.0.0-r20261025_all.ipk -C /tmp/ipk
tar tzf /tmp/ipk/control.tar.gz
tar tzf /tmp/ipk/data.tar.gz

# CRLF 检查（应无输出）
grep -rIl $'\r' feed/public/all/nas_luci 2>/dev/null || true

# 索引
grep -c '^Package: ' feed/public/all/meta/Packages
grep -c '^Package: ' feed/private/all/meta/Packages
```

## 签名

`Packages.sig` 默认 0 字节，仅用于开发/内网。生产签名：

```bash
export USIGN_KEY=/path/to/private.key
sh build-feed.sh
```

构建会对每个 feed 的 `Packages` 执行 `usign -S -m Packages -s "$USIGN_KEY"
-x Packages.sig`。公钥需通过其他可信渠道分发给设备；不要把私钥放进本目录或
feed。
