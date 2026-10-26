# Phase 2 执行交接单

日期：2026-10-26  
上位计划：[PHASE-2-FULL-VERIFICATION.md](PHASE-2-FULL-VERIFICATION.md)  
规范：[CASAOS-EXECUTION.md](specs/CASAOS-EXECUTION.md)、
[ISTORE-EXECUTION.md](specs/ISTORE-EXECUTION.md)、
[HARNESS-VERSION-EVIDENCE.md](specs/HARNESS-VERSION-EVIDENCE.md)、
[OMV-O01-O03.md](specs/OMV-O01-O03.md)

## 1. 当前状态（不要重复执行已完成项）

| 项 | 状态 | 证据 |
|---|---|---|
| C-03 24h soak | **PASS**，1440/1440，6 服务 PID 不变 | `reports/C03-SOAK.md` |
| A2 商店 115 | **PASS**，app-management 已重启 | `docs/research/verify-casaos-store.md` |
| C-04 Host A 重启自启 | **PASS**，7 unit active，115，Gatus 装/卸 200 | `reports/C04-REBOOT.md` |
| S-C5 数据保留首轮 | **PARTIAL**，actual-budget 通过；默认 DELETE 会删数据 | `reports/S-C5-DATA-RETENTION.md` |
| Loongnix ISO | **已保存**，`/mnt/Data/firmware/loongnix25-20260820.iso`，sha256 `6f607035…83b9` | 计划 §C0 |
| Docker Hub | **公开**，匿名 manifest 200；基础层 tag 见 `images/tag-policy.json` | `GAPS.md` |
| OMV O-01/O-02 | 完成：OMV 7 不可行；OMV 8 as-is 不可行（3 组硬阻塞） | `specs/OMV-O01-O03.md` |
| OMV O-03 | **BLOCKED**：缺 ≥16GiB scratch 与 loong64 OMV 依赖 | 同上 |
| B 机 sdb 干净安装 | **等 NAS 项目完成** | G1b |
| 115 应用全量矩阵 | 未开始 | 等待执行会话 |

**不要**在新会话里再次重启 Host A、再次写 58G U 盘、再次格式化任何盘；除非状态表/证据显示失败。

## 2. 新会话启动提示

### 2.1 `casaos-gate-exec`

```text
先读：
- docs/verification/PHASE-2-FULL-VERIFICATION.md
- docs/verification/specs/CASAOS-EXECUTION.md
- docs/verification/specs/HARNESS-VERSION-EVIDENCE.md
- docs/verification/EXECUTION-HANDOFF.md

当前状态：C-03、A2、C-04 Host A 已 PASS；S-C5 只有 actual-budget 首轮。
本会话从 S-C5 其余 5 类（joplin-server、bookstack、minio、wg-easy、gatus）
和平台矩阵 §6 开始，然后跑 115 应用矩阵 §7。不要重复重启 Host A。
SSH 必须用：ssh -o ClearAllForwardings=yes loongson-lab
证据/state 路径按规范；每批 commit。
```

### 2.2 `istore-la5-exec`

```text
先读：
- docs/verification/PHASE-2-FULL-VERIFICATION.md
- docs/verification/specs/ISTORE-EXECUTION.md
- docs/verification/specs/HARNESS-VERSION-EVIDENCE.md
- docs/verification/EXECUTION-HANDOFF.md

ISO 已保存到 /mnt/Data/firmware/loongnix25-20260820.iso（sha256 6f607035…83b9），
不要重复保存。58G U 盘 /dev/sdb 已授权整盘写 la5；写前确认 serial，
写后按规范恢复 Host A 内部启动。Docker Hub 公开，无需 token。
本会话只做 la5 公开版 + public feed；B 机 sdb 不要动。
```

### 2.3 `istore-p1-exec`

```text
先读同 la5，另看 store/private/README.md、store/istore/README.md。
ISO 已保存。p1 镜像 /build/firmware/personal-p1-20261019.img.gz。
先导出 local/linkwarden-private、local/karakeep-private 到 tar，
p1 启动后 docker load；private feed 默认 private；public feed 不得含 local/*。
B 机 sdb 不要动。
```

### 2.4 `casaos-clean-exec`

```text
等龙芯 NAS 项目完成、B 机 sdb 释放后再启动。
使用 B 机 172.16.100.66 /dev/sdb（sda 不动），Loongnix ISO 已保存在
Host A /mnt/Data/firmware/loongnix25-20260820.iso。
目标：CasaOS 0.1.3-store115 干净安装，AppManagement 直接返回 115。
不要碰 Host A 内部盘和 2TB 数据盘。
```

## 3. 执行会话必守

1. 只读本会话对应的规范，不跨阶段改 evidence。
2. 每个 PASS 必须写证据路径 + 哈希；dry-run/首页 200/未测不得 PASS。
3. `local/*` 只允许 E1/E3；E0/E2 出现即红线。
4. 默认 CasaOS DELETE 会删数据；卸载保留必须显式 `delete_config_folder=false`。
5. 磁盘 `/build`/`/var` <2GB、内存 `MemAvailable` <1GB 时暂停。
6. 失败项写 `failure_class` 与复现命令，不跨批无限重试。
7. 每批结束写报告、更新 `verify/state/<session>.yaml`、commit。

## 4. 新会话第一件事

```bash
git -C /c/Users/yunix/Documents/Codex/2026-10-01/zhe/outputs/istore-la-public status --short
git -C /c/Users/yunix/Documents/Codex/2026-10-01/zhe/outputs/istore-la-public log --oneline -5
```

确认工作区干净、最近提交为 Phase 2 规范/闸门结果；再按规范开跑。
