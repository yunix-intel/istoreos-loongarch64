# 阻塞应用解锁研究索引

日期：2026-10-25。目标平台：LoongArch64 / 3A6000 / Loongnix 25，构建容器 openEuler 24.03。

| 应用 | 结论 | 报告 | 备注 |
|---|---|---|---|
| Karakeep | **有条件 Go（基础版）** | [karakeep-unblock.md](karakeep-unblock.md) | SQLite + 静态抓取可首发；搜索/截图需外部 Meilisearch/browserless；原生 Chromium/Meilisearch No-Go |
| wg-easy | **Go（已发布）** | [wg-easy-unblock.md](wg-easy-unblock.md) | v15.4.0 已发布双 tag；复用 libsql loong64 绑定 + hash-wasm；真实隧道待验收 |
| Joplin Server | **Go** | [joplin-unblock.md](joplin-unblock.md) | sharp/sqlite-vec 非服务端依赖；sqlite3 5.1.6 已过 16K 页门禁；PostgreSQL 路径仍建临时 SQLite |
| Komga | **Go（已发布）** | [komga-unblock.md](komga-unblock.md) | 官方 jar + 自编 loongarch64 `libsqlitejdbc.so`；已发布双 tag，最小 CBZ 扫描通过 |
| Linkwarden | **有条件 Go** | [linkwarden-unblock.md](linkwarden-unblock.md) | Prisma 7 WASM+adapter-pg；自写 99 个迁移；LBrowser/外部 browserless；sharp 可删；5–7 天 |

## 基础层

- `yunixintel/node-sharp` 已发布（libvips 8.18.7 + sharp 0.35.5），见
  [../BASE-IMAGES.md](../BASE-IMAGES.md)。
- LBrowser/Playwright 基础层已在龙芯验证（Playwright 1.57 含 PDF、Patchright 1.59
  四项通过、跨 NAT CDP 通过），但 deb 许可证不清晰，**不发布镜像**，应用改为宿主
  `/opt/apps/lbrowser:ro` 挂载。见 [../BASE-IMAGES.md](../BASE-IMAGES.md)。

## 2026-10-25 深度验证

| 报告 | 结果 |
|---|---|
| [verify-karakeep.md](verify-karakeep.md) | monolith/PDF-OCR/AI/多用户 PASS；Meili/OAuth/browserless WS BLOCKED；未配 Meili 搜索 500 |
| [verify-linkwarden.md](verify-linkwarden.md) | monolith/Meili 源码/AI/导入/归档/用户隔离 PASS；OAuth BLOCKED；邮箱模板已修复并复测 PASS |
| [verify-wg-easy.md](verify-wg-easy.md) | 隧道转发/NAT/外网 PASS；内部 IPv6 PASS，外网 IPv6 BLOCKED；AmneziaWG PoC PASS（未打包） |
| [verify-komga.md](verify-komga.md) | CBZ/PDF/EPUB/RAR4/只读/claim PASS；HEIF/JXL FAIL；Kobo KEPUB BLOCKED |
| [verify-casaos.md](verify-casaos.md) | 应用装/卸、36min soak、数据保留 PASS；3 个 BLOCKER FAIL；24h/重启未验；禁止发布 |
| [casaos-blocker-fix.md](casaos-blocker-fix.md) | 三个 BLOCKER 修复：白名单下沉、首管理员仅 loopback、message-bus HTTP；15min soak PASS；24h 待做 |
| [verify-lbrowser.md](verify-lbrowser.md) | WebGL/视频/非 root/20 标签/只读根 PASS；Widevine 不可用 |

## 结论使用规则

- “Go”表示有可执行的构建路径；“有条件 Go”表示需要外部服务或功能降级，商店卡片必须写清。
- 报告中的命令是研究阶段的验证记录，不等于已发布镜像；发布前仍需按
  `docs/APP-SYNC-CHECKLIST.md` 完成构建、测试、文档、推送。
- 任何需要宿主内核模块、`/lib/modules`、`NET_ADMIN`、真实磁盘/网络的操作，必须在
  测试机验收并记录，不得只写“理论上可用”。
