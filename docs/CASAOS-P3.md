# CasaOS loong64 P3：构建、安装与运行

CasaOS 是 Debian/systemd 侧的应用面板，**不能与 iStoreOS/OpenWrt 同装**。
本页记录 P3 的组件版本、移植补丁、安装/运行方式和验证结论；源码/安装材料在私有库
`casaos-p3/`，发布包在盒子 `/build/archive/casaos-p3/`。

## 1. 组件版本

| 组件 | 版本 |
|---|---|
| casaos | v0.4.15 |
| gateway | v0.4.9-alpha4 |
| message-bus | v0.4.4-3-alpha2 |
| user-service | v0.4.8 |
| app-management | v0.4.10-alpha2 |
| local-storage | v0.4.4 |
| CLI | v0.4.4-3-alpha1 |
| UI | v0.4.25（linux-all） |
| AppStore | v0.4.5（linux-all） |

7 个 Go 组件均编为 LoongArch 静态 ELF（`CGO_ENABLED=0`），UI/AppStore 为架构无关静态资源。

## 2. 移植补丁（上游候选）

1. **modernc.org/sqlite → v1.30.0**：旧版 `modernc.org/libc v1.22` 缺 loong64 syscall/asm。
2. **gopsutil v3 → v4**：v3 host 包缺 loong64 utmp；v4 已支持。
3. **CASAOS_CONFIG_PATH 控制 gateway.ini 初建位置**：否则前缀安装会写宿主 `/etc`。
4. **get.casaos.io 安装脚本 arch 分支**：`loongarch64` 会被 `*64*` 误判为 amd64。
5. **local-storage `DeleteMountPointFromDB`**：格式化后旧 UUID 记录残留；建议按 mount_point 删除。
6. **P3 安装包补 `share/shell/local-storage-helper.sh`**：缺失时挂载/格式化报 `exit 127 do_mount`。

## 3. 安装包布局

```
casaos-p3-0.1.0/
  bin/         7 个 LoongArch ELF
  www/         CasaOS UI v0.4.25
  appstore/    loong64-only 商店 + 26 镜像覆盖
  conf/        gateway.ini / 各服务 conf
  share/shell/ 磁盘/USB 脚本（含 local-storage-helper.sh）
  scripts/     start.sh / stop.sh / healthcheck.sh
  systemd/     7 个 unit
  docs/        DEPENDENCIES.md / APPSTORE-LOONG64.md / UPSTREAM-PRS.md
  install.sh   uninstall.sh
```

当前包：`casaos-p3-loong64-0.1.0.tar.gz`，sha256 `6efcbb60…7bea`（旧包 `54fdd97a…b2b3` 作废）。

## 4. 安装与运行

```bash
tar -xzf casaos-p3-loong64-0.1.0.tar.gz
cd casaos-p3-0.1.0

# 前缀安装（不启用 systemd）
sudo ./install.sh --prefix /opt/casaos-p3 --store loong64
/opt/casaos-p3/scripts/start.sh
/opt/casaos-p3/scripts/healthcheck.sh

# systemd 安装
sudo ./install.sh --prefix /opt/casaos-p3 --store loong64 --system
sudo systemctl enable --now casaos.target
```

默认网关端口 8081（80 留给已有 Web 服务）；首次访问会要求初始化管理员。
卸载：`sudo ./uninstall.sh --prefix /opt/casaos-p3 [--system] [--purge]`，默认保留 `data/apps`。

## 5. local-storage / 磁盘

依赖：`udev smartmontools parted ntfs-3g mergerfs udevil`（Loongnix 源均有 loong64）。
`local-storage` 只接受 `sata/nvme/sas/spi/virtio/mmc` 传输层；loop/dm/nbd 会被过滤。

已验证（8G NBD 虚拟盘）：

- `POST /v1/storage` 挂载、写读、`DELETE /v1/storage` 卸载
- 重启 local-storage 后按 UUID 自动重挂
- `PUT /v1/storage` 格式化后重新挂载
- `image_ssim_diff` 与此无关；这里是 CasaOS 的挂载链路

2026-10-22 只读 USB 验证（未格式化、未写盘）：

- 设备：`/dev/sda`，58.2G Alcor Micro Multi Flash Reader，内含 `LOONGSONISO`（iso9660）。
- `udevil info /dev/sda1` 正确识别 removable/has media/size。
- `udevil mount /dev/sda1` 挂载到 `/media/root/LOONGSONISO`，`findmnt` 显示 `iso9660 ro`；
  `udevil umount /dev/sda1` 正常卸载。
- CasaOS local-storage 的 `o_disk` 没有新增该 USB 盘：其白名单只接受
  `sata/nvme/sas/spi/virtio/mmc`，`usb` 被过滤，符合当前实现。
- `smartctl` 通过 Alcor 读卡器桥接读取 SMART 失败（`Unknown USB bridge` / unsupported
  SCSI opcode），因此该读卡器无法验证 SMART。

未验证：真实 SATA/USB 盘的 SMART、格式化/写入、udevil 物理拔插、真机重启自挂。

## 6. 运行约束

- 不要装进 iStoreOS/OpenWrt；CasaOS 需要 systemd/Debian 用户态。
- 与 iStore 容器共存时，网关会占用 80–89 中最先空闲端口；同名容器/端口会冲突。
- 生产形态应装在 Debian/Loongnix 宿主；容器形态只用于测试/演示。
- 在真实盘验证通过前，CasaOS 镜像和安装包不发布。

## 7. 当前验证结论

- A 机 systemd 257：7 unit 安装、`systemd-analyze verify` 0 错误、6 服务 active、网关健康检查通过。
- `casaos-cli` 0.4.4 可运行；`uninstall.sh --system` 清理正确。
- 8G NBD 盘：挂载/卸载/服务重启自挂/格式化通过。
- 2026-10-22 真实 USB 只读：udevil 识别、ro 挂载、卸载通过；local-storage 不收录 usb，
  SMART 被读卡器桥接屏蔽。格式化/写入/物理拔插/真机重启仍未验证。

详见 [CASAOS-PLAN.md](CASAOS-PLAN.md)。

## 8. 2026-10-23 设计审查待修（发布闸门仍关闭）

独立审查发现以下问题，修复前不得发布：

1. **设备白名单只过滤列表**：`IsDiskSupported` 不拦 `POST/PUT /v1/storage`；
   必须把白名单下沉到 mutating handler 与 `local-storage-helper.sh`，并加
   `/dev/loop0` 负向测试。
2. **首次管理员可被局域网抢先注册**：首管理员存在前只允许 `127.0.0.1` 注册，
   安装脚本打印一次性 token 或要求 SSH 隧道。
3. **端口口径冲突**：CasaOS gateway 固定 8081；80 保留；MeTube 改 8082；
   Dashy 同机部署需改端口。不再使用静默 first-free。
4. **前缀安装路径未全覆盖**：除 `gateway.ini` 外，其余服务配置、runtime socket、
   helper 路径需逐项重定向；`/etc/systemd/system` 是明确例外。安装前后审计
   `/etc` `/usr` 新增路径。
5. **验收项与实现矛盾**：USB 盘不进入 local-storage，C-01 拆成 SATA 验收 +
   USB 只读验收；C-02 的前置补丁必须入包并记录 sha256。
6. **发布闸门过窄**：C-01、C-01b、C-02、C-03、C-04 全过才可发布；
   C-05/C-06 不阻塞。
7. **运维缺口**：systemd `Restart=`/hardening、平台备份/恢复、mergerfs 四场景、
   安装包/补丁 sha256 锚定，需补入验收。

完整设计与审查记录见 [APP-DESIGNS.md](APP-DESIGNS.md) 5.1 与 7.5。

## 9. 2026-10-24 新 SATA SSD 状态

- 设备：`/dev/sda`，Asgard AS2TS3-S7，2.04TB，SATA，SMART 健康（无待映射/离线不可修正扇区，
  温度 42°C，通电次数 6）。
- 分区：GPT，`sda1` 16MB Microsoft reserved，`sda2` 1.9TB NTFS，卷标“新加卷”。
- **不是空盘**：只读挂载 `sda2` 可见约 525GB 已用数据（`电厂规程文件`、`DCS`、
  `机械手_手套文档`、`秦山AI`、`.codex` 等）。未做任何写入/格式化。
- 因此 C-02（真实盘格式化/重建）不能直接在该盘执行；需要先确认数据已备份或有其他空盘。
  C-01（挂载/SMART/热插拔/重启）可先做只读部分，但写入类验收必须等确认。
- 新盘 SMART 已可用，之前“SSD 不识别”的阻塞已解除；当前阻塞变为“盘上有数据，需确认是否可清空”。
