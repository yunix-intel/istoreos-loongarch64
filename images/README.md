# 应用镜像 Dockerfile 目录

本目录是 99 个 `yunixintel/*:loong64` 镜像的构建材料索引。

> **仅支持 linux/loong64**。Docker Hub 仓库名统一为 `yunixintel/<app>`（不带架构后缀），架构由 `:loong64` / `:24.10-la5` tag 与 manifest 标识；`catalog.json` 每条记录包含 `"architecture": "linux/loong64"`。x86_64 / ARM 镜像不存在。

- `images/<app>/Dockerfile`：保留了 97 个镜像的 Dockerfile（部分带 `Dockerfile.*` 构建阶段）。
- `images/<app>/BUILD.md`：99 个应用每个都有独立构建记录；无 Dockerfile 的 10 个镜像也在
  对应目录的 BUILD.md 给出归档配方和上游版本。
- `catalog.json`：99 个镜像的名称、大小、验证结论、端口/限制说明、`architecture`，机读索引。
- 未保留 Dockerfile 的 10 个镜像：adguardhome、code-server、easytier、firefly-iii、
  gitea、memos、mihomo、miniflux、phpmyadmin、vaultwarden。它们的源码版本与重建步骤
  见各自的 `BUILD.md` 和 [../docs/IMAGE-BUILD.md](../docs/IMAGE-BUILD.md) 第 3 节。
- 启动命令与端口/挂载索引见 [../docs/RUNBOOK.md](../docs/RUNBOOK.md)。

## 构建上下文说明

仓库不提交大体积源码和前端产物。使用某个 Dockerfile 时，按它的 `COPY` 行准备：

| 镜像 | 额外上下文 |
|---|---|
| homer | Homer 官方 release 的 `dist/` |
| dashy | Dashy 官方 release 的 `dist/` |
| paperless-ngx | `paperless-ngx-3.3.2/src/`、`frontend/`、`requirements.txt` |
| changedetection | 上游源码 + `wheels/jq-*.whl` + `geckodriver` + patches |
| dozzle | 上游源码 + 预构建 `dist` |
| ntfy | 上游源码 + `server/site`（前端 build） |
| gotify | 上游源码 + `ui/build` |
| prometheus | `prometheus`、`promtool`、`prometheus.yml`（UI 已 embed） |
| pihole | `pihole-FTL`、`web/`、`cli/`（pihole/gravity.sh/advanced）、`pihole-adlist.sh`、`gravity.db.sql`、`docker-entrypoint.sh` |
| gatus | `gatus` 二进制 + `config.yaml` |
| actual-budget | Node 24 构建阶段安装 `@actual-app/sync-server`；手动编 better-sqlite3；运行阶段复制 Node 运行时与包 |
| minio | 仅 `minio` 静态二进制 + entrypoint；Go 源码 `-tags kqueue` 编 |
| homebox | `homebox` 二进制（前端已 embed）+ entrypoint；前端 x86 WSL2 构建 |
| nocodb | Node 24 构建阶段 `npm install --ignore-scripts` + 手动 sqlite3；自定义 runner |
| apprise-api | 上游 `apprise_api/` + requirements/constraints；Python 3.11 + nginx/supervisor |
| mealie | Python 3.14 运行时 + 预构建 Nuxt 前端；`usrlocal/` 由构建容器导出；HEIF stub |
| alertmanager | `alertmanager`/`amtool` 二进制 + `alertmanager.yml`；UI 需 x86 WSL2 构建 `ui/app/dist` |
| postgres | 仅 Dockerfile + entrypoint（openEuler `postgresql-server` 包） |
| redis | 仅 Dockerfile + entrypoint + `redis.conf`（openEuler `redis` 包） |
| mosquitto | 仅 Dockerfile + entrypoint + `mosquitto.conf`（openEuler `mosquitto` 包） |
| mariadb | 仅 Dockerfile + entrypoint + `client.cnf`（openEuler `mariadb-server` 包） |
| node-red | 多阶段；构建阶段 `node:24.22.1-loong64` 安装 Node-RED 5.0.8，运行阶段复制 Node 运行时与包 |
| grafana | `grafana` 二进制 + 预构建 `public/` + `defaults.ini` + `grafana.ini`；前端需 x86 WSL2 |
| memcached | 仅 Dockerfile + entrypoint（openEuler `memcached` 包） |
| homebridge | 多阶段；Node 24 下 `homebridge@2.4.0` + `homebridge-config-ui-x@5.29.0`；源码编译 node-pty；运行阶段重建 bin 符号链接 |
| node | Node.js 24.22.1 linux-loong64 运行时基础镜像（unofficial-builds） |
| rest-server | `rest-server` 静态二进制 + entrypoint/create_user/delete_user；依赖 openEuler `httpd-tools` |
| caddy/watchtower/node-exporter | 仅二进制 + CA |
| chinesesubfinder | 上游源码 + 预构建 `frontend/dist/spa` + 二进制 |
| lanraragi | `perl5/`（cpanm local::lib）+ `app/`（上游源码与前端 vendor） |
| owntone | `owntone`、`libowntone/`、`share/`、`owntone.conf` 构建产物 |
| mymind | 已提交 `site/` 静态站点（32 文件） |
| webvirtcloud | `app/`（上游源码 + venv + collectstatic 产物） |
| penpot-backend | `app/`（官方 `bundle-backend` 解包） |
| penpot-frontend | `app/`（官方 `/var/www/app` 静态产物） |
| hermes | `python/`（3.14.8 前缀）、`app/`、`webui/`、`get-pip.py` |
| zigbee2mqtt | 上游源码 + pnpm 构建 `dist`；运行阶段需 `systemd-udev` |
| smartctl-exporter | 上游源码 + Go 静态二进制；运行阶段安装 smartmontools |
| sftpgo | 上游源码 + CGO SQLite 二进制 + templates/static/openapi + sftpgo.json |
| bookstack | 上游源码 + Composer vendor + nginx/php-fpm 配置 |
| vikunja | 上游源码 + 预构建 `frontend/dist` + Go CGO 二进制 |
| piwigo | 上游源码 + nginx/php-fpm 配置；无 vendor |
| go2rtc | 上游源码 + Go 静态二进制 + 默认 `go2rtc.yaml` |
| scrutiny | 上游源码 + `scrutiny-sqlite.patch` + Angular `dist` + smartmontools |
| headscale | 上游源码 + Go 静态二进制 + `config-example.yaml` |
| backrest | 上游源码 + 预构建 `webui/dist` + Go 二进制 + 自编 restic |
| authelia | 上游源码 + 预构建 `public_html` + `api/` 资产 + CGO 二进制 |
| ente-server | 上游 `server/` + museum 二进制 + configurations/migrations/templates |

具体工具链、CGO/glibc、Vite 8 x86 构建、qpdf/jq/Firefox/OpenCV 补丁见
[../docs/IMAGE-BUILD.md](../docs/IMAGE-BUILD.md)。

## 标签约定

所有镜像同时打 `loong64` 与 `24.10-la5`，推送脚本在私有库
`scripts/push-images.sh`，覆盖 99 只。
