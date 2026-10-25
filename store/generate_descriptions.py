#!/usr/bin/env python3
"""Generate LoongArch store-card descriptions for CasaOS and iStore.

Source of truth:
  - images/catalog.json (image name, notes, verification)
  - docs/LOONG64-QUIRKS.md (behavior differences, mirrored below for stable output)

Output:
  - store/loong64-descriptions.json
  - store/descriptions-preview.md
"""

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "images", "catalog.json")
OUT_JSON = os.path.join(ROOT, "store", "loong64-descriptions.json")
OUT_MD = os.path.join(ROOT, "store", "descriptions-preview.md")

SKIP = {"node", "node-sharp", "lbrowser-runtime"}  # runtime base images, not installable apps

NAMES = {
    "qbittorrent-ee": "qBittorrent (Enhanced Edition)",
    "it-tools": "IT-Tools",
    "one-api": "One API",
    "code-server": "code-server",
    "jellyseerr": "Jellyseerr",
    "calibre-web": "Calibre-Web",
    "kodexplorer": "KodExplorer",
    "homeassistant": "Home Assistant",
    "stirling-pdf": "Stirling PDF",
    "paperless-ngx": "Paperless-ngx",
    "changedetection": "ChangeDetection.io",
    "node-exporter": "Node Exporter",
    "rest-server": "REST Server",
    "actual-budget": "Actual Budget",
    "apprise-api": "Apprise API",
    "chinesesubfinder": "ChineseSubFinder",
    "smartctl-exporter": "smartctl_exporter",
    "webvirtcloud": "WebVirtCloud",
    "penpot-backend": "Penpot (backend)",
    "penpot-frontend": "Penpot (frontend)",
    "go2rtc": "go2rtc",
    "sftpgo": "SFTPGo",
    "bookstack": "BookStack",
    "vikunja": "Vikunja",
    "piwigo": "Piwigo",
    "authelia": "Authelia",
    "ente-server": "Ente Server",
    "ente-web": "Ente Web",
    "autobrr": "Autobrr",
    "matomo": "Matomo",
    "woodpecker-server": "Woodpecker CI (server)",
    "woodpecker-agent": "Woodpecker CI (agent)",
    "mediamtx": "MediaMTX",
    "pocket-id": "Pocket ID",
    "mihomo": "Mihomo",
    "easytier": "EasyTier",
    "memos": "Memos",
    "gogs": "Gogs",
    "heimdall": "Heimdall",
    "wallabag": "Wallabag",
    "drawio": "draw.io",
    "jackett": "Jackett",
    "xteve": "xTeVe",
    "dpanel": "DPanel",
    "shiori": "Shiori",
    "openwebui": "Open WebUI",
    "sonarr": "Sonarr",
    "radarr": "Radarr",
    "tautulli": "Tautulli",
    "jellystat": "Jellystat",
    "wizarr": "Wizarr",
    "gitea": "Gitea",
    "miniflux": "Miniflux",
    "portainer": "Portainer",
    "nginx-proxy-manager": "Nginx Proxy Manager",
    "firefly-iii": "Firefly III",
    "phpmyadmin": "phpMyAdmin",
    "freshrss": "FreshRSS",
    "prowlarr": "Prowlarr",
    "bazarr": "Bazarr",
    "dashy": "Dashy",
    "watchtower": "Watchtower",
    "caddy": "Caddy",
    "dozzle": "Dozzle",
    "ntfy": "ntfy",
    "gotify": "Gotify",
    "prometheus": "Prometheus",
    "pihole": "Pi-hole",
    "gatus": "Gatus",
    "alertmanager": "Alertmanager",
    "postgres": "PostgreSQL",
    "redis": "Redis",
    "mosquitto": "Eclipse Mosquitto",
    "mariadb": "MariaDB",
    "node-red": "Node-RED",
    "grafana": "Grafana",
    "memcached": "Memcached",
    "homebridge": "Homebridge",
    "minio": "MinIO",
    "homebox": "HomeBox",
    "nocodb": "NocoDB",
    "mealie": "Mealie",
    "lanraragi": "LANraragi",
    "owntone": "OwnTone",
    "mymind": "MyMind",
    "hermes": "Hermes",
    "zigbee2mqtt": "Zigbee2MQTT",
    "scrutiny": "Scrutiny",
    "headscale": "Headscale",
    "backrest": "Backrest",
    "sabnzbd": "SABnzbd",
    "metube": "MeTube",
    "registry": "Docker Registry",
    "unpackerr": "Unpackerr",
    "readeck": "Readeck",
    "vaultwarden": "Vaultwarden",
    "uptimekuma": "Uptime Kuma",
    "syncthing": "Syncthing",
    "adguardhome": "AdGuard Home",
    "filebrowser": "File Browser",
    "excalidraw": "Excalidraw",
    "kopia": "Kopia",
    "linkding": "Linkding",
    "nextcloud": "Nextcloud",
    "typecho": "Typecho",
    "audiobookshelf": "Audiobookshelf",
    "homarr": "Homarr",
    "jellyfin": "Jellyfin",
    "navidrome": "Navidrome",
}

GROUPS = {
    "Media": [
        "jellyfin", "navidrome", "audiobookshelf", "calibre-web", "lanraragi", "owntone",
        "xteve", "jellyseerr", "tautulli", "jellystat", "chinesesubfinder", "mymind",
        "mediamtx", "go2rtc", "stirling-pdf", "excalidraw", "drawio",
    ],
    "Downloaders": [
        "sonarr", "radarr", "prowlarr", "bazarr", "jackett", "qbittorrent-ee",
        "sabnzbd", "metube", "autobrr", "unpackerr",
    ],
    "Cloud": [
        "syncthing", "nextcloud", "filebrowser", "kodexplorer", "sftpgo", "minio",
        "ente-server", "ente-web", "piwigo",
    ],
    "Productivity": [
        "memos", "linkding", "wallabag", "shiori", "readeck", "paperless-ngx",
        "homebox", "bookstack", "mealie", "freshrss", "vikunja", "actual-budget",
        "typecho", "firefly-iii", "matomo",
    ],
    "Backup": ["kopia", "backrest", "rest-server"],
    "Developer": [
        "gogs", "gitea", "code-server", "one-api", "openwebui", "node-red", "woodpecker-server",
        "woodpecker-agent", "registry", "portainer", "dpanel", "dozzle", "webvirtcloud",
        "nocodb", "penpot-backend", "penpot-frontend", "hermes", "it-tools",
    ],
    "Monitoring": [
        "uptimekuma", "gatus", "grafana", "prometheus", "node-exporter", "alertmanager",
        "scrutiny", "smartctl-exporter", "changedetection",
    ],
    "Networking": [
        "mihomo", "easytier", "adguardhome", "pihole", "caddy", "nginx-proxy-manager",
        "headscale", "homarr", "homer", "dashy", "memcached",
    ],
    "Security": ["vaultwarden", "authelia", "pocket-id"],
    "Home Automation": ["homeassistant", "homebridge", "zigbee2mqtt"],
    "Utilities": [
        "apprise-api", "ntfy", "gotify", "watchtower", "postgres", "redis",
        "mosquitto", "mariadb",
    ],
}
CATEGORY = {}
for cat, ids in GROUPS.items():
    for i in ids:
        CATEGORY[i] = cat

# Behavior differences / missing features / extra dependencies.
# Keep this in sync with docs/LOONG64-QUIRKS.md.
DEFAULT_QUIRK = {
    "zh": "此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。",
    "en": "LoongArch build; upstream functionality is largely retained, but behavior was not regression-tested item by item. Limitations in the image notes also apply.",
    "missing_zh": "未逐项验证上游全部功能；请以镜像说明中的限制为准。",
    "missing_en": "Upstream features were not verified item by item; treat the image notes as the limitation list.",
    "deps_zh": "无额外外部依赖（镜像说明中另有注明的除外）。",
    "deps_en": "No extra external dependency unless the image notes say otherwise.",
}

QUIRKS = {
    "scrutiny": {
        "zh": "使用 SQLite metrics 补丁，不再依赖 InfluxDB；历史数据保存在 SQLite。",
        "en": "Uses a SQLite metrics patch instead of InfluxDB; history is stored in SQLite.",
        "missing_zh": "不迁移旧 InfluxDB 历史；无保留/降采样任务；collector 需外部 cron/exec 触发。",
        "missing_en": "No migration of old InfluxDB history; no retention/downsampling jobs; collector must be triggered externally.",
        "deps_zh": "需 SYS_RAWIO/SYS_ADMIN 与磁盘设备直通；运行镜像含 libstdc++/libgcc。",
        "deps_en": "Requires SYS_RAWIO/SYS_ADMIN and disk device passthrough; image includes libstdc++/libgcc.",
    },
    "penpot-backend": {
        "zh": "Penpot 前后端拆成两个镜像；后端用 JDK 21 运行官方 jar。",
        "en": "Penpot is split into frontend and backend images; the backend runs the official jar on JDK 21.",
        "missing_zh": "无 exporter（PDF/PNG 导出会 502）；无 admin-console/MCP。",
        "missing_en": "No exporter (PDF/PNG export returns 502); no admin console/MCP.",
        "deps_zh": "需 PostgreSQL + Redis；PENPOT_SECRET_KEY 必填。",
        "deps_en": "Requires PostgreSQL and Redis; PENPOT_SECRET_KEY is mandatory.",
    },
    "penpot-frontend": {
        "zh": "Penpot 前端单独成镜像，通过 nginx 反代后端。",
        "en": "Separate Penpot frontend image, reverse-proxying the backend with nginx.",
        "missing_zh": "同上；导出功能未移植。",
        "missing_en": "Same as backend; exporter is not ported.",
        "deps_zh": "需同时部署 penpot-backend、PostgreSQL、Redis。",
        "deps_en": "Requires penpot-backend, PostgreSQL and Redis.",
    },
    "hermes": {
        "zh": "使用 Python 3.14 独立构建；镜像保留 gcc/rust 工具链。",
        "en": "Built with a standalone Python 3.14; the image keeps gcc/rust toolchains.",
        "missing_zh": "不支持 HEIC/HEIF；computer_use 在 loongarch64 不可用。",
        "missing_en": "No HEIC/HEIF support; computer_use is unavailable on loongarch64.",
        "deps_zh": "默认无 WebUI 密码；镜像约 3.68GB。",
        "deps_en": "No default WebUI password; image is about 3.68GB.",
    },
    "bookstack": {
        "zh": "PHP 8.3 + nginx/php-fpm；首次启动自动生成 .env。",
        "en": "PHP 8.3 with nginx/php-fpm; .env is generated on first start.",
        "missing_zh": "必须使用 MariaDB/MySQL，不支持 SQLite。",
        "missing_en": "Requires MariaDB/MySQL; SQLite is not supported.",
        "deps_zh": "需 MariaDB/MySQL；持久化 storage 与 public/uploads；首次用 artisan 建管理员。",
        "deps_en": "Requires MariaDB/MySQL; persist storage and public/uploads; create the admin with artisan.",
    },
    "piwigo": {
        "zh": "首次启动自动 POST install.php 完成安装。",
        "en": "Runs install.php automatically on first start.",
        "missing_zh": "必须使用 MariaDB/MySQL。",
        "missing_en": "Requires MariaDB/MySQL.",
        "deps_zh": "需 MariaDB/MySQL；持久化 local、_data、galleries、upload。",
        "deps_en": "Requires MariaDB/MySQL; persist local, _data, galleries and upload.",
    },
    "vikunja": {
        "zh": "Vue 前端在 x86 构建；后端 Go + CGO SQLite。",
        "en": "Vue frontend is built on x86; backend is Go with CGO SQLite.",
        "missing_zh": "默认允许注册，生产环境需关闭。",
        "missing_en": "Registration is enabled by default; disable it in production.",
        "deps_zh": "service.interface 必须为 0.0.0.0:3456；PUBLICURL 必须正确；持久化 /db。",
        "deps_en": "service.interface must be 0.0.0.0:3456; PUBLICURL must be correct; persist /db.",
    },
    "sftpgo": {
        "zh": "Go + CGO SQLite；首次进入安装页创建管理员。",
        "en": "Go with CGO SQLite; the first visit opens the setup page.",
        "missing_zh": "默认不创建管理员；FTP/WebDAV 默认关闭。",
        "missing_en": "No default admin; FTP/WebDAV are disabled by default.",
        "deps_zh": "持久化 /srv/sftpgo/data 与 /var/lib/sftpgo；公网需 TLS。",
        "deps_en": "Persist /srv/sftpgo/data and /var/lib/sftpgo; use TLS on the public network.",
    },
    "zigbee2mqtt": {
        "zh": "Node 24 + pnpm；serialport 针对 loongarch64 源码编译。",
        "en": "Node 24 with pnpm; serialport is compiled from source for loongarch64.",
        "missing_zh": "没有 USB 协调器时容器会退出。",
        "missing_en": "The container exits when no USB coordinator is present.",
        "deps_zh": "需 /dev/ttyACM0 或 /dev/serial/by-id/*，以及 dialout 组。",
        "deps_en": "Requires /dev/ttyACM0 or /dev/serial/by-id/* and the dialout group.",
    },
    "smartctl-exporter": {
        "zh": "仅暴露 Prometheus 指标，没有 UI 和历史库。",
        "en": "Exposes Prometheus metrics only; no UI or history database.",
        "missing_zh": "无内置历史/告警。",
        "missing_en": "No built-in history or alerting.",
        "deps_zh": "需 SYS_RAWIO/SYS_ADMIN 与设备直通；默认无认证。",
        "deps_en": "Requires SYS_RAWIO/SYS_ADMIN and device passthrough; no auth by default.",
    },
    "go2rtc": {
        "zh": "单二进制，无 ffmpeg 依赖。",
        "en": "Single binary; no ffmpeg dependency.",
        "missing_zh": "默认无摄像头流配置、无认证。",
        "missing_en": "No default camera streams and no authentication.",
        "deps_zh": "1984 API、8554 RTSP、8555 WebRTC；跨 NAT 需配置 candidates。",
        "deps_en": "Ports 1984 API, 8554 RTSP, 8555 WebRTC; configure candidates behind NAT.",
    },
    "headscale": {
        "zh": "单二进制，无 Web UI；通过 CLI/API 管理。",
        "en": "Single binary without a web UI; managed via CLI/API.",
        "missing_zh": "无图形界面；gRPC 默认仅本机。",
        "missing_en": "No GUI; gRPC listens on localhost by default.",
        "deps_zh": "HEADSCALE_SERVER_URL 必填；持久化 /etc/headscale 与 /var/lib/headscale。",
        "deps_en": "HEADSCALE_SERVER_URL is required; persist /etc/headscale and /var/lib/headscale.",
    },
    "backrest": {
        "zh": "前端在 x86 构建后内嵌；自带 restic 0.19.1。",
        "en": "Frontend is built on x86 and embedded; bundles restic 0.19.1.",
        "missing_zh": "首次需在 UI 建账号/仓库；默认无认证。",
        "missing_en": "Create the account/repository in the UI first; no auth by default.",
        "deps_zh": "持久化 /data、/config、/cache；备份源目录需额外挂载。",
        "deps_en": "Persist /data, /config and /cache; mount the backup source directories separately.",
    },
    "authelia": {
        "zh": "自动生成配置/用户库/密钥；单机 SQLite。",
        "en": "Generates config, user database and secrets automatically; single-node SQLite.",
        "missing_zh": "无内置 TLS；默认 one_factor，forward-auth 需反代配置。",
        "missing_en": "No built-in TLS; one_factor by default; forward-auth needs reverse-proxy config.",
        "deps_zh": "AUTH_DOMAIN/AUTH_URL 必须是 HTTPS 正式域名；持久化 /config。",
        "deps_en": "AUTH_DOMAIN/AUTH_URL must be real HTTPS domains; persist /config.",
    },
    "ente-server": {
        "zh": "仅 API；museum.yaml 首次启动生成。",
        "en": "API only; museum.yaml is generated on first start.",
        "missing_zh": "不自带 Web 图库，需要 ente-web。",
        "missing_en": "No web gallery; use ente-web.",
        "deps_zh": "需 PostgreSQL + S3/MinIO 三个桶；/data/museum.yaml 含密钥必须备份。",
        "deps_en": "Requires PostgreSQL and three S3/MinIO buckets; back up /data/museum.yaml (contains keys).",
    },
    "ente-web": {
        "zh": "10 个 Next 应用纯静态导出，由 nginx 托管。",
        "en": "Ten Next.js apps exported statically and served by nginx.",
        "missing_zh": "无 Next 服务端/API/图片优化器；未知路径回退到 index.html；不保证逐字节可复现。",
        "missing_en": "No Next server/API/image optimizer; unknown paths fall back to index.html; not byte-for-byte reproducible.",
        "deps_zh": "必须设置 ENTE_API_ORIGIN；端口 3000–3006、3008–3010。",
        "deps_en": "ENTE_API_ORIGIN is required; ports 3000–3006 and 3008–3010.",
    },
    "autobrr": {
        "zh": "前端在 x86 构建后内嵌；使用 SQLite。",
        "en": "Frontend is built on x86 and embedded; uses SQLite.",
        "missing_zh": "默认无认证；需自行配置 IRC 和下载器。",
        "missing_en": "No auth by default; configure IRC and download clients yourself.",
        "deps_zh": "持久化 /config；公网需反代认证。",
        "deps_en": "Persist /config; add reverse-proxy auth on the public network.",
    },
    "matomo": {
        "zh": "官方完整包；PHP 8.3 + nginx/php-fpm。",
        "en": "Official full package; PHP 8.3 with nginx/php-fpm.",
        "missing_zh": "首次必须走 Web 安装向导；没有 CLI 安装器。",
        "missing_en": "First run requires the web installer; there is no CLI installer.",
        "deps_zh": "必须 MariaDB/MySQL；持久化 config/tmp；归档需 cron。",
        "deps_en": "Requires MariaDB/MySQL; persist config/tmp; archiving needs cron.",
    },
    "mealie": {
        "zh": "Python 3.14 源码构建。",
        "en": "Built from source with Python 3.14.",
        "missing_zh": "不支持 HEIF/HEIC。",
        "missing_en": "No HEIF/HEIC support.",
        "deps_zh": "持久化 /app/data；UID 911。",
        "deps_en": "Persist /app/data; UID 911.",
    },
    "nextcloud": {
        "zh": "当前镜像使用 SQLite。",
        "en": "The current image uses SQLite.",
        "missing_zh": "生产不建议 SQLite；无外部数据库自动配置。",
        "missing_en": "SQLite is not recommended for production; no automatic external DB setup.",
        "deps_zh": "仅适合测试/轻量使用；持久化 config 与 data。",
        "deps_en": "Suitable for testing/light use; persist config and data.",
    },
    "navidrome": {
        "zh": "Go + 系统 taglib；DSD 已编译。",
        "en": "Go with system taglib; DSD support is compiled in.",
        "missing_zh": "DSD 真实播放尚未全量验证。",
        "missing_en": "Real DSD playback has not been fully verified.",
        "deps_zh": "音乐目录需只读挂载。",
        "deps_en": "Mount the music directory read-only.",
    },
    "jellyfin": {
        "zh": ".NET 9 自编 + ImageSharp 编码器。",
        "en": "Built from source with .NET 9 and the ImageSharp encoder.",
        "missing_zh": "无 ICC 色彩管理；纯托管性能低于 Skia；硬件转码未验证。",
        "missing_en": "No ICC color management; managed performance is below Skia; hardware transcoding is unverified.",
        "deps_zh": "媒体目录与 config 需持久化。",
        "deps_en": "Persist the media directories and config.",
    },
    "kopia": {
        "zh": "Web UI 强制 Basic 认证。",
        "en": "The web UI enforces Basic authentication.",
        "missing_zh": "默认凭据需修改。",
        "missing_en": "Change the default credentials.",
        "deps_zh": "仓库存储需持久化。",
        "deps_en": "Persist the repository storage.",
    },
    "woodpecker-server": {
        "zh": "前端 x86 构建后内嵌；CGO SQLite。",
        "en": "Frontend is built on x86 and embedded; CGO SQLite.",
        "missing_zh": "不配置 forge（Gitea/GitHub 等）无法启动；无内置账号体系。",
        "missing_en": "Cannot start without a forge (Gitea/GitHub/etc.); no built-in account system.",
        "deps_zh": "持久化 /var/lib/woodpecker；WOODPECKER_HOST 必须是外部可访问 URL。",
        "deps_en": "Persist /var/lib/woodpecker; WOODPECKER_HOST must be an externally reachable URL.",
    },
    "woodpecker-agent": {
        "zh": "Go CGO-free；UID 1114。",
        "en": "CGO-free Go binary; UID 1114.",
        "missing_zh": "无业务端口，仅 3000 健康检查；必须能访问 Docker daemon。",
        "missing_en": "No service port; 3000 is health only; requires Docker daemon access.",
        "deps_zh": "挂载 docker.sock 并加匹配的 --group-add；agent secret 与 server 一致；等同宿主 root。",
        "deps_en": "Mount docker.sock and add the matching --group-add; share the agent secret with the server; equivalent to host root.",
    },
    "metube": {
        "zh": "Python 3.13 自编；Angular 前端在 x86 构建。",
        "en": "Self-built Python 3.13; Angular frontend built on x86.",
        "missing_zh": "无 Brotli 解压；无内置 bgutil-pot；ffmpeg 为 6.1.1 而非上游 8.1。",
        "missing_en": "No Brotli decompression; no bundled bgutil-pot; ffmpeg 6.1.1 instead of upstream 8.1.",
        "deps_zh": "持久化 /downloads 并 chown 1111；默认用 Node 24 作为 yt-dlp JS runtime；8082。",
        "deps_en": "Persist /downloads and chown to 1111; Node 24 is the default yt-dlp JS runtime; port 8082.",
    },
    "sabnzbd": {
        "zh": "Python 3.11 + venv；par2/unrar 源码编译。",
        "en": "Python 3.11 venv; par2 and unrar built from source.",
        "missing_zh": "无 orjson（ujson 回退，性能略低）；unrar 为闭源 freeware。",
        "missing_en": "No orjson (ujson fallback, slightly slower); unrar is closed-source freeware.",
        "deps_zh": "持久化 /config 与 /downloads；UI 根路径是 / 而不是 /sabnzbd/。",
        "deps_en": "Persist /config and /downloads; the UI root is /, not /sabnzbd/.",
    },
    "mediamtx": {
        "zh": "Go 单二进制，配置内嵌。",
        "en": "Single Go binary with embedded configuration.",
        "missing_zh": "无 Web 管理界面/持久化；API 默认仅本机白名单。",
        "missing_en": "No web admin UI or persistence; API is localhost-only by default.",
        "deps_zh": "8554/1935/8888/8889/8890/9997；NAT 后 WebRTC 需配 additional hosts；与 go2rtc 二选一。",
        "deps_en": "Ports 8554/1935/8888/8889/8890/9997; configure additional hosts for WebRTC behind NAT; use instead of go2rtc.",
    },
    "registry": {
        "zh": "Go 单二进制；首次启动生成 htpasswd。",
        "en": "Single Go binary; htpasswd is generated on first start.",
        "missing_zh": "无 Web UI、无 TLS、无多实例共享存储；删除后需手动 GC。",
        "missing_en": "No web UI, no TLS, no shared storage across instances; run GC manually after deletes.",
        "deps_zh": "持久化 /var/lib/registry 与 /auth；/auth/password 是唯一密码来源；Docker CLI 需 insecure-registries。",
        "deps_en": "Persist /var/lib/registry and /auth; /auth/password is the only password source; Docker CLI needs insecure-registries.",
    },
    "unpackerr": {
        "zh": "Go 单二进制；需要升级 x/sys 才能支持 loongarch64。",
        "en": "Single Go binary; requires an x/sys upgrade for loongarch64.",
        "missing_zh": "无 Web UI/端口；健康检查仅进程存活；未接真实 *arr。",
        "missing_en": "No web UI/port; health check is process-only; not tested against a real *arr.",
        "deps_zh": "持久化 /config 与 /downloads，路径必须与 *arr 一致；unrar 为闭源 freeware。",
        "deps_en": "Persist /config and /downloads with paths identical to *arr; unrar is closed-source freeware.",
    },
    "pocket-id": {
        "zh": "SvelteKit 前端在 x86 构建后内嵌；Go 单二进制。",
        "en": "SvelteKit frontend built on x86 and embedded; single Go binary.",
        "missing_zh": "未做邮件 SMTP/SCIM/Passkey 全链路；与 Authelia 二选一。",
        "missing_en": "SMTP/SCIM/Passkey flows are not fully tested; choose instead of Authelia.",
        "deps_zh": "持久化 /data（含加密密钥）；APP_URL 必填为外部地址；1411。",
        "deps_en": "Persist /data (including the encryption key); APP_URL must be the external address; port 1411.",
    },
    "readeck": {
        "zh": "gulp 前端在 x86 构建；Go 使用 CGO/mattn sqlite。",
        "en": "gulp frontend built on x86; Go uses CGO/mattn sqlite.",
        "missing_zh": "CGO-free 的 modernc 旧版缺 loongarch64 定义；未做完整抓取联调。",
        "missing_en": "The pinned pure-Go modernc sqlite lacks loongarch64 definitions; full archiving was not tested.",
        "deps_zh": "持久化 /data；8000；与 Wallabag/Shiori 重叠。",
        "deps_en": "Persist /data; port 8000; overlaps with Wallabag/Shiori.",
    },
}

QUIRKS.update({
    "jellyseerr": {
        "zh": "Next 16 使用 WASM SWC 在 x86 构建；sharp 不可用，图片优化关闭。",
        "en": "Next 16 is built on x86 with WASM SWC; sharp is unavailable, so image optimization is disabled.",
        "missing_zh": "无 Next 图片优化器；依赖上游请求服务。",
        "missing_en": "No Next image optimizer; relies on upstream request services.",
        "deps_zh": "需 Sonarr/Radarr 等上游服务；5055。",
        "deps_en": "Requires Sonarr/Radarr and other upstream services; port 5055.",
    },
    "qbittorrent-ee": {
        "zh": "官方 loong64 静态包；WebUI 校验 Host header。",
        "en": "Official loong64 static package; the WebUI validates the Host header.",
        "missing_zh": "端口映射与 WebUI 端口不一致时会拒绝访问。",
        "missing_en": "Requests are rejected when the mapped port differs from the WebUI port.",
        "deps_zh": "建议让 WebUI 端口与宿主映射端口一致。",
        "deps_en": "Keep the WebUI port equal to the published host port.",
    },
    "homarr": {
        "zh": "Next 16 WASM SWC + Node 24；未使用 Bun/Turbo。",
        "en": "Next 16 with WASM SWC and Node 24; Bun/Turbo are not used.",
        "missing_zh": "Bun/Turbo 构建链未移植；依赖 Redis。",
        "missing_en": "The Bun/Turbo build chain is not ported; Redis is required.",
        "deps_zh": "需 Redis；7575。",
        "deps_en": "Requires Redis; port 7575.",
    },
    "openwebui": {
        "zh": "仅推理模式：不含 torch/onnxruntime/whisper/OCR 与内置模型。",
        "en": "Inference-only mode: no torch/onnxruntime/whisper/OCR and no bundled models.",
        "missing_zh": "本地推理、语音、OCR 不可用；RAG 需外部 pgvector。",
        "missing_en": "Local inference, speech and OCR are unavailable; RAG needs external pgvector.",
        "deps_zh": "需外部 Ollama/OpenAI 兼容服务；RAG 需 PostgreSQL + pgvector。",
        "deps_en": "Requires an external Ollama/OpenAI-compatible service; RAG needs PostgreSQL + pgvector.",
    },
    "paperless-ngx": {
        "zh": "qpdf 12.4.2 自编以支持 pikepdf；AI 功能关闭；未装 unpaper。",
        "en": "qpdf 12.4.2 is built for pikepdf; AI features are disabled; unpaper is not installed.",
        "missing_zh": "无 AI 分类/实体识别；无 unpaper 后处理。",
        "missing_en": "No AI classification/entity extraction; no unpaper post-processing.",
        "deps_zh": "需 Redis + celery worker/beat/consumer；8000。",
        "deps_en": "Requires Redis and celery worker/beat/consumer; port 8000.",
    },
    "stirling-pdf": {
        "zh": "官方 jar + Java 25。",
        "en": "Official jar on Java 25.",
        "missing_zh": "未装 LibreOffice/OCR，相关转换不可用。",
        "missing_en": "LibreOffice/OCR are not installed, so those conversions are unavailable.",
        "deps_zh": "8080；首次可按需在 UI 配置。",
        "deps_en": "Port 8080; configure optional features in the UI.",
    },
    "code-server": {
        "zh": "4.141.0 + VS Code 1.141，必须 Node 24；自编静态 ripgrep。",
        "en": "4.141.0 with VS Code 1.141; requires Node 24; static ripgrep is built in.",
        "missing_zh": "Node 20 缺少 module.registerHooks，不能替换运行时。",
        "missing_en": "Node 20 lacks module.registerHooks and cannot be used as the runtime.",
        "deps_zh": "8443；持久化 /home/coder。",
        "deps_en": "Port 8443; persist /home/coder.",
    },
    "changedetection": {
        "zh": "使用 Firefox 140.11 ESR + geckodriver/Selenium，不是 Playwright；OpenCV SSIM 使用 numpy 1.26.4。",
        "en": "Uses Firefox 140.11 ESR with geckodriver/Selenium instead of Playwright; OpenCV SSIM uses numpy 1.26.4.",
        "missing_zh": "无本地 Chrome；可配置远程 Chrome WebDriver。",
        "missing_en": "No local Chrome; a remote Chrome WebDriver can be configured.",
        "deps_zh": "需 --shm-size=1g；5000；持久化 /datastore。",
        "deps_en": "Needs --shm-size=1g; port 5000; persist /datastore.",
    },
    "filebrowser": {
        "zh": "上游已于 2026-09-01 归档，无后续安全修复；镜像默认监听 0.0.0.0（v2.63 上游默认 127.0.0.1）。",
        "en": "Upstream was archived on 2026-09-01 with no further security fixes; the image listens on 0.0.0.0 (v2.63 upstream defaults to 127.0.0.1).",
        "missing_zh": "无上游安全更新。",
        "missing_en": "No upstream security updates.",
        "deps_zh": "8080；持久化 /srv 与数据库。",
        "deps_en": "Port 8080; persist /srv and the database.",
    },
    "miniflux": {
        "zh": "上游已删除 SQLite 支持，必须提供 PostgreSQL DSN。",
        "en": "Upstream removed SQLite support; a PostgreSQL DSN is required.",
        "missing_zh": "不支持 SQLite。",
        "missing_en": "SQLite is not supported.",
        "deps_zh": "需 PostgreSQL；8080。",
        "deps_en": "Requires PostgreSQL; port 8080.",
    },
    "jellystat": {
        "zh": "Node 20 + Vite 6。",
        "en": "Node 20 with Vite 6.",
        "missing_zh": "无 SQLite 路径，必须外部 PostgreSQL。",
        "missing_en": "No SQLite path; external PostgreSQL is required.",
        "deps_zh": "需 PostgreSQL；3000。",
        "deps_en": "Requires PostgreSQL; port 3000.",
    },
    "minio": {
        "zh": "Go 源码编；单目录模式无纠删码。",
        "en": "Built from Go source; single-directory mode has no erasure coding.",
        "missing_zh": "无纠删码/多盘冗余；无内置 TLS。",
        "missing_en": "No erasure coding or multi-disk redundancy; no built-in TLS.",
        "deps_zh": "必须设 MINIO_ROOT_USER/PASSWORD；AGPLv3；9000/9001。",
        "deps_en": "MINIO_ROOT_USER/PASSWORD are required; AGPLv3; ports 9000/9001.",
    },
    "grafana": {
        "zh": "前端在 x86 构建；Go CGO-free 编。",
        "en": "Frontend built on x86; Go binary is CGO-free.",
        "missing_zh": "未内置 renderer；默认 admin/admin。",
        "missing_en": "No bundled renderer; default admin/admin.",
        "deps_zh": "3000；持久化 /var/lib/grafana。",
        "deps_en": "Port 3000; persist /var/lib/grafana.",
    },
    "pihole": {
        "zh": "FTL 6.8 源码编，版本自报 UNKNOWN；内置 pihole CLI 与 pihole-adlist。",
        "en": "FTL 6.8 is built from source and reports UNKNOWN; includes the pihole CLI and pihole-adlist.",
        "missing_zh": "需 host 网络；宿主 dnsmasq 占用 53 时不可用。",
        "missing_en": "Requires host networking; unusable while the host dnsmasq holds port 53.",
        "deps_zh": "53/tcp+udp、80；持久化 /etc/pihole。",
        "deps_en": "Ports 53/tcp+udp and 80; persist /etc/pihole.",
    },
    "adguardhome": {
        "zh": "官方无 loong64 资产，源码自编 + 官方前端。",
        "en": "No official loong64 asset; built from source with the official frontend.",
        "missing_zh": "53 端口需避让宿主 dnsmasq。",
        "missing_en": "Port 53 conflicts with the host dnsmasq.",
        "deps_zh": "建议 host 网络；3000 Web；持久化 work/conf。",
        "deps_en": "Host networking recommended; web on 3000; persist work/conf.",
    },
    "nginx-proxy-manager": {
        "zh": "前端在 x64 构建；自定义 entrypoint 替代 s6-overlay。",
        "en": "Frontend built on x64; a custom entrypoint replaces s6-overlay.",
        "missing_zh": "s6-overlay 的进程管理行为未完全复刻。",
        "missing_en": "s6-overlay process management is not fully replicated.",
        "deps_zh": "81/443；持久化 data 与 letsencrypt。",
        "deps_en": "Ports 81/443; persist data and letsencrypt.",
    },
    "rest-server": {
        "zh": "Go 静态编译，镜像约 12MB。",
        "en": "Static Go build; image is about 12MB.",
        "missing_zh": "默认开启认证；无 TLS。",
        "missing_en": "Authentication is enabled by default; no TLS.",
        "deps_zh": "8000；用 httpd-tools 的 htpasswd 建用户。",
        "deps_en": "Port 8000; create users with htpasswd from httpd-tools.",
    },
    "redis": {
        "zh": "openEuler 7.2.14 包；AOF+RDB。",
        "en": "openEuler 7.2.14 package; AOF+RDB.",
        "missing_zh": "默认 protected-mode no，必须配密码或限制网络。",
        "missing_en": "protected-mode is off by default; set a password or restrict the network.",
        "deps_zh": "6379；持久化 /data。",
        "deps_en": "Port 6379; persist /data.",
    },
    "mosquitto": {
        "zh": "openEuler 2.0.20 包。",
        "en": "openEuler 2.0.20 package.",
        "missing_zh": "默认 allow_anonymous true，公网必须配 passwd。",
        "missing_en": "allow_anonymous is true by default; configure passwd before exposing it.",
        "deps_zh": "1883；持久化 /mosquitto/data。",
        "deps_en": "Port 1883; persist /mosquitto/data.",
    },
    "memcached": {
        "zh": "openEuler 1.6.42 包；默认 64MB/1024 连接。",
        "en": "openEuler 1.6.42 package; defaults to 64MB and 1024 connections.",
        "missing_zh": "无认证、无持久化，禁止公网暴露。",
        "missing_en": "No auth and no persistence; never expose it publicly.",
        "deps_zh": "11211；用 MEMCACHED_* 调整。",
        "deps_en": "Port 11211; tune with MEMCACHED_*.",
    },
    "homebridge": {
        "zh": "Homebridge 2.4.0 + Config UI 5.29.0 + Node 24；node-pty 源码编 loongarch64。",
        "en": "Homebridge 2.4.0 with Config UI 5.29.0 and Node 24; node-pty is built from source for loongarch64.",
        "missing_zh": "建议 host 网络；默认配对码需修改。",
        "missing_en": "Host networking recommended; change the default pairing code.",
        "deps_zh": "8581 Web、51826；持久化 /homebridge。",
        "deps_en": "Ports 8581 and 51826; persist /homebridge.",
    },
    "webvirtcloud": {
        "zh": "Django 4.2 + Python 3.11 + libvirt + noVNC。",
        "en": "Django 4.2 with Python 3.11, libvirt and noVNC.",
        "missing_zh": "需真实 libvirt/KVM 与 SSH 凭据；noVNC WebSocket 需反代。",
        "missing_en": "Requires real libvirt/KVM and SSH credentials; proxy noVNC WebSocket.",
        "deps_zh": "80；持久化 data 与 .ssh。",
        "deps_en": "Port 80; persist data and .ssh.",
    },
    "lanraragi": {
        "zh": "Perl 0.9.81 + 126 个 CPAN 模块；内置 Redis。",
        "en": "Perl 0.9.81 with 126 CPAN modules; bundles Redis.",
        "missing_zh": "默认无认证。",
        "missing_en": "No authentication by default.",
        "deps_zh": "3000；持久化 content/thumb/database；UID 9001。",
        "deps_en": "Port 3000; persist content/thumb/database; UID 9001.",
    },
    "owntone": {
        "zh": "DAAP/DACP/AirPlay 服务端；运行期需 dbus 与 avahi。",
        "en": "DAAP/DACP/AirPlay server; needs dbus and avahi at runtime.",
        "missing_zh": "AirPlay 发现依赖宿主网络与 avahi。",
        "missing_en": "AirPlay discovery depends on host networking and avahi.",
        "deps_zh": "3689；挂载 /srv/music 与缓存。",
        "deps_en": "Port 3689; mount /srv/music and the cache.",
    },
    "apprise-api": {
        "zh": "Python 3.11 + 系统 cryptography/gevent；nginx+supervisor+gunicorn。",
        "en": "Python 3.11 with system cryptography/gevent; nginx, supervisor and gunicorn.",
        "missing_zh": "默认无认证/无 TLS。",
        "missing_en": "No auth or TLS by default.",
        "deps_zh": "8000；持久化 /config、/attach、/plugin。",
        "deps_en": "Port 8000; persist /config, /attach and /plugin.",
    },
})

QUIRKS["wg-easy"] = {
    "zh": "v15.4.0 在龙芯原生构建；libsql 使用龙芯 0.5.13 绑定，argon2 换成 hash-wasm。",
    "en": "v15.4.0 is built natively on LoongArch; libsql uses the LoongArch 0.5.13 binding and argon2 is replaced by hash-wasm.",
    "missing_zh": "AmneziaWG 未启用；IPv6 关闭；真实客户端握手/隧道尚未验证。",
    "missing_en": "AmneziaWG is disabled; IPv6 is off; real client handshakes/tunnels are not verified yet.",
    "deps_zh": "需 NET_ADMIN，建议 SYS_MODULE + /lib/modules；sysctls；51820/udp、51821；/etc/wireguard 持久化。",
    "deps_en": "Requires NET_ADMIN, ideally SYS_MODULE + /lib/modules, sysctls, ports 51820/udp and 51821, and persistent /etc/wireguard.",
}

QUIRKS["komga"] = {
    "zh": "官方 jar 不重编；自编 loongarch64 sqlite-jdbc JNI，经 org.sqlite.lib.path 外挂。",
    "en": "Uses the official jar unchanged with a locally built loongarch64 sqlite-jdbc JNI loaded via org.sqlite.lib.path.",
    "missing_zh": "HEIF/JXL 封面不可用；Kobo 转换未支持；PDF/EPUB/RAR 扫描未验证。",
    "missing_en": "HEIF/JXL covers are unavailable; Kobo conversion is unsupported; PDF/EPUB/RAR scanning is unverified.",
    "deps_zh": "JDK 21；/config 与 /data（可只读）；25600；UID 1110。",
    "deps_en": "JDK 21; /config and /data (read-only is fine); port 25600; UID 1110.",
}

QUIRKS["karakeep"] = {
    "zh": "复用 node-sharp；Next 在 x86 构建；默认不内置 Chromium。",
    "en": "Reuses node-sharp; the Next app is built on x86; no Chromium is bundled by default.",
    "missing_zh": "搜索需外部 Meilisearch；截图/PDF/JS 页面需 LBrowser sidecar；monolith/视频/OCR/AI 尚未验证。",
    "missing_en": "Search needs external Meilisearch; screenshots/PDF/JS pages need an LBrowser sidecar; monolith, video, OCR and AI are unverified.",
    "deps_zh": "BROWSER_WEB_URL 接 LBrowser（挂载宿主 /opt/apps/lbrowser:ro）；/data；3000；UID 1116。",
    "deps_en": "Point BROWSER_WEB_URL at an LBrowser sidecar (mount /opt/apps/lbrowser:ro); /data; port 3000; UID 1116.",
}

QUIRKS["linkwarden"] = {
    "zh": "Next 15 在 x86 构建；Prisma 7 WASM + adapter-pg；自写 99 个 SQL 迁移器；bcryptjs 替代 bcrypt。",
    "en": "Next 15 is built on x86; Prisma 7 uses the WASM compiler with adapter-pg; a custom runner applies the 99 SQL migrations; bcryptjs replaces bcrypt.",
    "missing_zh": "无 Meilisearch 时仅 SQL contains 搜索；默认无浏览器；monolith/AI/导入/OAuth 尚未验证。",
    "missing_en": "Search falls back to SQL contains without Meilisearch; no browser by default; monolith, AI, import and OAuth are unverified.",
    "deps_zh": "需 PostgreSQL；PLAYWRIGHT_WS_URL 接 LBrowser sidecar；/data/data；3000；UID 1118。",
    "deps_en": "Requires PostgreSQL; point PLAYWRIGHT_WS_URL at an LBrowser sidecar; /data/data; port 3000; UID 1118.",
}

QUIRKS["joplin-server"] = {
    "zh": "全程 loongarch64 构建；sqlite3 5.1.6 源码编译；Rollup 使用 wasm 别名。",
    "en": "Built natively on loongarch64; sqlite3 5.1.6 is compiled from source; Rollup uses the wasm alias.",
    "missing_zh": "无 sharp/sqlite-vec/PM2；向量搜索禁用；未验证桌面客户端双端同步、LDAP/SAML/Stripe/邮件。",
    "missing_en": "No sharp/sqlite-vec/PM2; vector search is disabled; desktop sync, LDAP/SAML/Stripe and email are unverified.",
    "deps_zh": "需 PostgreSQL；/data 持久化（含临时 SQLite）；22300；UID 1119；APP_BASE_URL 必填。",
    "deps_en": "Requires PostgreSQL; persist /data (including the temporary SQLite); port 22300; UID 1119; APP_BASE_URL is required.",
}

EXTRA_DEPS = {
    "homarr": ("需 Redis。", "Requires Redis."),
    "jellystat": ("需外部 PostgreSQL。", "Requires external PostgreSQL."),
    "miniflux": ("需外部 PostgreSQL。", "Requires external PostgreSQL."),
    "bookstack": ("需 MariaDB/MySQL。", "Requires MariaDB/MySQL."),
    "piwigo": ("需 MariaDB/MySQL。", "Requires MariaDB/MySQL."),
    "matomo": ("需 MariaDB/MySQL。", "Requires MariaDB/MySQL."),
    "penpot-backend": ("需 PostgreSQL + Redis。", "Requires PostgreSQL and Redis."),
    "penpot-frontend": ("需 penpot-backend + PostgreSQL + Redis。", "Requires penpot-backend, PostgreSQL and Redis."),
    "ente-server": ("需 PostgreSQL + S3/MinIO。", "Requires PostgreSQL and S3/MinIO."),
    "woodpecker-server": ("需一个 forge（Gitea/GitHub 等）。", "Requires a forge (Gitea/GitHub/etc.)."),
    "woodpecker-agent": ("需访问宿主 docker.sock。", "Requires access to the host docker.sock."),
    "portainer": ("需挂载 docker.sock。", "Requires docker.sock."),
    "dpanel": ("需挂载 docker.sock。", "Requires docker.sock."),
    "dozzle": ("需挂载 docker.sock。", "Requires docker.sock."),
    "watchtower": ("需挂载 docker.sock。", "Requires docker.sock."),
    "homeassistant": ("建议 host 网络以发现设备。", "Host networking is recommended for device discovery."),
    "homebridge": ("建议 host 网络；需改默认配对码。", "Host networking recommended; change the default pairing code."),
    "pihole": ("需 host 网络并避让宿主 dnsmasq。", "Requires host networking; avoid the host dnsmasq on port 53."),
    "adguardhome": ("需 host 网络并避让宿主 dnsmasq。", "Requires host networking; avoid the host dnsmasq on port 53."),
    "zigbee2mqtt": ("需 USB 协调器与 dialout 组。", "Requires a USB coordinator and the dialout group."),
    "smartctl-exporter": ("需磁盘设备与 SYS_RAWIO/SYS_ADMIN。", "Requires disk devices and SYS_RAWIO/SYS_ADMIN."),
    "scrutiny": ("需磁盘设备与 SYS_RAWIO/SYS_ADMIN。", "Requires disk devices and SYS_RAWIO/SYS_ADMIN."),
    "webvirtcloud": ("需 libvirt/KVM 与 SSH 凭据。", "Requires libvirt/KVM and SSH credentials."),
    "pocket-id": ("需设置 APP_URL。", "APP_URL is required."),
    "ente-web": ("需设置 ENTE_API_ORIGIN。", "ENTE_API_ORIGIN is required."),
    "authelia": ("需 HTTPS 反代与正式域名。", "Requires HTTPS reverse proxy and real domains."),
    "headscale": ("需设置 HEADSCALE_SERVER_URL。", "HEADSCALE_SERVER_URL is required."),
    "minio": ("必须设置 MINIO_ROOT_USER/PASSWORD。", "MINIO_ROOT_USER/PASSWORD are required."),
    "registry": ("无 TLS；公网需反代。", "No TLS; put it behind a reverse proxy on the public network."),
    "unpackerr": ("需与 *arr 使用相同的 /downloads 路径。", "Use the same /downloads path as *arr."),
}


def app_title(app_id):
    return NAMES.get(app_id, app_id)


def get_quirk(app_id):
    q = QUIRKS.get(app_id)
    if q:
        return q
    q = dict(DEFAULT_QUIRK)
    extra = EXTRA_DEPS.get(app_id)
    if extra:
        q["deps_zh"], q["deps_en"] = extra
    return q


def main():
    with io.open(CATALOG, encoding="utf-8") as f:
        catalog = json.load(f)

    apps = {}
    for item in catalog:
        image = item["image"]
        app_id = image.split("/", 1)[1]
        if app_id in SKIP:
            continue
        q = get_quirk(app_id)
        notes = item.get("notes", "")
        verification = item.get("verification", "")
        name = app_title(app_id)
        category = CATEGORY.get(app_id, "Utilities")
        disclosure_zh = (
            "架构：linux/loong64（仅龙芯 3A5000/3A6000，x86/ARM 无法运行）\n"
            f"龙芯版说明：{q['zh']}\n"
            f"缺失功能：{q['missing_zh']}\n"
            f"额外依赖：{q['deps_zh']}\n"
            f"镜像说明：{notes}"
        )
        disclosure_en = (
            "Architecture: linux/loong64 only (Loongson 3A5000/3A6000; x86/ARM images will not run)\n"
            f"LoongArch notes: {q['en']}\n"
            f"Missing features: {q['missing_en']}\n"
            f"Extra dependencies: {q['deps_en']}\n"
            f"Image notes: {notes}"
        )
        apps[app_id] = {
            "image": image,
            "title": {"zh_cn": name, "en_us": name},
            "category": category,
            "architecture": "linux/loong64",
            "tagline": {"zh_cn": f"{name} 的 LoongArch64 镜像，详见龙芯版说明。", "en_us": f"{name} LoongArch64 image; see the LoongArch notes."},
            "quirk": {"zh_cn": q["zh"], "en_us": q["en"]},
            "missing": {"zh_cn": q["missing_zh"], "en_us": q["missing_en"]},
            "dependencies": {"zh_cn": q["deps_zh"], "en_us": q["deps_en"]},
            "notes": notes,
            "verification": verification,
            "disclosure": {"zh_cn": disclosure_zh, "en_us": disclosure_en},
            "casaos_description": {
                "zh_cn": "**龙芯版说明**\n\n" + disclosure_zh,
                "en_us": "**LoongArch notes**\n\n" + disclosure_en,
            },
            "istore_description_html": {
                "zh_cn": "<p><strong>龙芯版说明</strong></p><p>架构：linux/loong64（仅龙芯 3A5000/3A6000）</p>"
                f"<p>与上游差异：{q['zh']}</p><p>缺失功能：{q['missing_zh']}</p>"
                f"<p>额外依赖：{q['deps_zh']}</p><p>镜像说明：{notes}</p>",
                "en_us": "<p><strong>LoongArch notes</strong></p><p>Architecture: linux/loong64 only</p>"
                f"<p>Differences: {q['en']}</p><p>Missing features: {q['missing_en']}</p>"
                f"<p>Extra dependencies: {q['deps_en']}</p><p>Image notes: {notes}</p>",
            },
        }

    doc = {
        "schema": 1,
        "generated": "2026-10-24",
        "architecture": "linux/loong64",
        "app_count": len(apps),
        "sources": ["images/catalog.json", "docs/LOONG64-QUIRKS.md"],
        "policy": "每张商店卡片必须同时展示架构、与上游差异、缺失功能、额外依赖；禁止只写应用名或“可安装”。",
        "apps": apps,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    casaos_export = os.path.join(ROOT, "store", "exports", "casaos-descriptions.json")
    istore_export = os.path.join(ROOT, "store", "exports", "istore-descriptions.json")
    os.makedirs(os.path.dirname(casaos_export), exist_ok=True)
    with io.open(casaos_export, "w", encoding="utf-8", newline="\n") as f:
        json.dump(
            {
                "schema": 1,
                "generated": doc["generated"],
                "apps": {
                    k: {
                        "title": v["title"],
                        "category": v["category"],
                        "tagline": v["tagline"],
                        "description": v["casaos_description"],
                    }
                    for k, v in apps.items()
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")
    with io.open(istore_export, "w", encoding="utf-8", newline="\n") as f:
        json.dump(
            {
                "schema": 1,
                "generated": doc["generated"],
                "apps": {
                    k: {
                        "title": v["title"],
                        "category": v["category"],
                        "description_html": v["istore_description_html"],
                    }
                    for k, v in apps.items()
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")

    with io.open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 商店卡片“龙芯版说明”预览\n\n")
        f.write(f"共 {len(apps)} 个可安装应用（不含运行时基础镜像 node）。\n\n")
        f.write("| 应用 | 分类 | 龙芯版说明 | 缺失功能 | 额外依赖 |\n|---|---|---|---|---|\n")
        for app_id, a in apps.items():
            q = a["quirk"]["zh_cn"].replace("|", "\\|")
            m = a["missing"]["zh_cn"].replace("|", "\\|")
            d = a["dependencies"]["zh_cn"].replace("|", "\\|")
            f.write(f"| {a['title']['zh_cn']} (`{app_id}`) | {a['category']} | {q} | {m} | {d} |\n")
    print(f"wrote {len(apps)} apps")


if __name__ == "__main__":
    main()
