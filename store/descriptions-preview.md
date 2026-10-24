# 商店卡片“龙芯版说明”预览

共 110 个可安装应用（不含运行时基础镜像 node）。

| 应用 | 分类 | 龙芯版说明 | 缺失功能 | 额外依赖 |
|---|---|---|---|---|
| Jellyfin (`jellyfin`) | Media | .NET 9 自编 + ImageSharp 编码器。 | 无 ICC 色彩管理；纯托管性能低于 Skia；硬件转码未验证。 | 媒体目录与 config 需持久化。 |
| Navidrome (`navidrome`) | Media | Go + 系统 taglib；DSD 已编译。 | DSD 真实播放尚未全量验证。 | 音乐目录需只读挂载。 |
| Vaultwarden (`vaultwarden`) | Security | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Uptime Kuma (`uptimekuma`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Mihomo (`mihomo`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| EasyTier (`easytier`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Syncthing (`syncthing`) | Cloud | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| AdGuard Home (`adguardhome`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需 host 网络并避让宿主 dnsmasq。 |
| Memos (`memos`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Gogs (`gogs`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| File Browser (`filebrowser`) | Cloud | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| qBittorrent (Enhanced Edition) (`qbittorrent-ee`) | Downloaders | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| IT-Tools (`it-tools`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Excalidraw (`excalidraw`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Kopia (`kopia`) | Backup | Web UI 强制 Basic 认证。 | 默认凭据需修改。 | 仓库存储需持久化。 |
| Linkding (`linkding`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Heimdall (`heimdall`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Nextcloud (`nextcloud`) | Cloud | 当前镜像使用 SQLite。 | 生产不建议 SQLite；无外部数据库自动配置。 | 仅适合测试/轻量使用；持久化 config 与 data。 |
| Typecho (`typecho`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Wallabag (`wallabag`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| draw.io (`drawio`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Jackett (`jackett`) | Downloaders | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| xTeVe (`xteve`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| One API (`one-api`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| code-server (`code-server`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| DPanel (`dpanel`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需挂载 docker.sock。 |
| Shiori (`shiori`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Jellyseerr (`jellyseerr`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Audiobookshelf (`audiobookshelf`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Calibre-Web (`calibre-web`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Homarr (`homarr`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需 Redis。 |
| Open WebUI (`openwebui`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| KodExplorer (`kodexplorer`) | Cloud | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Home Assistant (`homeassistant`) | Home Automation | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 建议 host 网络以发现设备。 |
| Sonarr (`sonarr`) | Downloaders | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Radarr (`radarr`) | Downloaders | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Tautulli (`tautulli`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Jellystat (`jellystat`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需外部 PostgreSQL。 |
| Stirling PDF (`stirling-pdf`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Wizarr (`wizarr`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Gitea (`gitea`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Miniflux (`miniflux`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需外部 PostgreSQL。 |
| Portainer (`portainer`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需挂载 docker.sock。 |
| Nginx Proxy Manager (`nginx-proxy-manager`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Firefly III (`firefly-iii`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| phpMyAdmin (`phpmyadmin`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| FreshRSS (`freshrss`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Prowlarr (`prowlarr`) | Downloaders | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Bazarr (`bazarr`) | Downloaders | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| homer (`homer`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Paperless-ngx (`paperless-ngx`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Dashy (`dashy`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Watchtower (`watchtower`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需挂载 docker.sock。 |
| ChangeDetection.io (`changedetection`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Caddy (`caddy`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Dozzle (`dozzle`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需挂载 docker.sock。 |
| ntfy (`ntfy`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Gotify (`gotify`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Node Exporter (`node-exporter`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Prometheus (`prometheus`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Pi-hole (`pihole`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需 host 网络并避让宿主 dnsmasq。 |
| Gatus (`gatus`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Alertmanager (`alertmanager`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| PostgreSQL (`postgres`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Redis (`redis`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Eclipse Mosquitto (`mosquitto`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| MariaDB (`mariadb`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Node-RED (`node-red`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Grafana (`grafana`) | Monitoring | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Memcached (`memcached`) | Networking | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Homebridge (`homebridge`) | Home Automation | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 建议 host 网络；需改默认配对码。 |
| REST Server (`rest-server`) | Backup | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Actual Budget (`actual-budget`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| MinIO (`minio`) | Cloud | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 必须设置 MINIO_ROOT_USER/PASSWORD。 |
| HomeBox (`homebox`) | Productivity | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| NocoDB (`nocodb`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Apprise API (`apprise-api`) | Utilities | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| Mealie (`mealie`) | Productivity | Python 3.14 源码构建。 | 不支持 HEIF/HEIC。 | 持久化 /app/data；UID 911。 |
| ChineseSubFinder (`chinesesubfinder`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| LANraragi (`lanraragi`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| OwnTone (`owntone`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| MyMind (`mymind`) | Media | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 无额外外部依赖。 |
| WebVirtCloud (`webvirtcloud`) | Developer | 未发现与上游应用的已知行为差异；仅镜像架构为 linux/loong64。 | 无已知缺失功能（尚未逐项做上游功能回归）。 | 需 libvirt/KVM 与 SSH 凭据。 |
| Penpot (backend) (`penpot-backend`) | Developer | Penpot 前后端拆成两个镜像；后端用 JDK 21 运行官方 jar。 | 无 exporter（PDF/PNG 导出会 502）；无 admin-console/MCP。 | 需 PostgreSQL + Redis；PENPOT_SECRET_KEY 必填。 |
| Penpot (frontend) (`penpot-frontend`) | Developer | Penpot 前端单独成镜像，通过 nginx 反代后端。 | 同上；导出功能未移植。 | 需同时部署 penpot-backend、PostgreSQL、Redis。 |
| Hermes (`hermes`) | Developer | 使用 Python 3.14 独立构建；镜像保留 gcc/rust 工具链。 | 不支持 HEIC/HEIF；computer_use 在 loongarch64 不可用。 | 默认无 WebUI 密码；镜像约 3.68GB。 |
| Zigbee2MQTT (`zigbee2mqtt`) | Home Automation | Node 24 + pnpm；serialport 针对 loongarch64 源码编译。 | 没有 USB 协调器时容器会退出。 | 需 /dev/ttyACM0 或 /dev/serial/by-id/*，以及 dialout 组。 |
| smartctl_exporter (`smartctl-exporter`) | Monitoring | 仅暴露 Prometheus 指标，没有 UI 和历史库。 | 无内置历史/告警。 | 需 SYS_RAWIO/SYS_ADMIN 与设备直通；默认无认证。 |
| SFTPGo (`sftpgo`) | Cloud | Go + CGO SQLite；首次进入安装页创建管理员。 | 默认不创建管理员；FTP/WebDAV 默认关闭。 | 持久化 /srv/sftpgo/data 与 /var/lib/sftpgo；公网需 TLS。 |
| BookStack (`bookstack`) | Productivity | PHP 8.3 + nginx/php-fpm；首次启动自动生成 .env。 | 必须使用 MariaDB/MySQL，不支持 SQLite。 | 需 MariaDB/MySQL；持久化 storage 与 public/uploads；首次用 artisan 建管理员。 |
| Vikunja (`vikunja`) | Productivity | Vue 前端在 x86 构建；后端 Go + CGO SQLite。 | 默认允许注册，生产环境需关闭。 | service.interface 必须为 0.0.0.0:3456；PUBLICURL 必须正确；持久化 /db。 |
| Piwigo (`piwigo`) | Cloud | 首次启动自动 POST install.php 完成安装。 | 必须使用 MariaDB/MySQL。 | 需 MariaDB/MySQL；持久化 local、_data、galleries、upload。 |
| go2rtc (`go2rtc`) | Media | 单二进制，无 ffmpeg 依赖。 | 默认无摄像头流配置、无认证。 | 1984 API、8554 RTSP、8555 WebRTC；跨 NAT 需配置 candidates。 |
| Scrutiny (`scrutiny`) | Monitoring | 使用 SQLite metrics 补丁，不再依赖 InfluxDB；历史数据保存在 SQLite。 | 不迁移旧 InfluxDB 历史；无保留/降采样任务；collector 需外部 cron/exec 触发。 | 需 SYS_RAWIO/SYS_ADMIN 与磁盘设备直通；运行镜像含 libstdc++/libgcc。 |
| Headscale (`headscale`) | Networking | 单二进制，无 Web UI；通过 CLI/API 管理。 | 无图形界面；gRPC 默认仅本机。 | HEADSCALE_SERVER_URL 必填；持久化 /etc/headscale 与 /var/lib/headscale。 |
| Backrest (`backrest`) | Backup | 前端在 x86 构建后内嵌；自带 restic 0.19.1。 | 首次需在 UI 建账号/仓库；默认无认证。 | 持久化 /data、/config、/cache；备份源目录需额外挂载。 |
| Authelia (`authelia`) | Security | 自动生成配置/用户库/密钥；单机 SQLite。 | 无内置 TLS；默认 one_factor，forward-auth 需反代配置。 | AUTH_DOMAIN/AUTH_URL 必须是 HTTPS 正式域名；持久化 /config。 |
| Ente Server (`ente-server`) | Cloud | 仅 API；museum.yaml 首次启动生成。 | 不自带 Web 图库，需要 ente-web。 | 需 PostgreSQL + S3/MinIO 三个桶；/data/museum.yaml 含密钥必须备份。 |
| Autobrr (`autobrr`) | Downloaders | 前端在 x86 构建后内嵌；使用 SQLite。 | 默认无认证；需自行配置 IRC 和下载器。 | 持久化 /config；公网需反代认证。 |
| Matomo (`matomo`) | Productivity | 官方完整包；PHP 8.3 + nginx/php-fpm。 | 首次必须走 Web 安装向导；没有 CLI 安装器。 | 必须 MariaDB/MySQL；持久化 config/tmp；归档需 cron。 |
| Woodpecker CI (server) (`woodpecker-server`) | Developer | 前端 x86 构建后内嵌；CGO SQLite。 | 不配置 forge（Gitea/GitHub 等）无法启动；无内置账号体系。 | 持久化 /var/lib/woodpecker；WOODPECKER_HOST 必须是外部可访问 URL。 |
| Woodpecker CI (agent) (`woodpecker-agent`) | Developer | Go CGO-free；UID 1114。 | 无业务端口，仅 3000 健康检查；必须能访问 Docker daemon。 | 挂载 docker.sock 并加匹配的 --group-add；agent secret 与 server 一致；等同宿主 root。 |
| Ente Web (`ente-web`) | Cloud | 10 个 Next 应用纯静态导出，由 nginx 托管。 | 无 Next 服务端/API/图片优化器；未知路径回退到 index.html；不保证逐字节可复现。 | 必须设置 ENTE_API_ORIGIN；端口 3000–3006、3008–3010。 |
| MeTube (`metube`) | Downloaders | Python 3.13 自编；Angular 前端在 x86 构建。 | 无 Brotli 解压；无内置 bgutil-pot；ffmpeg 为 6.1.1 而非上游 8.1。 | 持久化 /downloads 并 chown 1111；默认用 Node 24 作为 yt-dlp JS runtime；8082。 |
| SABnzbd (`sabnzbd`) | Downloaders | Python 3.11 + venv；par2/unrar 源码编译。 | 无 orjson（ujson 回退，性能略低）；unrar 为闭源 freeware。 | 持久化 /config 与 /downloads；UI 根路径是 / 而不是 /sabnzbd/。 |
| MediaMTX (`mediamtx`) | Media | Go 单二进制，配置内嵌。 | 无 Web 管理界面/持久化；API 默认仅本机白名单。 | 8554/1935/8888/8889/8890/9997；NAT 后 WebRTC 需配 additional hosts；与 go2rtc 二选一。 |
| Docker Registry (`registry`) | Developer | Go 单二进制；首次启动生成 htpasswd。 | 无 Web UI、无 TLS、无多实例共享存储；删除后需手动 GC。 | 持久化 /var/lib/registry 与 /auth；/auth/password 是唯一密码来源；Docker CLI 需 insecure-registries。 |
| Unpackerr (`unpackerr`) | Downloaders | Go 单二进制；需要升级 x/sys 才能支持 loongarch64。 | 无 Web UI/端口；健康检查仅进程存活；未接真实 *arr。 | 持久化 /config 与 /downloads，路径必须与 *arr 一致；unrar 为闭源 freeware。 |
| Pocket ID (`pocket-id`) | Security | SvelteKit 前端在 x86 构建后内嵌；Go 单二进制。 | 未做邮件 SMTP/SCIM/Passkey 全链路；与 Authelia 二选一。 | 持久化 /data（含加密密钥）；APP_URL 必填为外部地址；1411。 |
| Readeck (`readeck`) | Productivity | gulp 前端在 x86 构建；Go 使用 CGO/mattn sqlite。 | CGO-free 的 modernc 旧版缺 loongarch64 定义；未做完整抓取联调。 | 持久化 /data；8000；与 Wallabag/Shiori 重叠。 |
