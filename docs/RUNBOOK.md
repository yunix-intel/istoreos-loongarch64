# 运行手册（loong64 应用镜像）

所有镜像只支持 `linux/loong64`，标签为 `loong64` / `24.10-la5`。
启动前先确认宿主机是龙芯 3A5000/3A6000 或同级 LoongArch64。

## 1. 通用约定

- 需要 DNS/DHCP、广播、mDNS 的应用使用 `--network=host`（AdGuardHome、mihomo、easytier 等）。
- 持久数据一律挂卷；不要依赖容器可写层。
- 首次启动前看 `docker logs -f <name>`，不要只看 `docker ps`。
- 健康检查：优先用应用自己的 `/health`、`/ping`、`/api/...`，不要只看端口通。
- 端口冲突时改宿主端口；镜像内端口不变。

## 2. 新增镜像的启动命令

### Homer / Dashy

```bash
docker run -d --name homer -p 8080:8080 \
  -v /srv/homer/config.yml:/usr/share/nginx/html/assets/config.yml:ro \
  yunixintel/homer:loong64

docker run -d --name dashy -p 8081:8080 \
  -v /srv/dashy/conf.yml:/usr/share/nginx/html/conf.yml:ro \
  yunixintel/dashy:loong64
```

### Paperless-ngx

```bash
docker run -d --name paperless -p 8000:8000 \
  -v /srv/paperless:/data \
  -e PAPERLESS_ADMIN_USER=admin \
  -e PAPERLESS_ADMIN_PASSWORD='change-me' \
  yunixintel/paperless-ngx:loong64
```

首次启动会迁移数据库；OCR 语言为 `eng`，含 `chi_sim`。AI 功能关闭，`unpaper` 未安装。

### Watchtower

```bash
docker run -d --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  yunixintel/watchtower:loong64 --label-enable --interval 3600
```

`--label-enable` 只更新带 `com.centurylinklabs.watchtower.enable=true` 的容器，避免误更新全部服务。

### changedetection.io

```bash
docker run -d --name changedetection -p 5000:5000 --shm-size=1g \
  -v /srv/changedetection:/datastore \
  yunixintel/changedetection:loong64
```

- 默认使用 Firefox + geckodriver；`WEBDRIVER_BROWSER=chrome` + `WEBDRIVER_URL` 可切远程 Chrome。
- 截图/SSIM/浏览器步骤已内置；浏览器步骤由 Selenium 执行。
- `image_ssim_diff` 在 UI 中选择，或改 `watch.json` 的 `processor` 字段（API enum 不含它）。

### Caddy

```bash
docker run -d --name caddy -p 80:80 -p 443:443 \
  -v /srv/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  -v /srv/caddy/data:/data -v /srv/caddy/config:/config \
  yunixintel/caddy:loong64
```

默认 Caddyfile 只监听 8080 并返回欢迎页；生产请挂自己的配置。

### Dozzle

```bash
docker run -d --name dozzle -p 9999:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  yunixintel/dozzle:loong64
```

scratch 镜像，无 shell；排障用 `docker logs` 或另起 debug 容器。

### ntfy

```bash
docker run -d --name ntfy -p 8080:8080 \
  -v /srv/ntfy/cache:/var/cache/ntfy \
  -v /srv/ntfy/etc:/etc/ntfy \
  yunixintel/ntfy:loong64 serve --listen-http 0.0.0.0:8080
```

注意是 `--listen-http`；默认端口 80，容器内显式改 8080。

### Gotify

```bash
docker run -d --name gotify -p 8080:8080 \
  -v /srv/gotify:/data \
  -e GOTIFY_SERVER_PORT=8080 \
  -e GOTIFY_DATABASE_DIALECT=sqlite3 \
  -e GOTIFY_DATABASE_CONNECTION=/data/gotify.db \
  yunixintel/gotify:loong64
```

### PostgreSQL

```bash
docker run -d --name postgres \
  -e POSTGRES_USER=app -e POSTGRES_PASSWORD='change-me' -e POSTGRES_DB=appdb \
  -p 5432:5432 -v pgdata:/var/lib/postgresql/data \
  yunixintel/postgres:loong64
```

- 连接串：`postgres://app:change-me@<host>:5432/appdb?sslmode=disable`。
- 首启自动 `initdb`；`POSTGRES_HOST_AUTH_METHOD` 默认 `scram-sha-256`，可设 `trust`。
- 挂宿主目录时要 `chown -R 26:26 <dir>`（openEuler 的 postgres UID/GID 为 26）。
- 数据目录必须为空（可含 `lost+found`），ext4 分区建议挂子目录。
- 日志已关闭 `logging_collector`，直接看 `docker logs postgres`。
- 完整说明见 [../images/postgres/BUILD.md](../images/postgres/BUILD.md)。

### Redis

```bash
docker run -d --name redis -p 6379:6379 -v redis-data:/data \
  -e REDIS_PASSWORD='change-me' yunixintel/redis:loong64
```

- 默认开启 AOF（`/data/appendonlydir`）并保留 RDB 快照规则。
- 不设 `REDIS_PASSWORD` 时无认证，只适合可信内网；公网必须设密码并加防火墙。
- 挂宿主目录时要 `chown -R 998:996 <dir>`（openEuler 的 redis UID/GID）。
- 宿主建议 `sysctl vm.overcommit_memory=1`，否则日志会有 overcommit 警告。
- 完整说明见 [../images/redis/BUILD.md](../images/redis/BUILD.md)。

### MariaDB

```bash
docker run -d --name mariadb   -e MYSQL_ROOT_PASSWORD='change-me'   -e MYSQL_DATABASE=appdb -e MYSQL_USER=app -e MYSQL_PASSWORD='app-pass'   -p 3306:3306 -v mariadb-data:/var/lib/mysql   yunixintel/mariadb:loong64
```

- root 只允许容器内 `localhost` 登录；应用使用 `MYSQL_USER`。
- `MYSQL_USER` 与 `MYSQL_DATABASE` 应成对设置，否则不会授予库权限。
- 挂宿主目录需 `chown -R 27:27 <dir>`；命名卷无需处理。
- 日志经 `/var/log/mariadb/mariadb.log -> /dev/stderr`，`docker logs` 可见。
- 修改 `MYSQL_*` 不会改变已初始化数据目录中的账号。
- 完整说明见 [../images/mariadb/BUILD.md](../images/mariadb/BUILD.md)。

### Memcached

```bash
docker run -d --name memcached -p 11211:11211   -e MEMCACHED_MEMORY=128 yunixintel/memcached:loong64
```

- 默认 64MB 内存、1024 连接、4 线程、监听 0.0.0.0:11211。
- 可用 `MEMCACHED_MEMORY`、`MEMCACHED_PORT`、`MEMCACHED_MAX_CONN`、
  `MEMCACHED_THREADS` 调整；自定义参数会覆盖默认命令。
- 无认证、无持久化，重启即清空；只给可信内网或同一 Docker 网络使用。
- PHP 应用需要镜像内已装 `memcached` 扩展；本镜像只提供服务端。
- 完整说明见 [../images/memcached/BUILD.md](../images/memcached/BUILD.md)。

### Mosquitto

```bash
docker run -d --name mosquitto -p 1883:1883   -v /srv/mosquitto/config:/mosquitto/config:ro   -v /srv/mosquitto/data:/mosquitto/data   yunixintel/mosquitto:loong64
```

- 默认配置允许匿名，仅适合可信内网；公网必须关闭匿名并配置密码。
- 生成密码文件：

```bash
mkdir -p /srv/mosquitto/config
docker run --rm -v /srv/mosquitto/config:/cfg --entrypoint mosquitto_passwd   yunixintel/mosquitto:loong64 -b -c /cfg/passwd mqtt 'change-me'
```

  配置中加 `allow_anonymous false` 和 `password_file /mosquitto/config/passwd`。
- retained 消息持久化在 `/mosquitto/data/mosquitto.db`；挂宿主目录需
  `chown -R 998:996`。
- 需要 WebSocket 时追加 `listener 9001` + `protocol websockets` 并映射 9001。
- 完整说明见 [../images/mosquitto/BUILD.md](../images/mosquitto/BUILD.md)。

### Node-RED

```bash
docker run -d --name node-red -p 1880:1880   -v node-red-data:/data yunixintel/node-red:loong64
```

- 编辑器 `http://<host>:1880/`；数据、flows、settings 全在 `/data`。
- 容器以 UID/GID 1001 运行；挂宿主目录需 `chown -R 1001:1001 <dir>`。
- 首次启动会生成 `/data/settings.js`；改端口、`credentialSecret` 都在这里。
- 默认 `uiPort` 取 `PORT` 环境变量，未设置时 1880；改映射端口时同步设 `PORT`。
- 版本为 5.0.8 + Node 24.22.1；Node 运行时来自 `yunixintel/node` 基础镜像。
- 安装原生依赖的 palette 节点需要自行加回 gcc/make，运行镜像未带编译工具。
- 完整说明见 [../images/node-red/BUILD.md](../images/node-red/BUILD.md)。

### Grafana

```bash
docker run -d --name grafana -p 3000:3000   -v grafana-data:/var/lib/grafana yunixintel/grafana:loong64
```

- 登录 `http://<host>:3000/`，默认 `admin/admin`，首次登录要求改密码。
- 数据、SQLite、插件、PNG/PDF 导出都在 `/var/lib/grafana`；挂宿主目录需
  `chown -R 472:472 <dir>`。
- 添加 Prometheus 数据源时，容器内 `127.0.0.1:9090` 指向 Grafana 自己；
  bridge 网络请填宿主 IP 或 `host.docker.internal`，compose 里填服务名。
- 镜像不含 image renderer 和额外 bundled 插件；需要导出图片时另起 renderer。
- 默认 SQLite 适合家用；多副本/高并发改用外部 PostgreSQL/MySQL。
- 升级前备份整个 `/var/lib/grafana`。
- 完整说明见 [../images/grafana/BUILD.md](../images/grafana/BUILD.md)。

### Homebridge

```bash
docker run -d --name homebridge --network=host   -v homebridge-data:/homebridge yunixintel/homebridge:loong64
```

- Config UI：`http://<host>:8581/`；HomeKit 端口 `51826`。
- 必须用 host 网络才能正常 mDNS 发现；bridge 下 UI 可用但 HomeKit 常发现不了。
- 数据、config、插件都在 `/homebridge`；挂宿主目录需 `chown -R 1000:1000`。
- 默认配对码 `031-45-154`、MAC `0E:5A:2B:3C:4D:5E`，首次进入 UI 后应修改。
- 版本为 Homebridge 2.4.0 + UI 5.29.0 + Node 24.22.1；UI 由 `hb-service` 同时拉起。
  公网暴露 UI 时仍应加反向代理认证。
- 运行镜像保留 npm 但无 gcc/make，带原生编译的插件无法直接安装。
- 完整说明见 [../images/homebridge/BUILD.md](../images/homebridge/BUILD.md)。

### restic REST server

```bash
docker run -d --name rest-server -p 8000:8000   -v restic-data:/data yunixintel/rest-server:loong64
docker exec rest-server create_user backup 'change-me'
docker restart rest-server
```

- 仓库根目录 `/data`，端口 8000；认证默认开启，密码文件 `/data/.htpasswd`。
- 先 `create_user` 再重启容器，htpasswd 才会被重新加载；完全内网可
  `-e DISABLE_AUTHENTICATION=1` 关闭认证。
- 客户端：`RESTIC_REPOSITORY=rest:http://backup:change-me@<host>:8000/myrepo/`，
  注意末尾 `/`。
- 只增不删：追加参数 `--append-only`。
- 镜像不含 TLS，公网必须放在 Caddy/Nginx 反向代理后。
- 完整说明见 [../images/rest-server/BUILD.md](../images/rest-server/BUILD.md)。

### Node Exporter

```bash
docker run -d --name node-exporter --network=host \
  -v /proc:/host/proc:ro -v /sys:/host/sys:ro -v /:/rootfs:ro \
  yunixintel/node-exporter:loong64 \
  --path.procfs=/host/proc --path.sysfs=/host/sys --path.rootfs=/rootfs
```

不挂这些路径时只能看到容器命名空间指标。

### Prometheus

```bash
docker run -d --name prometheus -p 9090:9090 \
  -v /srv/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  -v /srv/prometheus/data:/prometheus \
  yunixintel/prometheus:loong64
```

最小 scrape 配置：

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: node
    static_configs:
      - targets: ["192.168.8.8:9100"]
```

### Mealie

```bash
docker run -d --name mealie -p 9000:9000   -v mealie-data:/app/data yunixintel/mealie:loong64
```

- Web UI：`http://<host>:9000/`；健康检查 `/api/app/about`。
- 数据目录 `/app/data`（SQLite、recipes、users、backups、日志）；挂宿主目录需
  `chown -R 911:911`。
- 首次访问完成管理员/家庭组初始化；`allowSignup` 默认 false。
- 镜像无内置 TLS；SQLite 单实例，不适合多副本写同一目录。
- **HEIF/HEIC 图片不支持**（loong64 缺 libheif，本镜像用 stub 禁用）。
- 完整说明见 [../images/mealie/BUILD.md](../images/mealie/BUILD.md)。

### ChineseSubFinder

```bash
docker run -d --name chinesesubfinder -p 19035:19035   -v csf-config:/config -v /path/to/media:/media   yunixintel/chinesesubfinder:loong64
```

- Web UI：`http://<host>:19035/`。
- `/config` 保存配置/数据库/日志；`/media` 挂影视目录。
- Lite 模式，内置 ffmpeg；首次启动到 UI 配置字幕站点。
- 完整说明见 [../images/chinesesubfinder/BUILD.md](../images/chinesesubfinder/BUILD.md)。

### LANraragi

```bash
docker run -d --name lanraragi -p 3000:3000   -v lanraragi-content:/home/koyomi/lanraragi/content   -v lanraragi-thumb:/home/koyomi/lanraragi/thumb   -v lanraragi-db:/home/koyomi/lanraragi/database   yunixintel/lanraragi:loong64
```

- Web `3000`；内置 Redis，首次启动自动拉起。
- 三个卷都建议持久化；数据库卷含索引。
- 默认无认证，公网暴露前务必加密码或反代认证。
- 完整说明见 [../images/lanraragi/BUILD.md](../images/lanraragi/BUILD.md)。

### OwnTone

```bash
docker run -d --name owntone -p 3689:3689   -v /path/to/music:/srv/music -v owntone-cache:/var/cache/owntone   yunixintel/owntone:loong64
```

- Web/DAAP `3689`；首次启动扫描 `/srv/music`。
- 容器内启动 dbus + avahi；AirPlay 发现建议 host 网络。
- 完整说明见 [../images/owntone/BUILD.md](../images/owntone/BUILD.md)。

### MyMind

```bash
docker run -d --name mymind -p 8080:80 yunixintel/mymind:loong64
```

- 纯静态思维导图；浏览器打开 `http://<host>:8080/`。
- 无后端、无持久化；数据在浏览器 LocalStorage/导出文件。
- 完整说明见 [../images/mymind/BUILD.md](../images/mymind/BUILD.md)。

### WebVirtCloud

```bash
docker run -d --name webvirtcloud -p 8080:80   -v webvirt-data:/srv/webvirtcloud/data   -v webvirt-ssh:/var/www/.ssh   yunixintel/webvirtcloud:loong64
```

- 登录页 `http://<host>:8080/`；首次启动自动迁移并建管理员。
- `data` 卷保存 SQLite 与 `secret_key`，必须持久化。
- noVNC 走 `/novncd/`、`/websockify`，反代需 WebSocket。
- 完整说明见 [../images/webvirtcloud/BUILD.md](../images/webvirtcloud/BUILD.md)。

### Penpot（backend + frontend）

```bash
docker network create penpot
# PostgreSQL / Redis 见 images/penpot-backend/BUILD.md
docker run -d --name penpot-backend --network penpot   -e PENPOT_PUBLIC_URI=http://<host>:9001   -e PENPOT_SECRET_KEY='<64-byte-random>'   -e PENPOT_DATABASE_URI=postgresql://penpot-postgres/penpot   -e PENPOT_DATABASE_USERNAME=penpot   -e PENPOT_DATABASE_PASSWORD=penpot   -e PENPOT_REDIS_URI=redis://penpot-redis/0   -e PENPOT_FLAGS='disable-email-verification disable-secure-session-cookies'   -v penpot-assets:/opt/data/assets yunixintel/penpot-backend:loong64
docker run -d --name penpot-frontend --network penpot -p 9001:8080   -e PENPOT_PUBLIC_URI=http://<host>:9001   -e PENPOT_BACKEND_URI=http://penpot-backend:6060   -e PENPOT_FLAGS='disable-email-verification disable-secure-session-cookies'   yunixintel/penpot-frontend:loong64
```

- Web `9001`；backend `6060`、frontend `8080` 仅容器网络内。
- 需要外部 PostgreSQL 与 Redis；`PENPOT_PUBLIC_URI` 必须与浏览器地址一致。
- 导出 PDF/PNG 需要 exporter（未移植），绘图/协作正常。
- 完整说明见 [../images/penpot-backend/BUILD.md](../images/penpot-backend/BUILD.md)。

### Hermes

```bash
docker run -d --name hermes -p 8787:8787 \
  -v hermes-data:/data/.hermes -v hermes-workspace:/workspace \
  yunixintel/hermes:loong64
```

- WebUI `http://<host>:8787/`；健康检查 `/health`。
- 容器内同时跑 `hermes gateway` 与 WebUI；任一退出会清理另一个。
- `data` 卷保存配置/会话/技能；`workspace` 是 agent 工作目录。
- 默认无密码，对外暴露前设 `HERMES_WEBUI_PASSWORD` 或加反代认证。
- HEIC/HEIF 图片不支持；`computer_use` 工具在 loongarch64 上不可用。
- 完整说明见 [../images/hermes/BUILD.md](../images/hermes/BUILD.md)。

### Zigbee2MQTT

```bash
docker run -d --name zigbee2mqtt -p 8080:8080 \
  --device /dev/ttyACM0:/dev/ttyACM0 --group-add dialout \
  -e MQTT_SERVER=mqtt://mosquitto:1883 \
  -v zigbee2mqtt-data:/app/data \
  yunixintel/zigbee2mqtt:loong64
```

- Web UI：`http://<host>:8080/`；首次启动无配置时进入 onboarding。
- `/app/data` 保存 configuration.yaml、database.db、devices.yaml、日志。
- 协调器建议用 `/dev/serial/by-id/...`；`dialout` GID 以宿主为准。
- 无协调器时容器会退出（上游行为）；先用 `Z2M_ONBOARD_FORCE_RUN=true` 可只看 UI。
- `MQTT_SERVER`/`MQTT_USER`/`MQTT_PASSWORD` 是便利变量，也可用 `ZIGBEE2MQTT_CONFIG_*`。
- 完整说明见 [../images/zigbee2mqtt/BUILD.md](../images/zigbee2mqtt/BUILD.md)。

### smartctl-exporter

```bash
docker run -d --name smartctl-exporter -p 9633:9633 \
  --cap-add SYS_RAWIO --cap-add SYS_ADMIN \
  -v /run/udev:/run/udev:ro \
  --device /dev/nvme0:/dev/nvme0 --device /dev/nvme0n1:/dev/nvme0n1 \
  yunixintel/smartctl-exporter:loong64 \
  --smartctl.device=/dev/nvme0
```

- 指标：`http://<host>:9633/metrics`；由 Prometheus 抓取，Grafana 出图。
- SATA 盘替换为 `/dev/sdX`；多盘重复 `--smartctl.device`。
- 需要 `SYS_RAWIO`；NVMe 建议 `SYS_ADMIN` 与 `/run/udev` 只读。
- 禁止 `-v /dev:/dev`；按盘逐个 `--device`。
- 镜像是只读指标 exporter，不存历史；历史由 Prometheus 保存。
- 完整说明见 [../images/smartctl-exporter/BUILD.md](../images/smartctl-exporter/BUILD.md)。

### SFTPGo

```bash
docker run -d --name sftpgo -p 8080:8080 -p 2022:2022 \
  -v sftpgo-data:/srv/sftpgo/data \
  -v sftpgo-db:/var/lib/sftpgo \
  -v sftpgo-backups:/srv/sftpgo/backups \
  yunixintel/sftpgo:loong64
```

- Web 管理/客户端：`http://<host>:8080/`；首次访问进入 `/web/admin/setup` 创建管理员。
- SFTP：`sftp -P 2022 <user>@<host>`。
- `/srv/sftpgo/data` 是用户文件根；`/var/lib/sftpgo` 存 SQLite 与 host key，必须持久化。
- FTP/WebDAV 默认关闭（端口 0）；需要时改配置。
- 公网使用必须配 TLS 或反代；默认 Web 无 HTTPS。
- 完整说明见 [../images/sftpgo/BUILD.md](../images/sftpgo/BUILD.md)。

### BookStack

```bash
docker network create bookstack
docker run -d --name bookstack-db --network bookstack \
  -e MYSQL_ROOT_PASSWORD='change-me' -e MYSQL_DATABASE=bookstack \
  -e MYSQL_USER=bookstack -e MYSQL_PASSWORD='bookpass' \
  -v bookstack-db:/var/lib/mysql yunixintel/mariadb:loong64
docker run -d --name bookstack --network bookstack -p 8080:80 \
  -e APP_URL=http://<host>:8080 -e DB_HOST=bookstack-db \
  -e DB_DATABASE=bookstack -e DB_USERNAME=bookstack -e DB_PASSWORD='bookpass' \
  -v bookstack-storage:/var/www/bookstack/storage \
  -v bookstack-uploads:/var/www/bookstack/public/uploads \
  yunixintel/bookstack:loong64
```

- Web：`http://<host>:8080/`；健康检查 `/login`。
- 必须外接 MariaDB/MySQL；不支持 SQLite。
- `storage`（含 `app.key`）与 `public/uploads` 必须持久化。
- 首次创建管理员：
  `docker exec -u nginx -w /var/www/bookstack bookstack php artisan bookstack:create-admin --email=... --name=... --password=... --initial`。
- 完整说明见 [../images/bookstack/BUILD.md](../images/bookstack/BUILD.md)。

### Vikunja

```bash
docker run -d --name vikunja -p 3456:3456 \
  -e VIKUNJA_SERVICE_PUBLICURL=http://<host>:3456/ \
  -v vikunja-files:/app/vikunja/files \
  -v vikunja-db:/db \
  yunixintel/vikunja:loong64
```

- Web/API：`http://<host>:3456/`；健康检查 `/health`。
- `/app/vikunja/files` 存附件；`/db` 存 SQLite 与 JWT secret，必须持久化。
- `VIKUNJA_SERVICE_PUBLICURL` 必须与浏览器地址一致；默认允许注册，生产建议关闭。
- 默认无 TLS；公网放在反代之后。
- 完整说明见 [../images/vikunja/BUILD.md](../images/vikunja/BUILD.md)。

### Piwigo

```bash
docker network create piwigo
docker run -d --name piwigo-db --network piwigo \
  -e MYSQL_ROOT_PASSWORD='change-me' -e MYSQL_DATABASE=piwigo \
  -e MYSQL_USER=piwigo -e MYSQL_PASSWORD='piwigo-pass' \
  -v piwigo-db:/var/lib/mysql yunixintel/mariadb:loong64
docker run -d --name piwigo --network piwigo -p 8080:80 \
  -e PIWIGO_DB_HOST=piwigo-db -e PIWIGO_DB_NAME=piwigo \
  -e PIWIGO_DB_USER=piwigo -e PIWIGO_DB_PASSWORD='piwigo-pass' \
  -e PIWIGO_ADMIN_USER=admin -e PIWIGO_ADMIN_PASSWORD='change-me' \
  -e PIWIGO_ADMIN_EMAIL=admin@example.com \
  -v piwigo-local:/var/www/piwigo/local \
  -v piwigo-data:/var/www/piwigo/_data \
  -v piwigo-galleries:/var/www/piwigo/galleries \
  -v piwigo-upload:/var/www/piwigo/upload \
  yunixintel/piwigo:loong64
```

- Web：`http://<host>:8080/`；管理员 `/identification.php`。
- 首次启动自动安装；失败则打开 `/install.php` 手动完成。
- `local`/`_data`/`galleries`/`upload` 必须持久化；必须外接 MariaDB/MySQL。
- 完整说明见 [../images/piwigo/BUILD.md](../images/piwigo/BUILD.md)。

### go2rtc

```bash
docker run -d --name go2rtc \
  -p 1984:1984 -p 8554:8554 -p 8555:8555 \
  -v go2rtc-config:/config \
  yunixintel/go2rtc:loong64
```

- Web/API：`http://<host>:1984/`；RTSP `rtsp://<host>:8554/<stream>`。
- WebRTC 8555/tcp+udp；跨 NAT 需配 `webrtc.candidates` 或反代。
- `/config/go2rtc.yaml` 只开端口，摄像头流由用户添加。
- API 默认无认证；公网必须加反代认证或 `api.username/password`。
- 完整说明见 [../images/go2rtc/BUILD.md](../images/go2rtc/BUILD.md)。

### Scrutiny（SQLite 版）

```bash
docker run -d --name scrutiny -p 8080:8080 \
  --cap-add SYS_RAWIO --cap-add SYS_ADMIN \
  -v /run/udev:/run/udev:ro \
  --device /dev/nvme0:/dev/nvme0 --device /dev/nvme0n1:/dev/nvme0n1 \
  -v scrutiny-config:/opt/scrutiny/config \
  yunixintel/scrutiny:loong64
```

- Web：`http://<host>:8080/web/`；健康 `/api/health`。
- 采集一次：`docker exec scrutiny /opt/scrutiny/bin/scrutiny-collector-metrics run`。
- 镜像默认只跑 Web；collector 由宿主 cron 或 `docker exec` 调度。
- `/opt/scrutiny/config` 存 SQLite，必须持久化。
- 不再依赖 InfluxDB；SMART 历史在 SQLite。
- 完整说明见 [../images/scrutiny/BUILD.md](../images/scrutiny/BUILD.md)。

### Headscale

```bash
docker run -d --name headscale -p 8080:8080 -p 9090:9090 \
  -e HEADSCALE_SERVER_URL=https://headscale.example.com \
  -v headscale-config:/etc/headscale \
  -v headscale-data:/var/lib/headscale \
  yunixintel/headscale:loong64
```

- HTTP/API `8080`；metrics `9090`；健康 `/health`。
- 创建用户：`docker exec headscale headscale users create <name>`。
- preauth key：`docker exec headscale headscale preauthkeys create --user <id>`。
- 无 Web UI；`/etc/headscale` 与 `/var/lib/headscale` 必须持久化。
- 公网需 HTTPS 反代；gRPC 默认只监听容器内 127.0.0.1。
- 完整说明见 [../images/headscale/BUILD.md](../images/headscale/BUILD.md)。

### NocoDB

```bash
docker run -d --name nocodb -p 8080:8080   -v nocodb-data:/data yunixintel/nocodb:loong64
```

- Web UI：`http://<host>:8080/`（跳转 `/dashboard/`）；健康检查 `/api/v1/health`。
- 数据目录 `/data`（SQLite `noco.db`）；挂宿主目录需 `chown -R 1000:1000`。
- 默认 `NC_DB=sqlite3://?d=/data/noco.db`；不要写成 `sqlite3:///data/...`。
- 默认 SQLite 单实例；多实例改用 PostgreSQL/MySQL 的 `NC_DB`。
- 镜像无 TLS，公网必须放在反向代理后。
- 完整说明见 [../images/nocodb/BUILD.md](../images/nocodb/BUILD.md)。

### Apprise API

```bash
docker run -d --name apprise-api -p 8000:8000   -v apprise-config:/config -v apprise-attach:/attach -v apprise-plugins:/plugin   yunixintel/apprise-api:loong64
```

- Web UI：`http://<host>:8000/`；状态：`/status` 返回 `OK`。
- 配置/附件/插件分别持久化到 `/config`、`/attach`、`/plugin`。
- `APPRISE_STATELESS_URLS` 可设置默认通知目标；PUID/PGID 默认 1000。
- 默认无认证、无 TLS；公网部署必须加反向代理和认证。
- 完整说明见 [../images/apprise-api/BUILD.md](../images/apprise-api/BUILD.md)。

### Homebox

```bash
docker run -d --name homebox -p 7745:7745   -v homebox-data:/data yunixintel/homebox:loong64
```

- Web UI：`http://<host>:7745/`，首次打开注册管理员。
- 数据目录 `/data`（SQLite + WAL/SHM）；挂宿主目录需 `chown -R 1000:1000`。
- 默认允许注册；公网部署应在首次注册后关闭注册或加反代认证。
- 镜像无内置 TLS；SQLite 单实例，不适合多副本写同一目录。
- 完整说明见 [../images/homebox/BUILD.md](../images/homebox/BUILD.md)。

### MinIO

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001   -e MINIO_ROOT_USER=admin   -e MINIO_ROOT_PASSWORD='change-me-123'   -v minio-data:/data yunixintel/minio:loong64
```

- S3 API：`9000`；Console：`9001`；数据目录 `/data`，UID 1000。
- 必须设置 `MINIO_ROOT_USER` 和 `MINIO_ROOT_PASSWORD`，没有默认密码。
- 单目录模式没有纠删码冗余；生产多盘/分布式部署并做好备份。
- 镜像无内置 TLS，公网必须放反向代理后；Console 和 API 都要限制来源。
- 软件许可证为 GNU AGPLv3。
- 完整说明见 [../images/minio/BUILD.md](../images/minio/BUILD.md)。

### Actual Budget

```bash
docker run -d --name actual-budget -p 5006:5006   -v actual-data:/data yunixintel/actual-budget:loong64
```

- Web UI：`http://<host>:5006/`，首次打开创建服务器密码/账号。
- 数据目录 `/data`（SQLite、server-files、user-files）；挂宿主目录需
  `chown -R 1002:1002`。
- `ACTUAL_DATA_DIR`、`ACTUAL_PORT` 可覆盖默认值。
- 镜像无内置 TLS，公网必须放在 Caddy/Nginx 反向代理后；反代时设置
  `ACTUAL_TRUSTED_PROXIES`/`ACTUAL_HOSTNAME`。
- 升级前备份整个 `/data`；数据库迁移单向，降级大版本可能打不开。
- 完整说明见 [../images/actual-budget/BUILD.md](../images/actual-budget/BUILD.md)。

### Alertmanager

```bash
docker run -d --name alertmanager -p 9093:9093 -p 9094:9094 \
  -v /srv/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro \
  -v /srv/alertmanager/data:/alertmanager \
  yunixintel/alertmanager:loong64
```

- Web UI/API：`9093`；gossip 集群：`9094`。单机不需要 HA 时加
  `--cluster.listen-address=` 可关闭 9094。
- 数据目录必须以 UID 65534 可写：`chown -R 65534:65534 /srv/alertmanager/data`。
- 默认配置只有一个空的 `default` receiver，只接收告警、不发送通知；生产必须挂载自己的
  `alertmanager.yml`（webhook、邮件、企业微信等）。
- 配置预检：`docker exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml`。
- Prometheus 端对接：

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ["127.0.0.1:9093"]
```

- 首启日志出现 `gossip not settled` 是单节点等待收敛，十几秒后恢复，不影响使用。
- 完整构建/验证记录见 [../images/alertmanager/BUILD.md](../images/alertmanager/BUILD.md)。

### Pi-hole

```bash
docker run -d --name pihole --network=host --shm-size=1g \
  -v /srv/pihole/etc:/etc/pihole \
  -e FTLCONF_dns_upstreams=1.1.1.1 \
  yunixintel/pihole:loong64
```

- Web UI：`http://<host>/admin/`；DNS：53/udp+tcp。
- 首启 entrypoint 会用 `gravity.db.sql` 创建 `/etc/pihole/gravity.db`；不建的话 FTL 会反复报
  `Gravity database not available`。
- 已内置上游 `pihole` CLI、`gravity.sh` 和 `pihole-adlist`：

```bash
docker exec pihole pihole-adlist list
docker exec pihole pihole-adlist add https://example.com/hosts.txt "my list"
docker exec pihole pihole -g          # 更新 gravity
docker exec pihole pihole deny ads.example.com
```

- `pihole-adlist add/remove` 会自动调用 `pihole -g`；首次拉取后 FTL 会 reload gravity。
- 用 host 网络时宿主不能已有 dnsmasq 占用 53；否则改用端口映射并停宿主 DNS。
- FTL 版本自报 `UNKNOWN (not a GIT build)` 是源码构建的正常现象。

### Gatus

```bash
docker run -d --name gatus -p 8080:8080 \
  -v /srv/gatus/config.yaml:/config/config.yaml:ro \
  yunixintel/gatus:loong64
```

默认配置监控 `http://127.0.0.1:9090/-/healthy`；生产请挂自己的 `config.yaml`。
状态页 `/`，API `/api/v1/endpoints/statuses`。

## 3. 端口索引（全部 96 个镜像）

### 从端口索引生成最小启动命令

所有镜像名统一为 `yunixintel/<app>:loong64`。通用模板：

```bash
docker run -d --name <app>   -p <宿主端口>:<容器端口>   -v <宿主目录>:<容器目录>   -e <变量>=<值>   yunixintel/<app>:loong64
```

常见变体：

```bash
# 单端口
docker run -d --name uptimekuma -p 3001:3001   -v /srv/uptimekuma:/app/data yunixintel/uptimekuma:loong64

# 多端口
docker run -d --name minio -p 9000:9000 -p 9001:9001   -e MINIO_ROOT_USER=admin -e MINIO_ROOT_PASSWORD='change-me'   -v /srv/minio:/data yunixintel/minio:loong64

# DNS / mDNS 或需要宿主网络的
docker run -d --name pihole --network=host --shm-size=1g   -v /srv/pihole/etc:/etc/pihole yunixintel/pihole:loong64

# 需要 Docker socket 的
docker run -d --name dozzle -p 8080:8080   -v /var/run/docker.sock:/var/run/docker.sock yunixintel/dozzle:loong64
```

每个应用的具体端口、挂载和限制见下表；逐应用构建记录在
`images/<app>/BUILD.md`。

| 镜像 | 端口 | 关键挂载/环境 | 备注 |
|---|---|---|---|
| adguardhome | 53/tcp+udp, 3000 | `/opt/adguardhome/work`、`/opt/adguardhome/conf` | 用 host 网络；避让宿主 dnsmasq |
| actual-budget | 5006 | `/data` | UID 1002；SQLite；无内置 TLS |
| node | — | — | Node 运行时基础镜像，不直接对外服务 |
| homebox | 7745 | `/data` | UID 1000；SQLite；默认允许注册 |
| mealie | 9000 | `/app/data` | UID 911；SQLite；HEIF 不支持 |
| chinesesubfinder | 19035 | `/config`、`/media` | UID 1026；Lite；内置 ffmpeg |
| lanraragi | 3000 | `content`、`thumb`、`database` | UID 9001；内置 Redis；默认无认证 |
| owntone | 3689 | `/srv/music`、`/var/cache/owntone` | UID 998；容器内 avahi/dbus |
| mymind | 80 | — | 纯静态；无持久化 |
| webvirtcloud | 80 | `/srv/webvirtcloud/data`、`/var/www/.ssh` | UID 33；SQLite；noVNC WebSocket |
| penpot-backend | 6060 | `/opt/data/assets` | 需 PostgreSQL/Redis；`PENPOT_SECRET_KEY` 必填 |
| penpot-frontend | 8080 | — | 反代 penpot-backend；9001 对外 |
| hermes | 8787 | `/data/.hermes`、`/workspace` | UID 1000；默认无密码；HEIC 不支持 |
| zigbee2mqtt | 8080 | `/app/data`；`--device /dev/ttyACM0 --group-add dialout` | UID 1101；需 USB 协调器；无适配器会退出 |
| smartctl-exporter | 9633 | `/run/udev:ro`；`--device /dev/nvme0` | 需 SYS_RAWIO/SYS_ADMIN；只读指标 |
| sftpgo | 8080, 2022 | `/srv/sftpgo/data`、`/var/lib/sftpgo`、`/srv/sftpgo/backups` | UID 1103；首次安装页建管理员；默认无 TLS |
| bookstack | 80 | `/var/www/bookstack/storage`、`/var/www/bookstack/public/uploads` | 必须 MariaDB；`app.key` 持久化；首次用 artisan 建管理员 |
| vikunja | 3456 | `/app/vikunja/files`、`/db` | UID 1104；SQLite；JWT secret 持久化；默认允许注册 |
| piwigo | 80 | `local`、`_data`、`galleries`、`upload` | 必须 MariaDB；首次自动安装；管理员 `/identification.php` |
| go2rtc | 1984, 8554, 8555 | `/config` | UID 1109；默认无认证；需自配摄像头流 |
| scrutiny | 8080 | `/opt/scrutiny/config`；`--device` + SYS_RAWIO | SQLite 历史；collector 需手动/cron 触发 |
| headscale | 8080, 9090 | `/etc/headscale`、`/var/lib/headscale` | UID 1106；无 Web UI；CLI 建用户/key |
| nocodb | 8080 | `/data` | UID 1000；SQLite；`NC_DB` 用 `?d=` |
| apprise-api | 8000 | `/config`、`/attach`、`/plugin` | 默认无认证/无 TLS |
| minio | 9000, 9001 | `/data` | UID 1000；必须设根凭据；AGPLv3 |
| alertmanager | 9093, 9094 | `/etc/alertmanager/alertmanager.yml`、`/alertmanager` | 9094 为 gossip；数据卷需 UID 65534 可写 |
| postgres | 5432 | `/var/lib/postgresql/data`；环境 `POSTGRES_*` | UID 26；日志走 stdout |
| redis | 6379 | `/data`；环境 `REDIS_PASSWORD` | AOF+RDB；UID/GID 998:996 |
| mosquitto | 1883 | `/mosquitto/config`、`/mosquitto/data` | 默认匿名；公网须配 passwd |
| mariadb | 3306 | `/var/lib/mysql`；环境 `MYSQL_*` | root 仅 localhost；UID/GID 27 |
| node-red | 1880 | `/data` | UID 1001；5.0.8 + Node 24；palette 需 npm |
| grafana | 3000 | `/var/lib/grafana` | UID/GID 472；默认 admin/admin；SQLite |
| memcached | 11211 | — | 无认证无持久化；仅内网 |
| homebridge | 8581, 51826 | `/homebridge` | 建议 host 网络；UID 1000；2.4.0 + UI 5.29 + Node 24；默认配对码需改 |
| rest-server | 8000 | `/data` | 默认 Basic 认证；无 TLS |
| audiobookshelf | 13378 | `/audiobooks`、`/config`、`/metadata` | Node 22 |
| bazarr | 6767 | `/config`、`/movies`、`/tv` | 含 ffmpeg |
| calibre-web | 8083 | `/books`、`/config` | 书库挂载 |
| changedetection | 5000 | `/datastore` | `--shm-size=1g`；Firefox/Selenium/SSIM |
| code-server | 8443 | `/home/coder` | 必须 Node 24 运行时 |
| caddy | 80/443/8080 | `/etc/caddy/Caddyfile`、`/data` | 纯 Go 反代 |
| dashy | 8080 | `conf.yml` | 静态仪表盘 |
| dpanel | 8807 | `/var/run/docker.sock` | 需 Docker socket |
| dozzle | 8080 | `/var/run/docker.sock` | 日志面板 |
| drawio | 8080 | — | 静态前端 |
| easytier | — | `network.toml` | host 网络；配置含密钥 |
| excalidraw | 80 | — | 静态前端 |
| filebrowser | 8080 | `/srv`、`/database.db` | |
| firefly-iii | 8080 | `/var/www/html/storage` | PHP 8.5；SQLite |
| freshrss | 8080 | `/var/www/FreshRSS/data` | 首次安装 admin/adminadmin |
| gatus | 8080 | `config.yaml` | 状态页/监控 |
| gitea | 3000 | `/data`、`/etc/gitea` | Go 1.27；SQLite |
| gogs | 3000 | `/data` | |
| gotify | 8080 | `/data` | SQLite |
| heimdall | 80 | `/config` | PHP 8.4 |
| homarr | 7575 | `/appdata` | 需 Redis |
| homeassistant | 8123 | `/config` | Python 3.14 |
| homer | 8080 | `config.yml` | 静态仪表盘 |
| it-tools | 80 | — | 静态工具集 |
| jackett | 9117 | `/config`、`/downloads` | .NET 9 |
| jellyfin | 8096 | `/config`、`/media` | .NET 9 + ImageSharp |
| jellyseerr | 5055 | `/app/config` | Next 16 WASM |
| jellystat | 3000 | `/app/data` | 需外部 PostgreSQL |
| kodexplorer | 80 | `/var/www/html` | PHP |
| kopia | 51515 | `/app/config`、`/repository` | Web UI Basic 认证 |
| linkding | 9090 | `/etc/linkding/data` | 需 `UWSGI_MAX_FD=4096` |
| memos | 5230 | `/opt/memos/data` | |
| mihomo | — | `/etc/mihomo` | host 网络；配置含密钥 |
| miniflux | 8080 | 环境 `DATABASE_URL` | 仅 PostgreSQL |
| navidrome | 4533 | `/data`、`/music` | taglib 2.0.2，DSD |
| nextcloud | 80 | `/var/www/html/data`、`/var/www/html/config` | SQLite（生产建议外部 DB） |
| nginx-proxy-manager | 81/443 | `/data`、`/etc/letsencrypt` | |
| node-exporter | 9100 | 宿主 `/proc`、`/sys`、`/` | `--path.*` |
| ntfy | 8080 | `/var/cache/ntfy`、`/etc/ntfy` | `--listen-http` |
| one-api | 3000 | `/data` | CGO sqlite |
| openwebui | 8080 | `/app/backend/data` | 轻量版，无 torch/RAG |
| paperless-ngx | 8000 | `/data` | OCR + consumer |
| phpmyadmin | 8080 | 外部 MySQL | |
| pihole | 53/tcp+udp, 80 | `/etc/pihole` | FTL 6.8 + web；首启建 gravity.db |
| portainer | 9000 | `/var/run/docker.sock`、`/data` | |
| prometheus | 9090 | `/etc/prometheus/prometheus.yml`、`/prometheus` | `-tags builtinassets` |
| prowlarr | 9696 | `/config` | .NET 9 |
| qbittorrent-ee | 8080 | `/config`、`/downloads` | Host header 需匹配 |
| radarr | 7878 | `/config`、`/movies` | .NET 9 |
| shiori | 8080 | `/data` | 建议设 `SHIORI_HTTP_SECRET_KEY` |
| sonarr | 8989 | `/config`、`/tv` | .NET 9 |
| stirling-pdf | 8080 | `/configs` | Java 25 |
| syncthing | 8384 | `/data` | v2 CLI 用双横线 |
| tautulli | 8181 | `/config` | Python |
| typecho | 80 | `/var/www/html`、`/data` | 站点根目录含 config/db |
| uptimekuma | 3001 | `/app/data` | |
| vaultwarden | 8443 | `/data` | 内置 glibc 2.41 闭包 |
| wallabag | 80 | `/var/www/wallabag/data` | 首次 CLI 安装 |
| watchtower | — | `/var/run/docker.sock` | `--label-enable` |
| wizarr | 5690 | `/data` | |
| xteve | 34400 | `/config`、`/data` | 自带 ffmpeg |
