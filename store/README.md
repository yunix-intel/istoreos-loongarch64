# 商店文案与“龙芯版说明”源

本目录是 CasaOS / iStore 商店卡片的文案源，先于应用定义完成。

## 文件

| 文件 | 内容 |
|---|---|
| `platform/casaos-loong64.md` | CasaOS 平台级说明（中文 + 英文，含发布状态与限制） |
| `platform/istore-loong64.md` | iStoreOS 平台级说明（公版 la5 / 私人 p1） |
| `generate_descriptions.py` | 从 `images/catalog.json` 与差异表生成卡片文案 |
| `validate_descriptions.py` | 校验应用集合、架构标识和四个必填字段 |
| `loong64-descriptions.json` | 115 个可安装应用的机读文案（不含运行时基础镜像 `node`） |
| `exports/casaos-descriptions.json` | 可直接映射到 CasaOS `x-casaos` 的 title/category/tagline/description |
| `exports/istore-descriptions.json` | 可直接写入 iStore app-meta description 的 HTML（中/英） |
| `casaos/Apps/<id>/docker-compose.yml` | CasaOS 应用定义：115 个应用全部生成，已逐个通过 CasaOS dry-run |
| `casaos/apply_descriptions.py` | 将导出的 title/category/tagline/description 写回 CasaOS 定义 |
| `casaos/validate_definitions.py` | 本地结构校验：镜像/架构/披露/路径/端口冲突/port_map |
| `casaos/dryrun_all.sh` | 通过 SSH 调用目标 CasaOS 的 `POST /v2/app_management/compose?dry_run=true` 全量校验 |
| `casaos/apply_icons.py` + `icon-map.json` | 为 115 个应用写入可用的 selfh.st 图标（官方仓库目录为 PascalCase，旧 URL 会 404） |
| `casaos/fix_healthchecks.py` | 给 PostgreSQL/MariaDB/Redis/MinIO sidecar 补健康检查，避免 `service_healthy` 永久等待 |
| `casaos/port-plan.json` | 115 个应用的宿主端口分配；18 个已有定义保留 18001–18018，其余从 18101 起预留 |
| `casaos/build_port_plan.py` | 重新生成端口分配（多端口/固定端口应用需手工覆盖） |
| `private/` | 私人版/公开版浏览器接入：私人版 embedded sidecar，公开版宿主挂载；含 Linkwarden/Karakeep compose |
| `descriptions-preview.md` | 人工复核用的表格预览 |

## 必备字段

每张卡片必须同时包含：

1. **架构**：`linux/loong64`，仅龙芯 3A5000/3A6000，x86/ARM 无法运行。
2. **与上游差异**：行为、默认值、功能变化。
3. **缺失功能**：没有移植或未验证的功能。
4. **额外依赖**：数据库、设备、Docker socket、外部服务。
5. **镜像说明**：来自 `catalog.json` 的构建/版本/限制。

禁止只写应用名、“可安装”或“一键即用”。没有逐项回归的应用必须写明
“尚未逐项做行为回归，限制见镜像说明”，不能写成“无差异/无缺失”。

## CasaOS

- 将 `casaos_description.zh_cn` / `en_us` 写入 `x-casaos.description`。
- `tagline`、`title`、`category` 可直接使用 JSON 中的字段。
- 商店详情页必须渲染完整的 `disclosure` 区块；只显示 tagline 视为不合格。

## iStore

- 将 `istore_description_html.zh_cn` / `en_us` 写入应用详情的 description 字段。
- 若 app-meta 只接受纯文本，使用 `disclosure` 字段（保留换行）。
- 上架前运行 `python3 store/generate_descriptions.py`，确认 `app_count` 与
  `images/catalog.json` 的镜像数减 1（`node` 为基础镜像）一致。

## 发布前置条件

- 当前 `yunixintel/*` 在 Docker Hub 上是**私有仓库**。公开 CasaOS/iStore 商店上架前，
  必须把对应仓库改为公开，或给商店配置带凭据的镜像源；否则用户安装会卡在拉取镜像。
- 私人版只引用 `local/*` 或私有仓库，不得把 `local/*` 推送到公开 registry。
- 所有卡片必须显示“龙芯版说明”；没有逐项回归的应用不能写“一键即用”。

## 更新规则

- 新增镜像：必须同时更新 `images/catalog.json`、`docs/LOONG64-QUIRKS.md` 和本目录的
  `QUIRKS` 表，然后重新生成。
- 修改行为/默认值：先改 `docs/LOONG64-QUIRKS.md`，再改生成器，重新生成 JSON。
- 平台说明（CasaOS/iStore）是独立文件，发布闸门状态变化时手工更新。
- 本目录不存放真实凭据、节点地址或私人源。
