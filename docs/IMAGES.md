# loongarch64 应用镜像

共 115 只，全部为 **linux/loong64 单架构**，在 3A6000（Loongnix 25）上构建并验证。镜像同时打两个 tag：
`loong64`（浮动）与 `24.10-la5`（与 GitHub Release 对齐）。

拉取：

```bash
docker pull yunixintel/jellyfin:loong64
```

| 镜像 | 大小 | 验证 | 说明 |
|---|---|---|---|
| `yunixintel/jellyfin` | 1.46GB | API 10.11.0 + Web 200 | .NET 9 自编；**自 2026-10-19 起内置 ImageSharp 编码器**（缩略图/Trickplay/拼图/BlurHash 全可用，含 Noto CJK 字体）；代价：纯托管性能较 Skia 慢、无 ICC 色彩管理 |
| `yunixintel/navidrome` | 1.18GB | 302 向导 + scanner | Go + 系统 taglib 2.0.2，**DSD 完整** |
| `yunixintel/vaultwarden` | 357MB | Rocket launched + Web 200 | Rust；镜像内置宿主 glibc 2.41 闭包（显式 loader 启动） |
| `yunixintel/uptimekuma` | 664MB | 302→200 | Node 20 + 源码编 sqlite3 |
| `yunixintel/mihomo` | 59MB | 204 / 152ms | scratch 单二进制，配置需挂载 |
| `yunixintel/easytier` | 26MB | 进网 ping 通 | scratch 单二进制，配置需挂载 |
| `yunixintel/syncthing` | 273MB | HTTP 200 | v2.1.6 官方 loong64 包；注意 v2 CLI 用双横线 `--home=` |
| `yunixintel/adguardhome` | 290MB | 302→200 | 官方无 loong64 资产，源码自编 + 官方前端；53 端口需映射避让宿主 dnsmasq |
| `yunixintel/memos` | 352MB | `/` 200、`/healthz` 200 | v0.31.0 源码编（官方无 loong64）；纯 Go sqlite；前端在 x64 上编（rolldown 无 loong64 binding），产物架构无关 |
| `yunixintel/gogs` | 613MB | 302→200，安装与 SQLite 验证通过 | v0.14.3 源码编；0.14 起 sqlite 已纯 Go（不需要 CGO）；镜像带 git |
| `yunixintel/filebrowser` | 290MB | `/` 200、`/login` 200 | v2.63.23 源码编；**上游 2026-09-01 已归档**，无后续安全修复；默认监听改 0.0.0.0（v2.63 默认 127.0.0.1） |
| `yunixintel/qbittorrent-ee` | 289MB | 200（Host 需匹配端口） | v5.2.4.10 官方 loong64 静态包；Host header 校验会拒绝端口映射不一致的访问，建议 `--webui-port` 与映射端口一致 |
| `yunixintel/it-tools` | 408MB | 200 | 纯静态站点 + nginx；Vite 4/rollup 3 可在龙芯本机直接编 |
| `yunixintel/excalidraw` | 439MB | 200（SPA 深路径 200） | v0.18.1；Vite 5 + rollup 4（自带 loongarch64 binding）；需 Node 22（用 /opt/node22-abi2） |
| `yunixintel/kopia` | 317MB | 401（Basic 认证）→ 200 | v0.23.1 源码编；为 loong64 打了 Stat_t.Dev/Rdev 类型补丁；Web UI 强制 Basic 认证（默认 admin/kopia） |
| `yunixintel/linkding` | 1.21GB | `/login/` 200、`/health` 200 | v1.47.0；Python 3.13 源码编 + uwsgi；cryptography 需 Rust 源码编；`UWSGI_MAX_FD=4096` 必设（否则 uwsgi 路由进程吃 8GB） |
| `yunixintel/heimdall` | 691MB | 200 | 2.8.3；PHP 8.4.26 自编（源里只有 8.3）+ nginx/php-fpm；数据在 /config（.env/sqlite/storage） |
| `yunixintel/nextcloud` | 1.48GB | `status.php` 200（installed=false，安装向导） | 33.0.10；PHP 8.3 + nginx/php-fpm；SQLite（测试用，生产建议 MySQL/MariaDB）；首次启动生成 config.php |
| `yunixintel/typecho` | 428MB | `/install.php` 200，完整安装验证 | v1.3.0；PHP 8.3 + nginx/php-fpm；**config.inc.php 与 typecho.db 在站点根目录**（不在挂载卷内，重建容器前需一并备份） |
| `yunixintel/wallabag` | 688MB | `/login` 200，登录与 quickstart 验证 | 2.6.14；PHP 8.3 + nginx/php-fpm；2.6 起无网页安装向导，entrypoint 首次启动 CLI 安装（默认 wallabag/wallabag） |
| `yunixintel/drawio` | 498MB | 200（app.min.js 10MB） | v32.5.5；直接取源码仓库预构建 `src/main/webapp`，无需 npm/maven；hash 路由 |
| `yunixintel/jackett` | 335MB | 301→302（登录） | v0.24.2867；.NET 9 源码编，自带运行时；需宿主 libstdc++ 6.0.33（已内置） |
| `yunixintel/xteve` | 1.13GB | 200 | 2.2.0.200；Go 静态编（升级 x/sys 支持 loong64）；自带 ffmpeg（占大头，可瘦身） |
| `yunixintel/one-api` | 294MB | `/` 200、`/api/status` 返回版本 | v0.6.10；三套前端主题本机编；go-sqlite3 需 CGO 静态链接（`-linkmode external -extldflags -static`） |
| `yunixintel/code-server` | 1.11GB | 200（或 302 登录） | 4.141.0 + VS Code 1.141；**必须 Node 24**（Node 20 缺 `module.registerHooks`）；自编静态 ripgrep 15.2 |
| `yunixintel/dpanel` | 566MB | 200 | v1.11.1；Go + CGO sqlite（CGO=0 会 panic）；需 docker.sock；8807 端口 |
| `yunixintel/shiori` | 290MB | 200 | v1.8.0；Go 静态编；8080 端口；生产建议设 `SHIORI_HTTP_SECRET_KEY` |
| `yunixintel/jellyseerr` | 1.56GB | 307→`/setup` 200 | v3.5.0；Next 16 用 WASM SWC（无 loong64 binding）；sharp 不可用 → `images.unoptimized`；5055 端口 |
| `yunixintel/audiobookshelf` | 1.50GB | 200 | v2.37.1；Node 22 + sqlite3/nusqlite3 源码编；前端在 x64 构建（Tailwind oxide 无 loong64）；13378 端口 |
| `yunixintel/calibre-web` | 657MB | 302→`/login` 200 | 0.6.27；Python 3.11 + Rust 源码编 lxml/nh3/cryptography；8083 端口；书库挂 /books |
| `yunixintel/homarr` | 819MB | 307→`/init` 200 | v2.6.0；Next 16 WASM SWC + Node 24 + redis；Bun/Turbo 无 loong64 改用 pnpm；7575 端口 |
| `yunixintel/openwebui` | 1.8GB | 200，`/api/config` 200 | v0.12.3 **轻量模式**：无 torch/onnxruntime/whisper/OCR，聊天对接 Ollama/OpenAI 正常；本地 RAG 需外部 pgvector |
| `yunixintel/kodexplorer` | 507MB | 302→登录 200 | 4.55；PHP 8.3 + nginx/php-fpm；首启为环境检查/设置管理员；默认 admin/admin |
| `yunixintel/homeassistant` | 2.53GB | 302→`/onboarding.html` 200 | Core 2026.10.2；Python 3.14 自编；cryptography/grpcio/Pillow/aiohttp 等全源码编；cloud/camera 集成需运行期编译器，未预装 |
| `yunixintel/sonarr` | 368MB | 200（API 401 未认证正常） | v4.0.20；.NET 9 运行时 + 自写 Mono.Posix loong64 兼容层；8989 |
| `yunixintel/radarr` | 367MB | 200 | v6.4.4；同上；自编译 e_sqlite3；7878 |
| `yunixintel/tautulli` | 390MB | 303→`/welcome` 200 | v2.18.2；纯 Python；8181 |
| `yunixintel/jellystat` | 833MB | 200，`/auth/isConfigured` 200 | 1.1.12；Node 20 + 降级 Vite 6；**需要外部 PostgreSQL**；3000 |
| `yunixintel/stirling-pdf` | 1.17GB | 200 | v3.2.0；官方 jar + Java 25；精简版未装 LibreOffice/OCR，相关端点自动禁用；8080 |
| `yunixintel/wizarr` | 1.22GB | 302→`/setup/` 200 | v2026.10.1；Python 3.13 自编；前端静态资源取自官方 amd64 镜像（架构无关）；5690 |
| `yunixintel/gitea` | 666MB | 200（安装页/SQLite 已验） | v28.2.0；Go 1.27 自编；modernc SQLite；入口脚本生成 app.ini；3000 |
| `yunixintel/miniflux` | 290MB | 200（**仅 PostgreSQL**） | v2.3.3；上游已删 SQLite 支持，必须提供 PostgreSQL DSN；8080 |
| `yunixintel/portainer` | 373MB | 200 | 2.45.2 LTS；Go 自编 + 前端本机 pnpm/webpack；需挂 docker.sock；9000 |
| `yunixintel/nginx-proxy-manager` | 774MB | 200，`/api/` OK | v2.16.0；Node 22 + nginx；前端在 x64 编 dist；自写 entrypoint 替代 s6-overlay；81/443 |
| `yunixintel/firefly-iii` | 821MB | 302→`/install` 200 | v6.7.9；PHP 8.5 自编（上游要求 ≥8.5）+ nginx；SQLite 自动迁移/种子；8080 |
| `yunixintel/phpmyadmin` | 581MB | 200 | 5.2.3；PHP 8.3 + nginx/php-fpm；无需数据库即可开登录页；8080 |
| `yunixintel/freshrss` | —（Hub 154MB 压缩） | 302→登录页 | 1.30.1；PHP 8.3 + nginx/php-fpm；SQLite 自动安装（admin/adminadmin）；8080 |
| `yunixintel/prowlarr` | 358MB | 200（API 401 正常） | 2.6.5；.NET 9 + 自编 Mono.Posix/e_sqlite3；9696 |
| `yunixintel/bazarr` | 2.28GB | 200，API 版本 1.6.2 | 1.6.2；Python 3.11 + lxml/Pillow 源码编；webrtcvad 补 loongarch 分支；含 ffmpeg/7za；6767 |
| `yunixintel/homer` | 371MB | HTTP 200，title/config 正常 | v26.08.3；openEuler nginx 1.24 + 官方静态包；8080 |
| `yunixintel/paperless-ngx` | 2.53GB | 302→登录 200；OCR、消费入库、重启持久化通过 | 3.3.2；qpdf 12.4.2 自编（pikepdf 10.17 要求）；tesseract eng/chi_sim/osd；AI 关闭、unpaper 无；单容器含 redis/celery worker/beat/consumer；8000 |
| `yunixintel/dashy` | 379MB | HTTP 200，title/conf 正常 | 4.8.0；官方预构建 `dist/` + nginx 1.24；配置挂载 `/usr/share/nginx/html/conf.yml`；8080 |
| `yunixintel/watchtower` | 14.7MB | `--help`；`--run-once --label-enable` 扫描 0 容器 | v1.7.1；Go 静态二进制 + CA 证书；需挂 `/var/run/docker.sock`；`--label-enable` 只更新带标签容器 |
| `yunixintel/changedetection` | 3.51GB | HTTP 200；Firefox 截图落盘；`image_ssim_diff` baseline/二次比对通过；Selenium 4 步表单（输入/点击）执行成功 | 0.60.9；SQLite；内置 Firefox 140.11ESR + geckodriver 0.37.1；Selenium 步骤适配层支持 Goto/点击/输入/等待/选择/按键/滚动/JS/复选框等（不再依赖 Playwright）；OpenCV 4.5.2 + numpy 1.26.4，SSIM 可用；Chrome 远程仍可 `WEBDRIVER_BROWSER=chrome` + `WEBDRIVER_URL`；5000 |
| `yunixintel/caddy` | 57MB | `caddy version` 2.11.7；默认页 HTTP 200 | 纯 Go 静态编；scratch + CA；默认 Caddyfile 监听 8080；挂载自己的 Caddyfile 覆盖，80/443/8080 |
| `yunixintel/dozzle` | 68MB | v11.3.3；HTTP 200；日志 `Connected to Docker` | 前端 Bun 1.4.3/Vite 在 x86 WSL2 构建（产物架构无关），Go 1.27.2 在 A 编 loong64；scratch；需挂 docker.sock；8080 |
| `yunixintel/ntfy` | 274MB | `/v1/health` healthy；UI 200；publish 成功 | 2.32.0；Go CGO（go-sqlite3）在 openEuler 容器编；前端 Vite 在 x86 WSL2 构建；8080；挂 `/var/cache/ntfy`、`/etc/ntfy` |
| `yunixintel/gotify` | 261MB | `/health` green；UI 200；`/version` v3.1.1 | 3.1.1；Go CGO（go-sqlite3）在 openEuler 容器编；UI Vite 8 在 x86 WSL2 构建；8080；数据卷 `/data` |
| `yunixintel/node-exporter` | 17MB | `/metrics` 200，含 `node_cpu_seconds_total` | 1.12.1；纯 Go 静态编；scratch + CA；9100；采集宿主指标需挂 `/proc`、`/sys`、`/` |
| `yunixintel/prometheus` | 407MB | `/-/healthy` 200；UI 200；`/api/v1/status/buildinfo` 3.15.0 | 3.15.0；UI 用 Vite 8 在 x86 WSL2 构建，Go `-tags builtinassets` 嵌入；TSDB `/prometheus`；9090 |
| `yunixintel/pihole` | 287MB | `/admin/` 200；`pihole -g` 拉取 1 条 adlist；`dig` 被拦截域名返回 NXDOMAIN | FTL 6.8 + web 6.6.1；C/C++，静态 nettle 3.10；上游 `pihole` CLI + `gravity.sh` + `pihole-adlist`（add/list/remove）；DNS 53 / Web 80；`/etc/pihole` |
| `yunixintel/gatus` | 35MB | `/` 200；`/api/v1/endpoints/statuses` 200 | 5.37.0；Go 静态编；自带 `web/static`；scratch；默认配置监控 Prometheus；8080 |
| `yunixintel/mealie` | 2.17GB | `/` 200；`/api/app/about` version 3.29.0；SQLite 初始化；健康检查 healthy | 3.29.0；Python 3.14.8 自编；Nuxt 前端 x86 构建；Rust 1.99 编原生模块；`/app/data`；9000；UID 911；HEIF/HEIC 不支持 |
| `yunixintel/chinesesubfinder` | 1.04GB（Hub 385MB） | `/` 200；健康检查 healthy | v0.55.2 Lite；Go + Quasar；go-webrtcvad 补 LoongArch；`/config`、`/media`；19035；内置 ffmpeg |
| `yunixintel/lanraragi` | 738MB（Hub 273MB） | `/` 200、标题 LANraragi、Redis 启动；healthy | 0.9.81；Perl + 126 CPAN 模块；内置 Redis；PERL5LIB 需带 loongarch64 目录；3000 |
| `yunixintel/owntone` | 980MB（Hub 355MB） | `/` 200；healthy | 29.3；DAAP/AirPlay；容器内 dbus + avahi；`/srv/music`；3689 |
| `yunixintel/mymind` | 约 330MB（Hub 130MB） | `/` 200、全部静态资源 200；healthy | 纯静态思维导图 + nginx；无后端；80 |
| `yunixintel/webvirtcloud` | 约 600MB（Hub 235MB） | 登录页 200、静态资源 200、migrate 完成；healthy | Django 4.2 + libvirt + noVNC；gunicorn/novncd/nginx；`data` 与 `.ssh` 需持久化；80 |
| `yunixintel/penpot-backend` | 约 900MB（Hub 710MB） | 迁移至 0153、6060、`/api` 200 | 2.18.3；官方 uberjar + openEuler JDK 21；需 PostgreSQL/Redis；`PENPOT_SECRET_KEY` 必填 |
| `yunixintel/penpot-frontend` | 约 350MB（Hub 274MB） | `/` 200、Penpot 标题、API 代理 200；healthy | 2.18.3 静态前端 + nginx；反代 backend；8080 |
| `yunixintel/hermes` | 3.68GB（Hub 1.23GB） | `/` 200、`/health` 200、双进程；healthy | Hermes agent + WebUI；Python 3.14.8；8787；HEIC 不支持；镜像含 gcc/rust |
| `yunixintel/zigbee2mqtt` | 649MB（Hub 217MB） | onboarding `/` 200、udevadm 255、serialport native 可加载、MQTT 连接 OK；healthy | 2.14.2；Node 24 + pnpm；serialport 源码编；需 USB 协调器；`/app/data`；8080；UID 1101 |
| `yunixintel/smartctl-exporter` | 约 123MB（Hub） | `/metrics` 200、NVMe SMART 可读；healthy | v0.15.0；Go + smartmontools；9633；需 SYS_RAWIO/SYS_ADMIN 与设备直通；替代 Scrutiny |
| `yunixintel/sftpgo` | 422MB（Hub 149MB） | Web 302→setup、管理员登录 200、SQLite/host key 生成；healthy | v2.7.6；Go+CGO SQLite；Web 8080/SFTP 2022；UID 1103；首次安装页创建管理员 |
| `yunixintel/bookstack` | 约 600MB（Hub 214MB） | MariaDB 迁移完成、`/login` 200；healthy | v26.09.2；PHP 8.3 + nginx/php-fpm；必须 MariaDB；`storage`/`public/uploads` 持久化；80 |
| `yunixintel/vikunja` | 约 169MB（Hub） | `/` 200、`/health` 200、`/api/v1/info` v2.7.1、注册/登录 200；healthy | v2.7.1；Vue x86 构建 + Go CGO SQLite；3456；`/db` 与 files 持久化；UID 1104 |
| `yunixintel/piwigo` | 约 550MB（Hub 179MB） | 首次自动安装成功、`/` 200、`/identification.php` 200；healthy | 16.4.0；PHP 8.3 + nginx/php-fpm；必须 MariaDB；`local`/`_data`/`galleries`/`upload` 持久化；80 |
| `yunixintel/go2rtc` | 约 111MB（Hub） | `/` 200、`/api/streams` `{}`、RTSP 8554/WebRTC 8555 监听；healthy | 1.9.14；Go 单二进制；1984 API；`/config`；UID 1109；默认无认证 |
| `yunixintel/scrutiny` | 242MB（Hub 145MB） | `/web/` 200、`/api/health` true、NVMe collector 读到型号/温度/通电小时；healthy | 0.9.5 + SQLite metrics 补丁；不依赖 InfluxDB；`/opt/scrutiny/config`；8080；需设备直通；collector 外部调度 |
| `yunixintel/headscale` | 约 137MB（Hub） | `/health` 200、metrics 9090、users/preauthkeys 成功；healthy | v0.29.5；Go 单二进制；无 Web UI；`/etc/headscale`、`/var/lib/headscale`；8080/9090；UID 1106 |
| `yunixintel/backrest` | 约 160MB（Hub） | Web UI `/` 200、restic 0.19.1 loong64、oplog 迁移完成；healthy | v1.14.1；`/data`、`/config`、`/cache`；9898；UID 1108；首次 UI 建账号/仓库 |
| `yunixintel/authelia` | 约 139MB（Hub） | `/api/health` 200、门户 `/` 200、SQLite 迁移 0→29；healthy | v4.39.28；CGO SQLite；自动生成配置/用户/密钥；`/config`；9091；UID 1107 |
| `yunixintel/ente-server` | 约 123MB（Hub） | `/ping` 200、PostgreSQL 迁移、MinIO 三桶可用；healthy | ente server master；需 PostgreSQL + S3/MinIO；`/data/museum.yaml`；8080；UID 1105 |
| `yunixintel/ente-web` | 约 103MB（Hub） | 10 个端口全部 200、photos `/gallery` 200、WASM `application/wasm`、占位符 0；静态导出 | 10 个 Next.js 16.4.2 应用静态导出；nginx 1.30；3000–3006/3008–3010；`ENTE_API_ORIGIN` 启动时注入，重启可改 |
| `yunixintel/metube` | 约 441MB（Hub） | `/` 200、`POST /add` 下载 YouTube 短视频成功、文件合并、healthy | 2026.10.23；Python 3.13.7 + yt-dlp 2026.10.21 + Node 24 + ffmpeg 6.1.1；`/downloads`；8082；UID 1111；无 Brotli/bgutil-pot |
| `yunixintel/sabnzbd` | 约 139MB（Hub） | `/wizard/` 200、API version 5.1.3、par2 create/verify 通过、healthy | 5.1.3；Python 3.11 + system cryptography；par2cmdline 0.8.1 + unrar 7.13；`/config`、`/downloads`；8080；UID 1112；无 orjson |
| `yunixintel/mediamtx` | 约 108MB（Hub） | RTSP 发布 ready、HLS 200、WebRTC 页面 200、API 容器内 200；healthy | 1.9.3；Go 单二进制；8554/1935/8888/8889/8890/9997；API 默认开；UID 1115；无持久化 |
| `yunixintel/registry` | 约 124MB（Hub） | 匿名 401、admin 认证通过、crane 推送/拉取、`_catalog` 正常；healthy | 3.1.2；Go 单二进制；`/var/lib/registry`、`/auth`；5000；UID 1121；首启生成 htpasswd；无 TLS |
| `yunixintel/unpackerr` | 约 100MB（Hub） | v0.9.9 启动、配置自动生成、假 Sonarr 轮询、`pgrep` healthy | 0.9.9；Go 单二进制；无 UI/端口；`/config`、`/downloads`；UID 1123；需 x/sys 升级补丁；unrar 7.13 + 7za |
| `yunixintel/pocket-id` | 约 136MB（Hub） | `/` 200、`/healthz` 204、首启建库/密钥；healthy | 2.9.0；SvelteKit 前端 x86 构建后 embed；Go 单二进制；`/data`；1411；UID 1122；首启生成加密密钥；无邮件/SCIM 联调 |
| `yunixintel/readeck` | 约 118MB（Hub） | `/` 303→引导页 200、首启生成配置与 SQLite；healthy | 0.9.2；Go CGO（mattn sqlite）+ gulp 前端；`/data`；8000；UID 1117；CGO-free 路径因 modernc 旧版不可用 |
| `yunixintel/wg-easy` | 约 169MB（Hub） | DB 迁移、wg0.conf、302→`/setup/1`、卷持久化、healthy；真实隧道未验 | 15.4.0；Node 24 + Nuxt + libsql（龙芯绑定）；hash-wasm 替代 argon2；51820/udp、51821/tcp；需 NET_ADMIN/SYS_MODULE；IPv4-only |
| `yunixintel/komga` | 约 318MB（Hub） | 94+2+1 迁移、`/` 200、health UP、重启持久化、最小 CBZ 扫描/单页读取；healthy | 1.29.1；官方 jar + 自编 loongarch64 libsqlitejdbc；JDK 21；`/config`、`/data`（可只读）；25600；UID 1110 |
| `yunixintel/node-sharp` | 约 157MB（Hub） | `sharp.versions` vips 8.18.7、JPEG/PNG/WebP 输出非空；ldd 无缺失 | 基础镜像：Node 24.22.1 + libvips 8.18.7 + sharp 0.35.5；复用 `/opt/vips`、`/opt/node_modules/sharp`；HEIF/JXL 未开 |
| `yunixintel/karakeep` | 约 470MB（Hub） | 健康检查、首用户 admin、静态抓取、banner WebP、Next 图片优化、重启持久化、LBrowser 截图/PDF 通过 | 0.34.1 基础版；SQLite + Next 16 + better-sqlite3；默认无浏览器，用 `BROWSER_WEB_URL` 接 LBrowser sidecar；搜索需 Meilisearch；`/data`；3000；UID 1116 |
| `yunixintel/autobrr` | 约 131MB（Hub） | `/` 200、`/api/healthz/liveness` 200、SQLite 迁移；healthy | master 2026-10；Go 单二进制 + 内嵌 Vue；`/config`；7474；UID 1113；默认无认证 |
| `yunixintel/matomo` | 约 193MB（Hub） | `/index.php` 200、安装向导可打开、PHP 扩展齐全；healthy | 5.14.2；PHP 8.3 + nginx/php-fpm；必须 MariaDB；`config`/`tmp` 持久化；80 |
| `yunixintel/woodpecker-server` | 约 133MB（Hub） | `/` 200、内嵌 UI 资源 200、`/api/healthz` 204；SQLite 迁移；healthy | 3.19.0；**必须配置 forge**（Gitea/GitHub）才能启动；`/var/lib/woodpecker`；8000/9000；自动生成 agent/grpc secret；UID 1114 |
| `yunixintel/woodpecker-agent` | 约 117MB（Hub） | 注册到 server、`/healthz` 200；healthy | 3.19.0；需 `docker.sock` + `--group-add`；`WOODPECKER_AGENT_SECRET` 与 server 一致；3000 仅健康检查；UID 1114 |
| `yunixintel/nocodb` | 1.58GB | `/api/v1/health` 200；`/` 302→`/dashboard/` 200；SQLite 初始化；健康检查 healthy | 0.301.3 + Node 24；npm 需 `--ignore-scripts`；sqlite3 手动编 loong64；自定义 runner；`/data`；8080；UID 1000 |
| `yunixintel/apprise-api` | 1.03GB | `/` 200；`/status` OK；stateless `/notify/` 进入通知流程；健康检查 healthy | 2.0.1 + Python 3.11；系统 cryptography/gevent；pycares 需 cmake；nginx+supervisor+gunicorn；`/config`、`/attach`、`/plugin`；8000 |
| `yunixintel/homebox` | 346MB | `/` 200；`/api/v1/status` health=true；版本 v0.10.3；SQLite 初始化；健康检查 healthy | v0.10.3；Nuxt 静态前端 embed；Go 1.27；modernc sqlite 升到 1.61 支持 loong64；`/data`；7745；UID 1000；默认允许注册 |
| `yunixintel/minio` | 483MB | `/minio/health/live` 200；Console 9001 200；数据目录初始化；RELEASE 版本串；健康检查 healthy | RELEASE.2025-10-15T17-29-55Z；Go 源码编；`/data`；9000/9001；UID 1000；必须设 `MINIO_ROOT_USER/PASSWORD`；AGPLv3；单盘无纠删码 |
| `yunixintel/actual-budget` | 554MB | 数据库迁移完成；`/` 200；标题 Actual；`actual-server --version` v26.10.0；`/data` 初始化；健康检查 healthy | 26.10.0 + Node 24.22.1；`/opt/node24`；`/data`；5006；UID 1002；better-sqlite3 手动编 loong64；无内置 TLS |
| `yunixintel/alertmanager` | 274MB | `/-/healthy`、`/-/ready` 200；UI/API 正常；amtool 推警成功 | 0.34.1；Elm + Vite 前端在 x86 WSL2 构建后 `go:embed`；Go 静态编；openEuler + curl 健康检查；9093 Web / 9094 gossip；nobody 运行；默认只收不发通知 |
| `yunixintel/postgres` | 378MB | `pg_isready` healthy；SCRAM TCP 登录；重启持久化；miniflux 迁移 132 版后 200 | 15.18；openEuler 包；entrypoint 支持 `POSTGRES_USER/PASSWORD/DB/HOST_AUTH_METHOD`；`PGDATA=/var/lib/postgresql/data`；5432；日志走 stdout |
| `yunixintel/redis` | 296MB | `PING`；`SET/GET`；重启持久化；密码认证通过 | 7.2.14；openEuler 包；AOF+RDB；`/data`；6379；默认 protected-mode no，公网必须设 `REDIS_PASSWORD` |
| `yunixintel/mosquitto` | 290MB | 匿名 pub/sub；retained 消息重启后仍可订阅；健康检查 healthy | 2.0.20；openEuler EPOL；1883；默认 `allow_anonymous true`，公网须关匿名并配 passwd；含 pub/sub/passwd 工具；`/mosquitto/data` |
| `yunixintel/mariadb` | 549MB | 初始化；root/app TCP 登录；建表；重启持久化；特殊字符密码通过 | 10.11.18；openEuler 包；`MYSQL_*` 初始化；`/var/lib/mysql`；3306；root 仅 localhost；日志走 stderr；UID/GID 27 |
| `yunixintel/node-red` | 499MB | `/` 200；标题 Node-RED；版本 5.0.8；`/data` 生成 settings/flows；重启后 200 | 5.0.8 + Node 24.22.1；基于 `yunixintel/node`；多阶段构建；1880；`/data`；保留 npm 支持 palette；UID 1001 |
| `yunixintel/grafana` | 1.18GB | `/api/health` database ok；`/login` 200；登录页 JS 200；SQLite 迁移；健康检查 healthy | 13.2.4；前端 WSL Node22/Yarn4 webpack 构建并删 source map；Go 1.27/CGO0 `-tags oss`；UID/GID 472；`/var/lib/grafana`；3000；默认 admin/admin；不含 image renderer |
| `yunixintel/memcached` | 354MB | 原始协议 `set/get`；`stats` 1.6.42；健康检查 healthy | 1.6.42；openEuler 包；默认 64MB/1024 连接/4 线程；`MEMCACHED_*` 可调；11211；无认证无持久化，禁止公网暴露 |
| `yunixintel/homebridge` | 583MB | Homebridge 2.4.0 启动；UI 8581 200；hb-service 同时拉起 UI 与核心；健康检查 healthy | 2.4.0 + Config UI 5.29.0 + Node 24.22.1；基于 `yunixintel/node`；node-pty 源码编 loong64；hb-service；建议 host 网络；`/homebridge`；8581/51826；UID 1000 |
| `yunixintel/node` | 420MB | `node -v` 24.22.1、`npm -v` 11.19.1、`corepack` 0.36.0 正常 | Node.js 24.22.1 linux-loong64（unofficial-builds）；openEuler 24.03；`/opt/node24`；Node 22.23.3 保留 `:22.23.3` |
| `yunixintel/rest-server` | 250MB | `?create=true` 建库；config 写入/读取；Basic 认证 401/200 | 0.14.0；Go 静态二进制；openEuler + httpd-tools；`/data`；8000；默认开认证，先 create_user 再重启；无 TLS |

> 2026-10-21：新增 `alertmanager`、`postgres`、`redis`、`mosquitto`、`mariadb`、`node-red`、`grafana`、`memcached`、`homebridge`、`rest-server`、`node`，均已推送双 tag。Node-RED 5.0.8、Homebridge 2.4.0 已改用 Node 24.22.1；对应 digest 为 `6f46a30d…8fca`、`c94527ee…825b`、`424db4cd…3137`、`d55c5799…edce`、`bf37b65e…5e00`、`f44460c6…8cfc`、`5b4bd1fb…f282`、`085ae164…15ba`、`dafe9de5…ef83`、`53624433…a19a`、`0f4d19bb…4fb5`。
> 2026-10-20：新增 `homer`、`paperless-ngx`、`dashy`、`watchtower`、`changedetection`、`caddy`、`dozzle`、`ntfy`、`gotify`、`node-exporter`、`prometheus`、`pihole`、`gatus`，均已推送 Docker Hub，双 tag 均为 `linux/loong64`。
> OpenCV/SSIM 的可复用配方见 [OPENCV-SSIM.md](OPENCV-SSIM.md)。

## 运行示例

```bash
# jellyfin
docker run -d --name jellyfin --network=host \
  -v jf_config:/config -v /你的媒体:/media:ro yunixintel/jellyfin:loong64

# navidrome
docker run -d --name navidrome --network=host \
  -v nd_data:/data -v /你的音乐:/music:ro yunixintel/navidrome:loong64

# vaultwarden
docker run -d --name vaultwarden --network=host -v vw_data:/data \
  -e ROCKET_PORT=8443 yunixintel/vaultwarden:loong64

# uptimekuma
docker run -d --name uptimekuma --network=host \
  -v uk_data:/app/data yunixintel/uptimekuma:loong64

# mihomo（配置自行准备）
docker run -d --name mihomo --network=host --privileged \
  -v /你的配置目录:/etc/mihomo yunixintel/mihomo:loong64 -d /etc/mihomo

# easytier（配置自行准备）
docker run -d --name easytier --network=host --privileged \
  -v /你的/network.toml:/etc/easytier/network.toml:ro \
  yunixintel/easytier:loong64 --config-file /etc/easytier/network.toml
```

## 注意

- 仅 loongarch64；x86/ARM 机器无法运行。
- `mihomo`/`easytier` 镜像不含配置（配置含密钥，不入镜像）。
- jellyfin 已内置 ImageSharp 编码器（缩略图/Trickplay/拼图/BlurHash 可用），代价是无 ICC 色彩管理、性能低于 Skia。
- vaultwarden 的 Web 客户端为官方静态包（架构无关）。
- CasaOS 镜像暂未发布（磁盘能力验证完成前撤下）；其安装包与镜像只在本地/验证机。
- podman bridge 网络需宿主内核 nft conntrack；缺该模块时用 host/none。
