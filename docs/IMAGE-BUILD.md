# 应用镜像构建手册（loong64）

本文件说明 115 个 `yunixintel/*` 镜像的可复现构建方式。`images/` 保存了 105 个镜像的 Dockerfile；
其余 10 个早期镜像的 Dockerfile 未保留，但下方给出源码版本、关键步骤和构建日志入口。

## 0. 共同约定

- 基础镜像：`openeuler/openeuler:24.03`（loongarch64），少数为 scratch。
- 构建机：龙芯 3A6000 / Loongnix 25，Docker 为 loong64；Go 工具链可用
  `/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64/bin/go`。
- 推送标签固定两只：`loong64` 与 `24.10-la5`。
- 构建上下文中的 `frontend/`、`src/`、`app/`、`dist/` 等大目录不提交到本仓库；
  按 Dockerfile 的 `ARG`/注释从上游对应 tag 获取。
- 每个镜像构建后至少验证：`docker inspect` 架构为 `loong64`、进程能启动、首页/健康检查 200。

## 1. 工具链模式

### 1.1 纯 Go（无 CGO）

```bash
export GOROOT=/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64
export PATH=$GOROOT/bin:$PATH GOTOOLCHAIN=local GOPROXY=https://goproxy.cn,direct
CGO_ENABLED=0 go build -trimpath -ldflags '-s -w' -o app .
```

适用：caddy、watchtower、node-exporter、prometheus、dozzle 的 Go 部分等。

### 1.2 Go + CGO（SQLite / 系统库）

`go-sqlite3`、mattn 系依赖必须 `CGO_ENABLED=1`，且必须在**目标 glibc 版本**的基础镜像内编：

```bash
docker run --rm -v "$PWD":/src -w /src openeuler/openeuler:24.03 bash -c '
  dnf install -y gcc make
  export GOROOT=/toolchain PATH=/toolchain/bin:$PATH GOTOOLCHAIN=local
  CGO_ENABLED=1 GOOS=linux GOARCH=loong64 go build -trimpath -ldflags "-s -w" -o app .
'
```

适用：ntfy、gotify、gitea、miniflux、adguardhome 等。
不要在 Loongnix 宿主直接编后拿到 openEuler 镜像运行：宿主 glibc 2.41 会引入
`GLIBC_2.39 not found`（geckodriver 已踩过）。

### 1.3 Vite 8 / Rolldown 前端

Vite 8 的 Rolldown 没有 loong64 native binding（`rolldown-binding.linux-loong64-gnu.node` 不存在）。
做法：在 x86_64 WSL2 / x86 构建机用 Node 22 生成架构无关的 `dist`，再拷到龙芯构建上下文。

```bash
# WSL2 x86_64
curl -fsSLO https://nodejs.org/dist/v22.23.3/node-v22.23.3-linux-x64.tar.xz
tar xf node-v22.23.3-linux-x64.tar.xz
export PATH=$PWD/node-v22.23.3-linux-x64/bin:$PATH
npm ci && npm run build
```

适用：dozzle、ntfy、gotify、prometheus、changedetection 的部分前端。

Alertmanager 是 Elm + Vite：`ui/app` 用 `npm ci && npm run build`（`vite-plugin-elm` 编译
Elm），产物 `dist` 被 Go `//go:embed app/dist` 嵌入。`ui/mantine-ui/` 在本版本未接入构建，
不需要处理。完整命令见 [../images/alertmanager/BUILD.md](../images/alertmanager/BUILD.md)。

Node-RED 5 和 Homebridge 2 需要 Node ≥22.9/22.12，openEuler 24.03 只有 Node 20。
使用 unofficial-builds 的 `node-v24.22.1-linux-loong64.tar.xz`（SHA256
`5653027b…6b58`）构建 `yunixintel/node:24.22.1`：openEuler 的基础 + `/opt/node24`
运行时；Node 22.23.3 仍保留为 `:22.23.3`。该二进制最高只要求 `GLIBC_2.38`，
与镜像一致。注意 npm 全局前缀是 `/opt/node24`，不是 `/usr/local`。

`homebridge-config-ui-x` 的 `node-pty` 没有 loong64 预编译且 npm 包不含
`src/unix`，需要从 GitHub `v0.14.1` 源码 `node-gyp rebuild` 出 `pty.node` 再放回包内。
Config UI 5 由 `hb-service run` 同时启动 UI 和 Homebridge，单独跑 `homebridge`
不会监听 8581。详见 [../images/node/BUILD.md](../images/node/BUILD.md)、
[../images/node-red/BUILD.md](../images/node-red/BUILD.md)、
[../images/homebridge/BUILD.md](../images/homebridge/BUILD.md)。

### 1.4 特殊补丁

- **changedetection + jq 1.13**：内置 oniguruma 的旧 `config.sub` 不认 loongarch64；
  用 automake 1.16 的 `config.guess/config.sub` 替换嵌套 tarball，并给 configure 加
  `--build=loongarch64-unknown-linux-gnu`，预编 `jq-1.13.0-cp311-cp311-linux_loongarch64.whl`。
- **paperless-ngx**：openEuler 只有 qpdf 11.1，pikepdf 10.17 需要 qpdf 12；多阶段源码编 qpdf 12.4.2。
- **changedetection Firefox**：geckodriver 在 openEuler 容器内用 Rust 1.99 编；见
  `images/changedetection/Dockerfile.firefox` 与 `docs/OPENCV-SSIM.md`。
- **prometheus**：UI 必须 `go build -tags builtinassets`，否则 UI 500/静态资源 404。
- **OpenCV/SSIM**：openEuler 的 opencv 4.5.2 自带 cv2，但 numpy 必须降到 1.26.4；配方见
  [OPENCV-SSIM.md](OPENCV-SSIM.md)。

### 1.5 Pi-hole FTL（C/C++）

- FTL v6.8 + web v6.6.1，web 是 `.lp` 模板 + 静态资源，不需要 Node 构建。
- openEuler 24.03 的 nettle 3.8.1 缺 `balloon.h`：源码编 nettle 3.10.2 静态库到
  `/usr/local/lib64`，FTL configure 加 `-I/usr/local/include`、
  `-DLIBNETTLE=/usr/local/lib64/libnettle.a -DLIBHOGWEED=/usr/local/lib64/libhogweed.a`。
- 构建依赖必须有 `vim-common`（提供 `xxd`，FTL 用它生成 `docs.h` 资源数组）。
- openEuler 的 EPOL/debuginfo metalink 会 404：dnf 加
  `--disablerepo=debuginfo --disablerepo=EPOL --setopt=retries=1 --setopt=timeout=15`。
- 龙芯编译把 `src/CMakeLists.txt` 的 `-Werror` 改为 `-Wno-error`。
- 运行时用 entrypoint 在首启执行 `sqlite3 /etc/pihole/gravity.db < gravity.db.sql`（使用
  `advanced/Templates/gravity.db.sql` 的干净 schema，不含测试假数据）。
- 镜像包含上游 `pihole` CLI、`gravity.sh`、`advanced/`，以及自定义 `pihole-adlist`
  （add/list/remove，add/remove 后自动 `pihole -g`）；Dockerfile/entrypoint/CLI 见 `images/pihole/`。

### 1.6 直接使用 openEuler 系统包（PostgreSQL / Redis）

上游官方镜像没有 loong64 资产，而 openEuler 24.03 SP4 已提供
`postgresql-server 15.18`、`redis 7.2.14`。这类基础服务直接基于系统包构建，
避免无收益的源码重编，并保证与镜像 glibc 2.38 一致。

- PostgreSQL：`images/postgres/`，entrypoint 负责 initdb、创建用户/库、SCRAM 认证、
  降权到 UID 26 并用 `runuser` 启动；详见 [../images/postgres/BUILD.md](../images/postgres/BUILD.md)。
- Redis：`images/redis/`，entrypoint 负责 `/data` 权限、`REDIS_PASSWORD` 临时配置副本，
  再降权到 UID 998 启动；详见 [../images/redis/BUILD.md](../images/redis/BUILD.md)。

## 2. 有 Dockerfile 的镜像

`images/<app>/Dockerfile` 可直接作为构建入口；上下文要求：

| 类型 | 需要的上下文 |
|---|---|
| `homer` / `dashy` | `dist/`（Homer 官方 zip；Dashy 官方 release 的 `dist/`） |
| `caddy` / `watchtower` / `node-exporter` | 仅二进制 + CA 证书 |
| `prometheus` | `prometheus`、`promtool`、`prometheus.yml`（UI 已 embed） |
| `paperless-ngx` | 源码 `paperless-ngx-3.3.2/src/`、`frontend/`、`requirements.txt` |
| `changedetection` | 源码 + `wheels/jq-*.whl` + `geckodriver` + 打过补丁的 fetcher |
| `dozzle` | 上游源码 + 预构建 `dist` |
| `ntfy` / `gotify` | 上游源码 + 预构建 `web/build` / `ui/build` |
| `alertmanager` | `alertmanager`/`amtool` 二进制 + `alertmanager.yml`；前端 `ui/app/dist`（x86 WSL2 编） |
| `postgres` / `redis` / `mosquitto` / `mariadb` | 仅 Dockerfile + entrypoint（+ 配置文件）；依赖 openEuler 系统包 |
| `node-red` | 以 `node:22.23.3-loong64` 为构建阶段，`npm install -g node-red@5.0.8`；运行阶段复制 `/opt/node22/bin`、`lib` 和 Node-RED 包 |
| `grafana` | `grafana` 二进制 + 预构建 `public/`（x86 WSL2 的 Yarn 4/webpack）+ `conf/defaults.ini` |
| `memcached` | 仅 Dockerfile + entrypoint；依赖 openEuler `memcached` 包 |
| `homebridge` | Node 22 下安装 Homebridge 2.4.0 + UI 5.29.0；源码编译 node-pty；`hb-service` 启动；运行阶段重建 `homebridge.js` 符号链接 |
| `node` | Node.js 24.22.1 loong64 运行时基础镜像；从 unofficial-builds tarball 解压，`/opt/node24` |
| `rest-server` | `rest-server` 静态二进制 + entrypoint/用户脚本；`htpasswd` 由 openEuler `httpd-tools` 提供 |
| `actual-budget` | Node 24 构建阶段安装 `@actual-app/sync-server`；手动 `node-gyp rebuild` better-sqlite3；运行阶段复制 `/opt/node24` 与包 |
| `minio` | Go 1.27 源码 `-tags kqueue` 静态编；显式设置 RELEASE ldflags；运行阶段仅二进制 + CA |
| `homebox` | 前端 Nuxt 在 x86 WSL2 构建后 embed；Go 1.27 编后端；`modernc.org/sqlite` 升到 1.61 支持 loong64 |
| `nocodb` | Node 24 构建阶段 `npm install --ignore-scripts`，手动编 sqlite3；运行阶段自定义 `docker-main.js` + NocoDB 包 |
| `apprise-api` | Python 3.11 + 系统 cryptography/gevent；pip 构建 pycares 等；nginx+supervisor+gunicorn |
| `mealie` | Python 3.14 源码 + Nuxt 前端 x86 构建；Rust 1.99 编 orjson/pydantic-core/curl-cffi；pillow-heif 用 stub（HEIF 禁用） |
| 其余 | 见 Dockerfile 的 `COPY` 行；大目录不随仓库提交 |

## 3. 未保留 Dockerfile 的 10 个镜像

这些镜像的构建步骤在 [BUILDLOG.md](BUILDLOG.md) 有记录；按以下版本/入口重建：

| 镜像 | 版本/上游 | 关键步骤 |
|---|---|---|
| adguardhome | AdGuardHome 源码 + 官方前端 | Go 编；官方无 loong64 资产；53 端口需避让宿主 dnsmasq |
| code-server | 4.141.0 + VS Code 1.141 | 必须 Node 24；自编静态 ripgrep 15.2 |
| easytier | 上游 loong64 release / 源码 | scratch + 单二进制；配置挂载 `/etc/easytier` |
| firefly-iii | v6.7.9 | openEuler 只有 PHP 8.3，builder 阶段源码编 PHP 8.5；SQLite 迁移/种子 |
| gitea | v28.2.0 | Go 1.27 编；modernc SQLite；入口生成 app.ini |
| jellyfin | 10.11.0 | .NET 9 SDK 自编；web 单独编；e_sqlite3 用系统库；ImageSharp 编码器 |
| memos | v0.31.0 | Go 源码编；前端在 x64 编（rolldown 无 loong64） |
| mihomo | 上游 loong64 release | scratch + 单二进制；配置挂载 `/etc/mihomo` |
| miniflux | 2.3.3 | 上游删 SQLite，必须外接 PostgreSQL |
| navidrome | v2.x + taglib 2.0.2 | Go 编 + 系统 taglib；DSD 完整 |
| one-api | v0.6.10 | 三套前端本机编；go-sqlite3 需 CGO 静态链接 |
| phpmyadmin | 5.2.3 | PHP 8.3 + nginx/php-fpm；首启建 `/run/php-fpm` |
| vaultwarden | 1.35.x | Rust 编后带 GLIBC_2.39 引用；镜像内置宿主 glibc 2.41 闭包并显式 loader |

> 注：表中是 13 个条目，其中 `one-api` 对应本地目录 `oneapi`，`jellyfin`/`navidrome`
> 的 Dockerfile 已从归档补入 `images/`；真正缺 Dockerfile 的是
> adguardhome、code-server、easytier、firefly-iii、gitea、memos、mihomo、miniflux、
> phpmyadmin、vaultwarden 共 10 个。

## 3.5 2026-10 新增的 36 个镜像

| 镜像 | 上游 | 关键步骤/坑 |
|---|---|---|
| chinesesubfinder | v0.55.2 | Quasar 前端在 x86 构建；go-webrtcvad 补 LoongArch 分支；`WORKDIR=/config` |
| lanraragi | 0.9.81 | cpanm local::lib 126 模块；PERL5LIB 带 loongarch64 目录；内置 Redis |
| owntone | 29.3 | autoreconf；运行期 dbus+avahi；gettext/openssl devel |
| mymind | iStore 静态包 | 纯静态 + nginx；32 文件 |
| webvirtcloud | master 2026-10 | Django venv + gunicorn + novncd + nginx；bcrypt 需 Rust |
| penpot-backend | 2.18.3 | 官方 uberjar（Java 21 字节码）+ openEuler JDK 21；需 PostgreSQL/Redis |
| penpot-frontend | 2.18.3 | 官方静态产物 + nginx 反代；envsubst |
| hermes | master 2026-10 | Python 3.14.8；pip 冲突用 --no-deps + 过滤依赖；`HERMES_NIX_BUILD=1` |
| zigbee2mqtt | 2.14.2 | Node 24 + pnpm；serialport 源码编 loong64；运行阶段需 systemd-udev（udevadm） |
| smartctl-exporter | v0.15.0 | Go 单二进制 + smartmontools；替代 Scrutiny（InfluxDB 阻塞） |
| sftpgo | v2.7.6 | openEuler 容器内 CGO 编 SQLite；运行资产 templates/static/openapi；首次安装页建管理员 |
| bookstack | v26.09.2 | PHP 8.3 + nginx/php-fpm；Composer vendor；必须 MariaDB；`app.key` 持久化 |
| vikunja | v2.7.1 | Vue 前端 x86 构建 + Go CGO SQLite；`service.interface=0.0.0.0:3456`；JWT secret 持久化 |
| piwigo | 16.4.0 | PHP 8.3 + nginx/php-fpm；必须 MariaDB；首次启动 curl POST `install.php` 自动安装 |
| go2rtc | 1.9.14 | Go 单二进制；1984 API/8554 RTSP/8555 WebRTC；默认无认证 |
| scrutiny | 0.9.5 + SQLite 补丁 | Go 纯 Go SQLite；Angular 13（Node 20）；运行阶段需 libstdc++/libgcc 供 smartctl |
| headscale | v0.29.5 | Go 单二进制；配置模板 + `/var/run/headscale` 权限；无 Web UI |
| backrest | v1.14.1 | 前端 x86 构建后 embed；restic 0.19.1 源码编；`/data`/`/config`/`/cache` |
| authelia | v4.39.28 | 前端 x86 构建 + api 资产；Go CGO SQLite；自动生成配置/用户/密钥 |
| ente-server | master 2026-10 | Go CGO-free；museum.yaml 自动生成；需 PostgreSQL + S3/MinIO |
| ente-web | ente commit 1353a65 | 10 个 Next.js 静态导出；x86 上 Rust/wasm-pack 与 npm 构建；nginx 模板启动时注入 `ENTE_API_ORIGIN` |
| autobrr | master 2026-10 | Vue 前端 x86 构建后 embed；Go CGO-free；SQLite |
| matomo | 5.14.2 | 官方完整包；PHP 8.3 + nginx/php-fpm；必须 MariaDB；Web 安装向导 |
| woodpecker-server | v3.19.0 | Vue 前端 x86 构建后 embed；Go CGO SQLite；必须配置 forge；`/var/lib/woodpecker` |
| woodpecker-agent | v3.19.0 | Go CGO-free；UID 1114；需 `docker.sock` + `--group-add`；3000 健康检查 |
| metube | 2026.10.23 | Angular x86 构建；openEuler 内编 Python 3.13.7；yt-dlp + Node 24 + ffmpeg；watchfiles 轮询补丁；无 Brotli/bgutil-pot |
| sabnzbd | 5.1.3 | Python 3.11 + venv；orjson 用 ujson 回退、cryptography 用系统包；par2cmdline 需 `--build=loongarch64-...`；unrar 源码 |
| mediamtx | 1.9.3 | Go 静态编；先写 `internal/core/VERSION` 并 `go generate` 下载 hls.js；配置默认开 API |
| registry | 3.1.2 | Go 静态编；输出路径与仓库 `registry/` 目录冲突；entrypoint 生成 htpasswd 与 HTTP secret |
| unpackerr | 0.9.9 | Go 静态编；必须把 `golang.org/x/sys` 升到 v0.35.0（旧版无 loongarch64 定义）；unrar 源码 |
| pocket-id | 2.9.0 | SvelteKit 前端 x86 构建后 embed；Go 静态编；首启生成加密密钥；健康检查用 curl（内置 healthcheck 需要完整 env） |
| readeck | 0.9.2 | gulp 前端 x86 构建到 `assets/www`；必须 `CGO_ENABLED=1`（modernc 旧版无 loongarch64）；mattn sqlite |
| wg-easy | 15.4.0 | Nuxt/Nitro 本机构建；vendor 5 个 loong64 绑定（libsql/oxc/rolldown/lightningcss）；argon2 换 hash-wasm；运行阶段需 EPOL 的 wireguard-tools |
| komga | 1.29.1 | 官方 jar；构建阶段从 sqlite-jdbc 3.53.4.0 编 loongarch64 JNI（必须 `OS_NAME=Linux`）；JDK 21 |
| node-sharp | sharp 0.35.5 | 基础镜像；源码编 libvips 8.18.7 + node-gyp 编 sharp；`/opt/vips` 与 `/opt/node_modules/sharp` 可复用 |
| karakeep | 0.34.1 | Next standalone（x86 `--webpack`）+ workers + better-sqlite3 重编；复用 node-sharp；默认无浏览器，LBrowser 走 sidecar |

逐应用细节见 `images/<app>/BUILD.md`。无法移植的 8 个商店应用见
[BLOCKED-APPS.md](BLOCKED-APPS.md)。

## 3.6 可复用基础层

| 层 | 状态 | 说明 |
|---|---|---|
| `yunixintel/node-sharp` | 已发布 | Node 24.22.1 + libvips 8.18.7 + sharp 0.35.5；源码编 libvips + node-gyp；复用 `/opt/vips` 与 `/opt/node_modules/sharp` |
| LBrowser / Playwright | 本地，不发布 | 许可证不清晰；运行时镜像不含浏览器字节，挂载宿主 `/opt/apps/lbrowser:ro`；Playwright 1.57 含 PDF、Patchright 1.59 四项、跨 NAT CDP 通过 |

详见 [BASE-IMAGES.md](BASE-IMAGES.md)。

## 4. 提交与验证

构建完成后记录：镜像大小、`docker inspect` 架构、启动日志、HTTP/健康检查、digest。
统一推送到 `docker.io/yunixintel/<app>:loong64` 与 `:24.10-la5`。
`scripts/push-images.sh`（私有库）覆盖全部 115 只。
