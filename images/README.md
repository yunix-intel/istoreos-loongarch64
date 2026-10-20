# 应用镜像 Dockerfile 目录

本目录是 67 个 `yunixintel/*:loong64` 镜像的构建材料索引。

- `images/<app>/Dockerfile`：保留了 57 个镜像的 Dockerfile（部分带 `Dockerfile.*` 构建阶段）。
- `catalog.json`：67 个镜像的名称、大小、验证结论、端口/限制说明，机读索引。
- 未保留 Dockerfile 的 10 个镜像：adguardhome、code-server、easytier、firefly-iii、
  gitea、memos、mihomo、miniflux、phpmyadmin、vaultwarden。它们的源码版本与重建步骤
  见 [../docs/IMAGE-BUILD.md](../docs/IMAGE-BUILD.md)。
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
| alertmanager | `alertmanager`/`amtool` 二进制 + `alertmanager.yml`；UI 需 x86 WSL2 构建 `ui/app/dist` |
| postgres | 仅 Dockerfile + entrypoint（openEuler `postgresql-server` 包） |
| redis | 仅 Dockerfile + entrypoint + `redis.conf`（openEuler `redis` 包） |
| mosquitto | 仅 Dockerfile + entrypoint + `mosquitto.conf`（openEuler `mosquitto` 包） |
| mariadb | 仅 Dockerfile + entrypoint + `client.cnf`（openEuler `mariadb-server` 包） |
| caddy/watchtower/node-exporter | 仅二进制 + CA |

具体工具链、CGO/glibc、Vite 8 x86 构建、qpdf/jq/Firefox/OpenCV 补丁见
[../docs/IMAGE-BUILD.md](../docs/IMAGE-BUILD.md)。

## 标签约定

所有镜像同时打 `loong64` 与 `24.10-la5`，推送脚本在私有库
`scripts/push-images.sh`，覆盖 67 只。
