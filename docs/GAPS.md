# GAPS：计划与实际完成状态（2026-10-21）

口径：只读盘点。证据来自 docs、GitHub Releases/tags/API、Docker Hub API、本地产物。图例：✅完成　🟡部分/进行中　⬜未开始　❌撤下/判死　❓无法确认。

| 计划项 | 出处 | 状态 | 证据与说明 |
|---|---|---|---|
| la1–la5 连续发版，la5 内置 docker+podman | ROADMAP/NAMING | ✅ | 6 个 tag 全公开；la5 Release 10-19 发布，5 附件、316MB；最近的 CI 全绿（la2/la3 历史 Release 仅 2 附件） |
| 78 只应用镜像上 Docker Hub | ROADMAP | ✅ | Hub 78 仓库（含 freshrss、homer、paperless-ngx、dashy、watchtower、changedetection、caddy、dozzle、ntfy、gotify、node-exporter、prometheus、pihole、gatus、alertmanager、postgres、redis、mosquitto、mariadb、node-red、grafana、memcached、homebridge、rest-server、node、actual-budget、minio、homebox、nocodb、apprise-api）；逐个核验均含 `loong64`+`24.10-la5` 双 tag，均 loong64 单架构 |
| 文档与实物一致 | IMAGES/README/STORE-APP-LIST | ✅ | README/IMAGES 均为 78 只；CasaOS 已标注“磁盘验证前不发布”；GAPS 本次同步 |
| 镜像推送可复现 | 私有库 | ✅ | push-images.sh 已覆盖 78 只；本地 tag 名与 Hub 仓库名不一致时按脚本注释先 `docker tag` |
| CasaOS P1+P2 | CASAOS §7 | ✅ | 7 个 ELF、网关/UI、18 应用商店、memos 安装实测 |
| CasaOS P3 系统集成 | CASAOS §8/§10 | ✅ | 开发/系统集成完成：A 机 systemd 257 的 7 unit、6 服务、CLI 0.4.4、安装/卸载、NBD 磁盘链路、helper 打包修复均已验证；真实盘验收与上游 PR 待做，发布闸门仍关闭 |
| CasaOS local-storage 磁盘能力 | CASAOS §9/§10 | 🟡 | 8G NBD 盘验证：挂载、写读、卸载、服务重启按 UUID 自挂、格式化全过；真实 SATA/USB 盘的 SMART、udevil 拔插、真机重启待测；`IsDiskSupported` 白名单会过滤 loop/dm/nbd |
| CasaOS 对外发布 | NAMING/§9 | ❌ | Hub 无 casaos；GitHub `casaos-0.1.0` 返回 404（Actions 曾构建过） |
| CasaOS 与固件补丁上游化 | CASAOS §8/BUILD.md | ⬜ | UPSTREAM-PRS.md 自述“未 push 任何仓库”；无公开 PR |
| 私人 p1 命名 | NAMING | ✅ | `personal-p1-20261019.img.gz`（398.5MB，md5 a4d5…）与 FLASH-USB 一致；archive 命名合规；仅 ROADMAP/BUILDLOG 残留旧名 `v2-personal-full-la5` |
| 个人版 U 盘真机验证 | ROADMAP 进行中 | ⬜ | FLASH-USB 验证清单全未勾，无启动日志 |
| KVM | KVM-PLAN | ❌封存 | A 四组合全败；B（自编 qemu 9.2）同症状复现，按判据落 D；C 未投 |
| OpenMediaVault | ROADMAP 待排期 | ⬜ | 仅“建议只做可行性调研”，无代码/验证；compose/ZFS/KVM 插件同样未动（KVM 已封存） |
| jellyfin 缩略图 | ROADMAP/BUILDLOG | ✅ | ImageSharp 全接口 + 真照片库验证，镜像已替换 |
| navidrome DSD | IMAGES/BUILDLOG | ✅/❓ | 系统 taglib 2.0.2，DSD 已编译验证；真实媒体播放无记录 |
| podman bridge | BUILDLOG | 🟡 | 需宿主 nft_conntrack，Loongnix 6.6 缺；host/none 可用，未修也未写入 IMAGES 限制 |
| 其余镜像已知限制 | IMAGES/BUILDLOG | 🟡 | filebrowser 上游已归档、无安全修复；xteve/linkding 瘦身未做；openwebui 轻量；mihomo 在 LA 拒全部 mmdb，仅私人 RULE-SET 绕过 |

## 最该做的 5 件事

1. **U 盘真机验证 p1**：唯一未验收的固件交付，可一次覆盖首启、overlay、docker/podman、dockerman，风险最高而成本最低。
2. **CasaOS 真实盘收口**：NBD 已验证挂载/卸载/重启自挂/格式化；还需 SATA/USB 盘验 SMART、udevil 拔插与真机重启，之后才能解禁发布。
3. **补全 push-images.sh**：A 机凭据已从 Windows Docker Desktop 迁移，`homer`/`paperless-ngx` 已推送（Hub 共 51 仓库）；但脚本仍只覆盖 6 只，需扩到全量才能复现上架。
4. **提交 CasaOS 上游 PR**：4 个移植补丁 + 新发现的 `DeleteMountPointFromDB` 旧 UUID 残留问题；否则移植成果无法回流。
5. **收口 podman bridge 与 mmdb**：决定 NAS 场景容器网络是否可用；至少补内核模块或明确公开限制，避免用户误判。
