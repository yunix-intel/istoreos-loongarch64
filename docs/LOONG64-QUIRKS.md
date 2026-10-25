# 龙芯版应用差异清单（商店描述来源）

用途：CasaOS/iStore 的应用详情页必须显示“龙芯版说明”，不能只写“可安装”。
本文件是差异的**人工维护清单**，商店生成器还必须把 `images/catalog.json` 的 `notes`
一并渲染到卡片描述中。没有差异的应用也要写“未发现行为差异”。

状态：初始清单。每次新增/更新镜像时同步本文件；商店阶段（NEXT-PLAN §9.5）逐项核对。

| 应用 | 与上游/原商店应用的行为差异 | 缺失或受限功能 | 额外依赖/启动注意 |
|---|---|---|---|
| Scrutiny | 使用 SQLite metrics 补丁，不再依赖 InfluxDB；历史数据在 SQLite | 不迁移旧 InfluxDB 历史；无保留/降采样任务；collector 需外部 cron/exec 触发 | 需 `SYS_RAWIO`/`SYS_ADMIN` 与设备直通；运行镜像含 libstdc++/libgcc |
| Penpot | 前后端拆两个镜像；后端用 JDK 21 跑官方 jar | 无 exporter（PDF/PNG 导出 502）；无 admin-console/MCP | 需 PostgreSQL + Redis；`PENPOT_SECRET_KEY` 必填 |
| Hermes | Python 3.14 独立构建；镜像保留 gcc/rust | HEIC/HEIF 不支持；`computer_use` 在 loongarch64 不可用 | 默认无 WebUI 密码；镜像 3.68GB |
| BookStack | PHP 8.3 + nginx/php-fpm；自动生成 `.env` | 必须 MariaDB/MySQL，不支持 SQLite | `storage`/`public/uploads` 持久化；首次用 artisan 建管理员 |
| Piwigo | 首次启动自动 POST `install.php` | 必须 MariaDB/MySQL | `local`/`_data`/`galleries`/`upload` 持久化 |
| Vikunja | Vue 前端在 x86 构建；Go CGO SQLite | 默认允许注册，生产需关闭 | `service.interface=0.0.0.0:3456`；`PUBLICURL` 必须正确 |
| SFTPGo | Go CGO SQLite；首次进入安装页 | 默认不创建管理员；FTP/WebDAV 默认关闭 | `/srv/sftpgo/data`、`/var/lib/sftpgo` 持久化；公网需 TLS |
| Zigbee2MQTT | Node 24 + pnpm；serialport 源码编 | 无 USB 协调器时容器退出 | 需 `/dev/ttyACM0` 或 `/dev/serial/by-id/*`；`dialout` 组 |
| smartctl_exporter | 仅暴露 Prometheus 指标，无 UI/历史 | 无内置历史库/告警 | 需 `SYS_RAWIO`/`SYS_ADMIN`、设备直通；默认无认证 |
| go2rtc | 单二进制，无 ffmpeg 依赖 | 默认无摄像头流配置；无认证 | 1984 API/8554 RTSP/8555 WebRTC；跨 NAT 配 candidates |
| Headscale | 单二进制，无 Web UI；CLI/API 管理 | 无图形界面；gRPC 默认仅本机 | `HEADSCALE_SERVER_URL` 必填；`/etc/headscale` 与 `/var/lib/headscale` 持久化 |
| Backrest | 前端 x86 构建后内嵌；自带 restic 0.19.1 | 首次需 UI 建账号/仓库；默认无认证 | `/data`/`/config`/`/cache` 持久化；备份源目录需额外挂载 |
| Authelia | 自动生成配置/用户库/密钥；单机 SQLite | 无内置 TLS；默认 one_factor，forward-auth 需反代配置 | `AUTH_DOMAIN`/`AUTH_URL` 必须是 HTTPS 正式域名；`/config` 持久化 |
| Ente server | 仅 API；museum.yaml 首次启动生成 | 无 Web 图库（需配 `ente-web`） | `/data/museum.yaml` 含密钥必须备份；S3 bucket 需预先创建 |
| Ente web | 10 个 Next 应用纯静态导出；nginx | 无 Next 服务端/API/图片优化器；未知路径回退 index.html；不保证逐字节可复现 | 必须设 `ENTE_API_ORIGIN`；10 个端口；升级 origin 后重启容器生效 |
| Autobrr | 前端 x86 构建后内嵌；SQLite | 默认无认证；需自配 IRC/下载器 | `/config` 持久化；公网加反代认证 |
| Matomo | 官方完整包；PHP 8.3 | 首次必须走 Web 安装向导；无 CLI 安装 | 必须 MariaDB/MySQL；`config`/`tmp` 持久化；归档需 cron |
| Jellyseerr | Next 16 用 WASM SWC 在 x86 构建；sharp 不可用，图片优化关闭 | 无 Next 图片优化器 | 需 Sonarr/Radarr 等上游服务；5055 |
| qBittorrent-EE | 官方 loong64 静态包；WebUI 校验 Host header | 映射端口与 WebUI 端口不一致会拒绝访问 | 让 WebUI 端口与宿主映射端口一致 |
| Homarr | Next 16 WASM SWC + Node 24；未用 Bun/Turbo | Bun/Turbo 构建链未移植 | 需 Redis；7575 |
| Open WebUI | 仅推理模式，不含 torch/onnxruntime/whisper/OCR 与模型 | 本地推理/语音/OCR 不可用；RAG 需外部 pgvector | 需外部 Ollama/OpenAI 兼容服务；RAG 需 PostgreSQL+pgvector |
| Paperless-ngx | qpdf 12.4.2 自编；AI 关闭；未装 unpaper | 无 AI 分类/实体识别；无 unpaper 后处理 | 需 Redis + celery worker/beat/consumer；8000 |
| Stirling PDF | 官方 jar + Java 25 | 未装 LibreOffice/OCR，相关转换不可用 | 8080 |
| code-server | 4.141.0 + VS Code 1.141；必须 Node 24；自编静态 ripgrep | Node 20 缺 `module.registerHooks`，不能替换运行时 | 8443；持久化 `/home/coder` |
| ChangeDetection | Firefox 140.11 ESR + geckodriver/Selenium，不是 Playwright；SSIM 用 numpy 1.26.4 | 无本地 Chrome；可配远程 Chrome WebDriver | `--shm-size=1g`；5000；持久化 `/datastore` |
| File Browser | 上游 2026-09-01 已归档；镜像默认监听 0.0.0.0 | 无上游安全更新 | 8080；持久化 `/srv` 与数据库 |
| Miniflux | 上游已删 SQLite，必须 PostgreSQL DSN | 不支持 SQLite | 需 PostgreSQL；8080 |
| Jellystat | Node 20 + Vite 6 | 无 SQLite 路径，必须外部 PostgreSQL | 需 PostgreSQL；3000 |
| MinIO | Go 源码编；单目录无纠删码 | 无纠删码/多盘冗余；无内置 TLS | 必须设 `MINIO_ROOT_USER/PASSWORD`；AGPLv3；9000/9001 |
| Grafana | 前端 x86 构建；Go CGO-free | 未内置 renderer；默认 admin/admin | 3000；持久化 `/var/lib/grafana` |
| Pi-hole | FTL 6.8 源码编，版本自报 UNKNOWN；内置 CLI 与 pihole-adlist | 需 host 网络；宿主 dnsmasq 占 53 时不可用 | 53/tcp+udp、80；持久化 `/etc/pihole` |
| AdGuard Home | 官方无 loong64 资产，源码编 + 官方前端 | 53 端口需避让宿主 dnsmasq | 建议 host 网络；3000 Web；持久化 work/conf |
| Nginx Proxy Manager | 前端 x64 构建；自定义 entrypoint 替代 s6-overlay | s6-overlay 进程管理未完全复刻 | 81/443；持久化 data/letsencrypt |
| REST Server | Go 静态编，约 12MB | 默认开认证；无 TLS | 8000；用 httpd-tools 的 htpasswd 建用户 |
| Redis | openEuler 7.2.14 包；AOF+RDB | 默认 protected-mode no，必须配密码或限制网络 | 6379；持久化 `/data` |
| Mosquitto | openEuler 2.0.20 包 | 默认 allow_anonymous true，公网必须配 passwd | 1883；持久化 `/mosquitto/data` |
| Memcached | openEuler 1.6.42 包；默认 64MB/1024 连接 | 无认证、无持久化，禁止公网暴露 | 11211；用 `MEMCACHED_*` 调整 |
| Homebridge | 2.4.0 + Config UI 5.29.0 + Node 24；node-pty 源码编 | 建议 host 网络；默认配对码需改 | 8581/51826；持久化 `/homebridge` |
| WebVirtCloud | Django 4.2 + Python 3.11 + libvirt + noVNC | 需真实 libvirt/KVM 与 SSH 凭据；noVNC WebSocket 需反代 | 80；持久化 data 与 `.ssh` |
| LANraragi | Perl 0.9.81 + 126 个 CPAN 模块；内置 Redis | 默认无认证 | 3000；持久化 content/thumb/database；UID 9001 |
| OwnTone | DAAP/DACP/AirPlay；运行期需 dbus/avahi | AirPlay 发现依赖宿主网络与 avahi | 3689；挂载 `/srv/music` 与缓存 |
| Apprise API | Python 3.11 + 系统 cryptography/gevent；nginx+supervisor+gunicorn | 默认无认证/无 TLS | 8000；持久化 `/config`、`/attach`、`/plugin` |
| MeTube | Python 3.13 自编；Angular 前端 x86 构建 | 无 Brotli 解压；无内置 `bgutil-pot`（部分 YouTube 视频需 cookies/远程 provider）；ffmpeg 为 6.1.1 而非上游 8.1 | `/downloads` 持久化并 `chown 1111`；默认 `YTDL_OPTIONS` 用 Node 24 作 JS runtime；8082 |
| SABnzbd | Python 3.11 + venv；par2/unrar 源码编 | 无 orjson（ujson 回退，性能略低）；unrar 为闭源 freeware | `/config`、`/downloads` 持久化；UI 根路径 `/` 不是 `/sabnzbd/`；8080 |
| MediaMTX | Go 单二进制；配置内嵌 | 无 Web 管理界面/持久化；API 默认仅本机白名单；`runOnInit` 等同容器内执行命令 | 8554/1935/8888/8889/8890/9997；NAT 后 WebRTC 需配 additional hosts；与 go2rtc 二选一 |
| Registry | Go 单二进制；首启生成 htpasswd | 无 Web UI、无 TLS、无多实例共享存储；删除后需手动 GC | `/var/lib/registry` 与 `/auth` 持久化；`/auth/password` 是唯一密码来源；Docker CLI 需 insecure-registries |
| Unpackerr | Go 单二进制；需升 x/sys 才支持 loongarch64 | 无 Web UI/端口；健康检查仅进程存活；未接真实 *arr | `/config`、`/downloads` 持久化且路径必须与 *arr 一致；unrar 闭源 freeware；UID 1123 |
| Pocket ID | SvelteKit 前端 x86 构建后 embed；Go 单二进制 | 未做邮件 SMTP/SCIM/Passkey 全链路；与 Authelia 二选一 | `/data` 必须持久化（含加密密钥）；`APP_URL` 必填为外部地址；1411；UID 1122 |
| Readeck | gulp 前端 x86 构建；Go 用 CGO/mattn sqlite | CGO-free 的 modernc 旧版缺 loongarch64 定义；未做完整抓取联调 | `/data` 持久化；8000；UID 1117；与 Wallabag/Shiori 重叠 |
| wg-easy | v15.4.0；Nuxt 在龙芯原生构建；libsql 用龙芯 0.5.13 绑定；argon2 换 hash-wasm | AmneziaWG 未启用；IPv6 关闭；真实握手已验证，外网转发/NAT 未验证 | 需 NET_ADMIN，建议 SYS_MODULE + `/lib/modules`；sysctls；51820/udp、51821；`/etc/wireguard` 持久化 |
| Komga | 官方 jar；自编 loongarch64 sqlite-jdbc JNI，经 `org.sqlite.lib.path` 外挂 | HEIF/JXL 封面不可用；Kobo 转换未支持；PDF/EPUB/RAR 未验证 | JDK 21；`/config`、`/data`（可只读）；25600；UID 1110 |
| Karakeep | 复用 node-sharp；Next 在 x86 构建；默认不内置 Chromium | 搜索需外部 Meilisearch；截图需 LBrowser sidecar；PDF 默认关闭（`CRAWLER_STORE_PDF=true` 已验证）；monolith/视频/OCR/AI 未验证 | `BROWSER_WEB_URL` 接 LBrowser（挂载宿主 `/opt/apps/lbrowser:ro`）；`/data`；3000；UID 1116 |
| Linkwarden | Next 15 x86 构建；Prisma 7 WASM + adapter-pg；自写 99 迁移器；bcryptjs | 无 Meilisearch 时仅 SQL contains；默认无浏览器；monolith/AI/导入/OAuth 未验证 | PostgreSQL；`PLAYWRIGHT_WS_URL` 接 LBrowser sidecar；`/data/data`；3000；UID 1118 |
| Woodpecker server | 前端 x86 构建后内嵌；CGO SQLite | **不配置 forge（Gitea/GitHub 等）无法启动**；无内置账号体系，依赖 forge OAuth | `/var/lib/woodpecker` 持久化；`WOODPECKER_HOST` 必须是外部可访问 URL；agent/grpc secret 自动生成 |
| Woodpecker agent | Go CGO-free；UID 1114 | 无业务端口，仅 3000 健康检查；必须能访问 Docker daemon | 挂 `docker.sock` 并 `--group-add <GID>`；`WOODPECKER_AGENT_SECRET` 与 server 一致；等同宿主 root，只接可信仓库 |
| Mealie | Python 3.14 自编 | HEIF/HEIC 不支持 | `/app/data`；UID 911 |
| Nextcloud | 当前镜像使用 SQLite | 生产不建议 SQLite；无外部 DB 自动配置 | 仅测试/轻量使用；`config`/`data` 持久化 |
| Navidrome | Go + 系统 taglib | DSD 已编，但真实播放未全量验证 | 音乐目录只读挂载 |
| Jellyfin | .NET 9 自编 + ImageSharp | 无 ICC 色彩管理；性能低于 Skia | 硬件转码未验证 |
| Kopia | Web UI 强制 Basic 认证 | 默认凭据需修改 | 仓库存储需持久化 |

## 商店页面模板

CasaOS `x-casaos` 描述和 iStore 应用详情至少包含：

```text
架构：linux/loong64（仅龙芯）
龙芯版说明：<本表对应行>
与上游差异：<行为/功能/默认值>
缺失功能：<无/具体项>
额外依赖：<数据库/设备/宿主能力>
```

## 规则

1. 新增镜像必须在本表增加一行；没有差异写“未发现行为差异”。
2. 差异如果只写在 BUILD.md、没进 `catalog.json` notes 或本表，视为商店文档未完成。
3. 商店生成器必须同时读取 `catalog.json` 的 `notes` 和本表，不允许只渲染应用名。
4. 禁止把“需要手工 docker pull/改配置”的应用写成“一键即用”。
