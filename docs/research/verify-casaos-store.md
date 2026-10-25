# CasaOS 商店定义验收（2026-10-25）

范围：`store/casaos/Apps/` 的 115 个应用定义，以及 CasaOS P3
（`/opt/casaos-p3`，AppManagement v0.4.10-alpha2）的 dry-run 与真实安装。

## 结果

| 检查 | 结果 | 证据 |
|---|---|---|
| 定义数量 | 115/115 | 18 个已有定义 + 97 个新生成；与 `port-plan.json`、`loong64-descriptions.json` 集合一致 |
| 本地结构校验 | 115/115 | `python store/casaos/validate_definitions.py`：`ok=115 errors=0` |
| CasaOS dry-run | 115/115 | `bash store/casaos/dryrun_all.sh`：`pass=115 fail=0`（CasaOS 自身 compose-go 解析） |
| 图标 | 115/115 有 URL | 官方 AppStore 目录为 PascalCase，旧 `Apps/<id>/icon.png` 全部 404；改用 `selfh.st/icons`，映射在 `icon-map.json` |
| 龙芯版说明 | 115/115 | 每张卡片含架构、与上游差异、缺失功能、额外依赖、镜像说明 |
| 过期披露修正 | 4 个应用 | wg-easy、Komga、Karakeep、Linkwarden 的“缺失功能”按最终复验回写并重新生成 |

## 真实安装抽样

每次均通过 CasaOS API 安装、检查容器/HTTP，再卸载；不是直接 `docker run`。

| 应用 | 类型 | 结果 |
|---|---|---|
| linkding | 简单单容器（已有定义） | 容器 Up，`http://127.0.0.1:18011/` 302（登录页） |
| actual-budget | 新定义、Node/SQLite | 容器 Up，`http://127.0.0.1:18101/` 200 |
| minio | 对象存储、双端口 | 容器 Up，控制台 18153 200，S3 health 18500 200 |
| bookstack | MariaDB sidecar | `bookstack-db` healthy，应用 `/login` 200 |
| joplin-server | PostgreSQL sidecar、多服务 | `joplin-postgres` healthy，`/api/ping` 200，容器 `healthy` |
| wg-easy | NET_ADMIN/SYS_MODULE、UDP | UI 51821 302，51820/udp 已监听 |
| gatus | 文件型配置改为 compose `configs.content` | 容器 Up，`http://127.0.0.1:18124/` 200 |

未逐台启动全部 115 个：部分应用需要外部 forge、真实 USB 设备、DNS 53 端口、
TLS 域名或首次 Web 向导，无法在无人值守脚本里判定成功；这些以 dry-run + 镜像自身
测试记录为准，并在卡片描述中写明依赖。

## 发现并修复的问题

1. **图标全 404**：CasaOS 官方仓库已改为 `Apps/ActualBudget/` 这种目录名，
   `Apps/actual-budget/icon.png` 不存在。改用 selfh.st 的 7786 个图标库并做规范化映射。
2. **sidecar 健康依赖不可满足**：14 处 `depends_on: service_healthy` 的目标没有
   `healthcheck`。已为 PostgreSQL/MariaDB/Redis/MinIO 补检查，Piwigo 的短格式
   `depends_on` 同步转换。
3. **Joplin bind mount 缺子目录**：`/data` 被宿主目录遮住后，镜像内的
   `logs/temp/resource/storage` 消失；entrypoint 现在每次启动用
   `install -d -o 1119 -g 1119` 重建。健康检查也会用 `APP_BASE_URL` 的 host:port
   作为 `Host` 头，否则固定 `127.0.0.1` 会被 Joplin 以 origin 不匹配拒绝（404）。
   修复镜像 digest：`sha256:59177faf22ef40fc7579a609cb855911ad09a375b4ab14d3dbe1d1b77adb4bff`。
4. **文案过期**：生成器中的 wg-easy/Komga/Karakeep/Linkwarden “缺失功能”停留在
   旧验证状态；已按 `docs/LOONG64-QUIRKS.md` 和最终复验结果更新，重新生成 115 份文案。
5. **7 个文件型 bind 会安装失败**：Caddy、Alertmanager、Gatus、Homer、Dashy、
   Mosquitto、Prometheus 把单个配置文件 bind 到宿主；CasaOS 会先建同名目录，
   容器把目录当文件读取而启动失败。已改为 compose 顶层 `configs.content` 内嵌默认
   配置（CasaOS dry-run 与真实安装均接受），Gatus 实测 200。自定义配置需修改
   compose 的 `configs.content`；卡片描述已注明。

## 复现命令

```bash
python store/casaos/validate_definitions.py
HOST=loongson-lab bash store/casaos/dryrun_all.sh
python store/casaos/apply_descriptions.py
python store/casaos/apply_icons.py
python store/casaos/fix_healthchecks.py
```

## 未完成

- S-C4 的“全新机器只点商店安装”：本轮是在已有 CasaOS P3 上验证，未重装系统。
- 115 个定义已同步到 Host A 的 `/opt/casaos-p3/appstore/default/Apps`（AppManagement
  实际读取路径）和 `appstore/loong64/Apps`（审计 overlay）；旧 18 个备份为
  `/opt/casaos-p3/appstore-default-backup-18-20261025.tar.gz` 与
  `appstore-Apps-backup-18-20261025.tar.gz`。但 AppManagement 的 `appStore.catalog`
  是进程内缓存，当前 API 仍返回 18。为避免打断进行中的 24h soak，重启
  `casaos-app-management` 安排在 soak 结束后；届时复验商店 UI 显示 115 个。
- S-C5 升级/卸载/数据保留：已观察到 CasaOS 卸载会删除 `Apps/<id>` 元数据，数据目录
  保留策略仍需单独用例。
- 115 个应用没有全部启动；设备类/外部依赖类应用的实机安装留给对应硬件环境。
