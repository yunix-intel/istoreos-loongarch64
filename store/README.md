# 商店文案与“龙芯版说明”源

本目录是 CasaOS / iStore 商店卡片的文案源，先于应用定义完成。

## 文件

| 文件 | 内容 |
|---|---|
| `platform/casaos-loong64.md` | CasaOS 平台级说明（中文 + 英文，含发布状态与限制） |
| `platform/istore-loong64.md` | iStoreOS 平台级说明（公版 la5 / 私人 p1） |
| `generate_descriptions.py` | 从 `images/catalog.json` 与差异表生成卡片文案 |
| `validate_descriptions.py` | 校验应用集合、架构标识和四个必填字段 |
| `loong64-descriptions.json` | 110 个可安装应用的机读文案（不含运行时基础镜像 `node`） |
| `exports/casaos-descriptions.json` | 可直接映射到 CasaOS `x-casaos` 的 title/category/tagline/description |
| `exports/istore-descriptions.json` | 可直接写入 iStore app-meta description 的 HTML（中/英） |
| `casaos/Apps/<id>/docker-compose.yml` | CasaOS 应用定义（当前 18 个已导入并注入说明，其余待生成） |
| `casaos/apply_descriptions.py` | 将导出的 title/category/tagline/description 写回 CasaOS 定义 |
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

## 更新规则

- 新增镜像：必须同时更新 `images/catalog.json`、`docs/LOONG64-QUIRKS.md` 和本目录的
  `QUIRKS` 表，然后重新生成。
- 修改行为/默认值：先改 `docs/LOONG64-QUIRKS.md`，再改生成器，重新生成 JSON。
- 平台说明（CasaOS/iStore）是独立文件，发布闸门状态变化时手工更新。
- 本目录不存放真实凭据、节点地址或私人源。
