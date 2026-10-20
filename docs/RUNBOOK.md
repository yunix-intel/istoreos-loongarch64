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

## 3. 端口索引（全部 67 个镜像）

| 镜像 | 端口 | 关键挂载/环境 | 备注 |
|---|---|---|---|
| adguardhome | 53/tcp+udp, 3000 | `/opt/adguardhome/work`、`/opt/adguardhome/conf` | 用 host 网络；避让宿主 dnsmasq |
| alertmanager | 9093, 9094 | `/etc/alertmanager/alertmanager.yml`、`/alertmanager` | 9094 为 gossip；数据卷需 UID 65534 可写 |
| postgres | 5432 | `/var/lib/postgresql/data`；环境 `POSTGRES_*` | UID 26；日志走 stdout |
| redis | 6379 | `/data`；环境 `REDIS_PASSWORD` | AOF+RDB；UID/GID 998:996 |
| mosquitto | 1883 | `/mosquitto/config`、`/mosquitto/data` | 默认匿名；公网须配 passwd |
| mariadb | 3306 | `/var/lib/mysql`；环境 `MYSQL_*` | root 仅 localhost；UID/GID 27 |
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
