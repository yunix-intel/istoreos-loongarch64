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
| MeTube | Python 3.13 自编；Angular 前端 x86 构建 | 无 Brotli 解压；无内置 `bgutil-pot`（部分 YouTube 视频需 cookies/远程 provider）；ffmpeg 为 6.1.1 而非上游 8.1 | `/downloads` 持久化并 `chown 1111`；默认 `YTDL_OPTIONS` 用 Node 24 作 JS runtime；8082 |
| SABnzbd | Python 3.11 + venv；par2/unrar 源码编 | 无 orjson（ujson 回退，性能略低）；unrar 为闭源 freeware | `/config`、`/downloads` 持久化；UI 根路径 `/` 不是 `/sabnzbd/`；8080 |
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
