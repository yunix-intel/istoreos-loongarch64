# CasaOS 龙芯版说明（商店/详情页文案源）

状态：**内部验证版，未公开发布**。2026-10-25 三个 BLOCKER 已修复；仍待 24h soak 与真机重启自启。

## 卡片文案（zh-CN）

**CasaOS（LoongArch64 龙芯版）**

CasaOS 的龙芯移植版，基于上游 v0.4.15 的 7 个 Go 组件与 v0.4.25 UI，运行在
Loongnix/Debian 类 systemd 宿主上，提供应用商店、容器管理、磁盘挂载与文件入口。

龙芯版说明：
- 仅支持 `linux/loong64`；不能与 iStoreOS/OpenWrt 同机安装。
- 7 个后端组件为 LoongArch 静态 ELF；UI/AppStore 为架构无关静态资源。
- 针对龙芯修正了 `modernc.org/sqlite`、`gopsutil`、安装脚本架构识别、
  local-storage 辅助脚本与格式化后 UUID 残留等问题。
- 商店默认只展示已提供 `loong64` 镜像且有应用定义的应用，不展示上游 x86/ARM 镜像。
- 网关默认端口 8081；80 保留给宿主已有 Web 服务。

缺失/受限功能：
- 真实 SATA/USB 热插拔、SMART、格式化/写入、重启自挂仍在验收；USB 盘不进入
  local-storage 的磁盘白名单（仅 SATA/NVMe/SAS/SPI/virtio/mmc）。
- 前缀路径与 message-bus HTTP 事件链路已修复；危险 helper 已移出包。
- 首次管理员已限制为仅 loopback 注册（LAN 返回 403，含伪造 XFF/X-Real-IP）。
- 应用商店定义仍在补齐，当前不是全部 117 个镜像都已上架。

额外依赖/注意：
- 需要 systemd、udev、smartmontools、parted、ntfs-3g、mergerfs、udevil。
- C-01/C-01b/C-02 已过，三个 BLOCKER 已修复；C-03 24h 与真机重启、C-04 评审仍需完成。

## Card text (en-US)

**CasaOS (LoongArch64 edition)**

A LoongArch port of CasaOS based on upstream v0.4.15 Go services and the v0.4.25 UI,
running on a systemd-based Loongnix/Debian host.

LoongArch-specific notes:
- `linux/loong64` only; cannot coexist with iStoreOS/OpenWrt on the same machine.
- Backend services are static LoongArch ELF binaries; UI/AppStore assets are architecture-neutral.
- Patches cover sqlite/gopsutil LoongArch support, installer arch detection, local-storage helpers,
  and stale UUID records after formatting.
- The bundled store only lists apps with a verified `loong64` image and an app definition.
- Default gateway port is 8081; port 80 is reserved for an existing host web service.

Missing/limited:
- Real SATA/USB hotplug, SMART, format/write, and reboot remount are still under acceptance.
  USB disks are not accepted by local-storage (SATA/NVMe/SAS/SPI/virtio/mmc only).
- Prefix installs still have some paths not fully redirected.
- First-admin registration can be raced from LAN; this must be restricted before release.
- Store definitions are still being completed; not all 111 images are listed yet.

Dependencies: systemd, udev, smartmontools, parted, ntfs-3g, mergerfs, udevil.
Do not use in production before the release gates pass.
