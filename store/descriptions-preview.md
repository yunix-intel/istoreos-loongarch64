# 商店卡片“龙芯版说明”预览

共 115 个可安装应用（不含运行时基础镜像 node）。

| 应用 | 分类 | 龙芯版说明 | 缺失功能 | 额外依赖 |
|---|---|---|---|---|
| Jellyfin (`jellyfin`) | Media | .NET 9 自编 + ImageSharp 编码器。 | 无 ICC 色彩管理；纯托管性能低于 Skia；硬件转码未验证。 | 媒体目录与 config 需持久化。 |
| Navidrome (`navidrome`) | Media | Go + 系统 taglib；DSD 已编译。 | DSD 真实播放尚未全量验证。 | 音乐目录需只读挂载。 |
| Vaultwarden (`vaultwarden`) | Security | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Uptime Kuma (`uptimekuma`) | Monitoring | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Mihomo (`mihomo`) | Networking | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| EasyTier (`easytier`) | Networking | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Syncthing (`syncthing`) | Cloud | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| AdGuard Home (`adguardhome`) | Networking | 官方无 loong64 资产，源码自编 + 官方前端。 | 53 端口需避让宿主 dnsmasq。 | 建议 host 网络；3000 Web；持久化 work/conf。 |
| Memos (`memos`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Gogs (`gogs`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| File Browser (`filebrowser`) | Cloud | 上游已于 2026-09-01 归档，无后续安全修复；镜像默认监听 0.0.0.0（v2.63 上游默认 127.0.0.1）。 | 无上游安全更新。 | 8080；持久化 /srv 与数据库。 |
| qBittorrent (Enhanced Edition) (`qbittorrent-ee`) | Downloaders | 官方 loong64 静态包；WebUI 校验 Host header。 | 端口映射与 WebUI 端口不一致时会拒绝访问。 | 建议让 WebUI 端口与宿主映射端口一致。 |
| IT-Tools (`it-tools`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Excalidraw (`excalidraw`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Kopia (`kopia`) | Backup | Web UI 强制 Basic 认证。 | 默认凭据需修改。 | 仓库存储需持久化。 |
| Linkding (`linkding`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Heimdall (`heimdall`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Nextcloud (`nextcloud`) | Cloud | 当前镜像使用 SQLite。 | 生产不建议 SQLite；无外部数据库自动配置。 | 仅适合测试/轻量使用；持久化 config 与 data。 |
| Typecho (`typecho`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Wallabag (`wallabag`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| draw.io (`drawio`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Jackett (`jackett`) | Downloaders | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| xTeVe (`xteve`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| One API (`one-api`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| code-server (`code-server`) | Developer | 4.141.0 + VS Code 1.141，必须 Node 24；自编静态 ripgrep。 | Node 20 缺少 module.registerHooks，不能替换运行时。 | 8443；持久化 /home/coder。 |
| DPanel (`dpanel`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 需挂载 docker.sock。 |
| Shiori (`shiori`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Jellyseerr (`jellyseerr`) | Media | Next 16 使用 WASM SWC 在 x86 构建；sharp 不可用，图片优化关闭。 | 无 Next 图片优化器；依赖上游请求服务。 | 需 Sonarr/Radarr 等上游服务；5055。 |
| Audiobookshelf (`audiobookshelf`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Calibre-Web (`calibre-web`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Homarr (`homarr`) | Networking | Next 16 WASM SWC + Node 24；未使用 Bun/Turbo。 | Bun/Turbo 构建链未移植；依赖 Redis。 | 需 Redis；7575。 |
| Open WebUI (`openwebui`) | Developer | 仅推理模式：不含 torch/onnxruntime/whisper/OCR 与内置模型。 | 本地推理、语音、OCR 不可用；RAG 需外部 pgvector。 | 需外部 Ollama/OpenAI 兼容服务；RAG 需 PostgreSQL + pgvector。 |
| KodExplorer (`kodexplorer`) | Cloud | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Home Assistant (`homeassistant`) | Home Automation | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 建议 host 网络以发现设备。 |
| Sonarr (`sonarr`) | Downloaders | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Radarr (`radarr`) | Downloaders | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Tautulli (`tautulli`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Jellystat (`jellystat`) | Media | Node 20 + Vite 6。 | 无 SQLite 路径，必须外部 PostgreSQL。 | 需 PostgreSQL；3000。 |
| Stirling PDF (`stirling-pdf`) | Media | 官方 jar + Java 25。 | 未装 LibreOffice/OCR，相关转换不可用。 | 8080；首次可按需在 UI 配置。 |
| Wizarr (`wizarr`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Gitea (`gitea`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Miniflux (`miniflux`) | Utilities | 上游已删除 SQLite 支持，必须提供 PostgreSQL DSN。 | 不支持 SQLite。 | 需 PostgreSQL；8080。 |
| Portainer (`portainer`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 需挂载 docker.sock。 |
| Nginx Proxy Manager (`nginx-proxy-manager`) | Networking | 前端在 x64 构建；自定义 entrypoint 替代 s6-overlay。 | s6-overlay 的进程管理行为未完全复刻。 | 81/443；持久化 data 与 letsencrypt。 |
| Firefly III (`firefly-iii`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| phpMyAdmin (`phpmyadmin`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| FreshRSS (`freshrss`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Prowlarr (`prowlarr`) | Downloaders | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Bazarr (`bazarr`) | Downloaders | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| homer (`homer`) | Networking | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Paperless-ngx (`paperless-ngx`) | Productivity | qpdf 12.4.2 自编以支持 pikepdf；AI 功能关闭；未装 unpaper。 | 无 AI 分类/实体识别；无 unpaper 后处理。 | 需 Redis + celery worker/beat/consumer；8000。 |
| Dashy (`dashy`) | Networking | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Watchtower (`watchtower`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 需挂载 docker.sock。 |
| ChangeDetection.io (`changedetection`) | Monitoring | 使用 Firefox 140.11 ESR + geckodriver/Selenium，不是 Playwright；OpenCV SSIM 使用 numpy 1.26.4。 | 无本地 Chrome；可配置远程 Chrome WebDriver。 | 需 --shm-size=1g；5000；持久化 /datastore。 |
| Caddy (`caddy`) | Networking | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Dozzle (`dozzle`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 需挂载 docker.sock。 |
| ntfy (`ntfy`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Gotify (`gotify`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Node Exporter (`node-exporter`) | Monitoring | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Prometheus (`prometheus`) | Monitoring | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Pi-hole (`pihole`) | Networking | FTL 6.8 源码编，版本自报 UNKNOWN；内置 pihole CLI 与 pihole-adlist。 | 需 host 网络；宿主 dnsmasq 占用 53 时不可用。 | 53/tcp+udp、80；持久化 /etc/pihole。 |
| Gatus (`gatus`) | Monitoring | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Alertmanager (`alertmanager`) | Monitoring | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| PostgreSQL (`postgres`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Redis (`redis`) | Utilities | openEuler 7.2.14 包；AOF+RDB。 | 默认 protected-mode no，必须配密码或限制网络。 | 6379；持久化 /data。 |
| Eclipse Mosquitto (`mosquitto`) | Utilities | openEuler 2.0.20 包。 | 默认 allow_anonymous true，公网必须配 passwd。 | 1883；持久化 /mosquitto/data。 |
| MariaDB (`mariadb`) | Utilities | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Node-RED (`node-red`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Grafana (`grafana`) | Monitoring | 前端在 x86 构建；Go CGO-free 编。 | 未内置 renderer；默认 admin/admin。 | 3000；持久化 /var/lib/grafana。 |
| Memcached (`memcached`) | Networking | openEuler 1.6.42 包；默认 64MB/1024 连接。 | 无认证、无持久化，禁止公网暴露。 | 11211；用 MEMCACHED_* 调整。 |
| Homebridge (`homebridge`) | Home Automation | Homebridge 2.4.0 + Config UI 5.29.0 + Node 24；node-pty 源码编 loongarch64。 | 建议 host 网络；默认配对码需修改。 | 8581 Web、51826；持久化 /homebridge。 |
| REST Server (`rest-server`) | Backup | Go 静态编译，镜像约 12MB。 | 默认开启认证；无 TLS。 | 8000；用 httpd-tools 的 htpasswd 建用户。 |
| Actual Budget (`actual-budget`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| MinIO (`minio`) | Cloud | Go 源码编；单目录模式无纠删码。 | 无纠删码/多盘冗余；无内置 TLS。 | 必须设 MINIO_ROOT_USER/PASSWORD；AGPLv3；9000/9001。 |
| HomeBox (`homebox`) | Productivity | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| NocoDB (`nocodb`) | Developer | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| Apprise API (`apprise-api`) | Utilities | Python 3.11 + 系统 cryptography/gevent；nginx+supervisor+gunicorn。 | 默认无认证/无 TLS。 | 8000；持久化 /config、/attach、/plugin。 |
| Mealie (`mealie`) | Productivity | Python 3.14 源码构建。 | 不支持 HEIF/HEIC。 | 持久化 /app/data；UID 911。 |
| ChineseSubFinder (`chinesesubfinder`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| LANraragi (`lanraragi`) | Media | Perl 0.9.81 + 126 个 CPAN 模块；内置 Redis。 | 默认无认证。 | 3000；持久化 content/thumb/database；UID 9001。 |
| OwnTone (`owntone`) | Media | DAAP/DACP/AirPlay 服务端；运行期需 dbus 与 avahi。 | AirPlay 发现依赖宿主网络与 avahi。 | 3689；挂载 /srv/music 与缓存。 |
| MyMind (`mymind`) | Media | 此镜像为 LoongArch 适配构建；上游主要功能保留，但尚未逐项做行为回归，镜像说明中列出的限制同样适用。 | 未逐项验证上游全部功能；请以镜像说明中的限制为准。 | 无额外外部依赖（镜像说明中另有注明的除外）。 |
| WebVirtCloud (`webvirtcloud`) | Developer | Django 4.2 + Python 3.11 + libvirt + noVNC。 | 需真实 libvirt/KVM 与 SSH 凭据；noVNC WebSocket 需反代。 | 80；持久化 data 与 .ssh。 |
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
| wg-easy (`wg-easy`) | Utilities | v15.4.0 在龙芯原生构建；libsql 使用龙芯 0.5.13 绑定，argon2 换成 hash-wasm。 | AmneziaWG 未启用；IPv6 关闭；真实客户端握手/隧道尚未验证。 | 需 NET_ADMIN，建议 SYS_MODULE + /lib/modules；sysctls；51820/udp、51821；/etc/wireguard 持久化。 |
| komga (`komga`) | Utilities | 官方 jar 不重编；自编 loongarch64 sqlite-jdbc JNI，经 org.sqlite.lib.path 外挂。 | HEIF/JXL 封面不可用；Kobo 转换未支持；PDF/EPUB/RAR 扫描未验证。 | JDK 21；/config 与 /data（可只读）；25600；UID 1110。 |
| karakeep (`karakeep`) | Utilities | 复用 node-sharp；Next 在 x86 构建；默认不内置 Chromium。 | 搜索需外部 Meilisearch；截图/PDF/JS 页面需 LBrowser sidecar；monolith/视频/OCR/AI 尚未验证。 | BROWSER_WEB_URL 接 LBrowser（挂载宿主 /opt/apps/lbrowser:ro）；/data；3000；UID 1116。 |
| linkwarden (`linkwarden`) | Utilities | Next 15 在 x86 构建；Prisma 7 WASM + adapter-pg；自写 99 个 SQL 迁移器；bcryptjs 替代 bcrypt。 | 无 Meilisearch 时仅 SQL contains 搜索；默认无浏览器；monolith/AI/导入/OAuth 尚未验证。 | 需 PostgreSQL；PLAYWRIGHT_WS_URL 接 LBrowser sidecar；/data/data；3000；UID 1118。 |
| joplin-server (`joplin-server`) | Utilities | 全程 loongarch64 构建；sqlite3 5.1.6 源码编译；Rollup 使用 wasm 别名。 | 无 sharp/sqlite-vec/PM2；向量搜索禁用；未验证桌面客户端双端同步、LDAP/SAML/Stripe/邮件。 | 需 PostgreSQL；/data 持久化（含临时 SQLite）；22300；UID 1119；APP_BASE_URL 必填。 |
