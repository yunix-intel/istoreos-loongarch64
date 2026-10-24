# 阻塞应用解锁研究索引

日期：2026-10-25。目标平台：LoongArch64 / 3A6000 / Loongnix 25，构建容器 openEuler 24.03。

| 应用 | 结论 | 报告 | 备注 |
|---|---|---|---|
| Karakeep | **有条件 Go（基础版）** | [karakeep-unblock.md](karakeep-unblock.md) | SQLite + 静态抓取可首发；搜索/截图需外部 Meilisearch/browserless；原生 Chromium/Meilisearch No-Go |
| wg-easy | **Go（已发布）** | [wg-easy-unblock.md](wg-easy-unblock.md) | v15.4.0 已发布双 tag；复用 libsql loong64 绑定 + hash-wasm；真实隧道待验收 |
| Joplin Server | **Go** | [joplin-unblock.md](joplin-unblock.md) | sharp/sqlite-vec 非服务端依赖；sqlite3 5.1.6 已过 16K 页门禁；PostgreSQL 路径仍建临时 SQLite |
| Komga | **Go（已发布）** | [komga-unblock.md](komga-unblock.md) | 官方 jar + 自编 loongarch64 `libsqlitejdbc.so`；已发布双 tag，最小 CBZ 扫描通过 |
| Linkwarden | **有条件 Go** | [linkwarden-unblock.md](linkwarden-unblock.md) | Prisma 7 WASM+adapter-pg；自写 99 个迁移；LBrowser/外部 browserless；sharp 可删；5–7 天 |

## 结论使用规则

- “Go”表示有可执行的构建路径；“有条件 Go”表示需要外部服务或功能降级，商店卡片必须写清。
- 报告中的命令是研究阶段的验证记录，不等于已发布镜像；发布前仍需按
  `docs/APP-SYNC-CHECKLIST.md` 完成构建、测试、文档、推送。
- 任何需要宿主内核模块、`/lib/modules`、`NET_ADMIN`、真实磁盘/网络的操作，必须在
  测试机验收并记录，不得只写“理论上可用”。
