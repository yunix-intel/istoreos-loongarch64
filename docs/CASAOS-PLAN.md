# CasaOS 龙芯（loong64）移植评估

**结论：代码层可行，整体难度中低；真正的瓶颈是 loong64 应用镜像，不是 CasaOS 本身。** 建议做“应用面板”MVP（约 2–4 人日），不碰磁盘/网络接管；与 iStore 是不同 OS 层的互补，不能同机同装。

## 1. 组件盘点

官方分发以 `get.casaos.io` 脚本为主：按架构下载 GitHub Release 的 tar.gz，解包到 `/`，注册 systemd 服务；apt 源并非必经。稳定线为 CasaOS v0.4.15，脚本锁定：gateway v0.4.9-alpha4、message-bus v0.4.4-3-alpha2、user-service v0.4.8、local-storage v0.4.4、app-management v0.4.10-alpha2、CLI v0.4.4-3-alpha1、UI v0.4.25、AppStore v0.4.5；另有全线 v0.4.17-alpha1（已附 riscv64 包）。

| 组件 | 语言/形态 | 关键依赖 | loong64 |
|---|---|---|---|
| casaos（主服务） | Go，单二进制 | SQLite（纯 Go）、SMB 库、systemd notify | 易 |
| casaos-gateway | Go，反向代理+静态站 | 端口 80–89、8080–8089 自动选空闲；无其他系统依赖 | 易 |
| casaos-message-bus | Go，WebSocket 事件总线 | 纯 Go SQLite | 易 |
| casaos-user-service | Go | JWT、纯 Go SQLite | 易 |
| casaos-app-management | Go | Docker SDK、compose v2 **作为库**（非 CLI）、Docker API ≥1.24 | 中 |
| casaos-local-storage | Go | udev、FUSE、mergerfs、rclone、smartctl/parted/ntfs-3g | 中 |
| CasaOS-UI / AppStore | Vue 静态包 / YAML 清单 | 架构无关（`linux-all`） | 易 |
| Docker | 宿主服务 | 需 Docker ≥20；CasaOS 会写 `DOCKER_MIN_API_VERSION=1.24` | 已有 |

仓库内无闭源组件、无预编译二进制；rclone、mergerfs、smartmontools 等是外部开源发行版包。安装脚本还依赖 udevil、samba、cifs-utils、net-tools、unzip。

## 2. 移植难点

六个 Go 仓库源码均无 `import "C"`，优先用 `CGO_ENABLED=0 GOOS=linux GOARCH=loong64` 交叉编译（官方发行用 musl 静态链接；若个别传递依赖确实要 cgo，改为龙芯本机 gcc 直编即可）。唯一架构相关代码是 sonic 等库的 amd64/arm64 汇编优化，其他架构自动回退，不影响功能。

分级：**易**——gateway、message-bus、user-service、主服务、CLI、UI；**中**——app-management（依赖多、需真实 Docker 验证）、local-storage（FUSE/udev 与宿主包）；**难**——无（代码层）。

两个坑：
1. 安装脚本 `Check_Arch` 用 `*64*` 匹配，`loongarch64` 会被误判成 **amd64**，下载 x86 二进制。必须显式加 `loong64|loongarch64` 分支。
2. 脚本只列 amd64/arm64/armv7，并明确拒绝 OpenWrt；官方 README 也未列 loong64（riscv64 同样未列）。

## 3. 与 iStore 的关系

iStoreOS 是 OpenWrt（opkg/procd/LuCI），CasaOS 是 Debian 系（apt/systemd/Docker）。**同一系统不能同装**：脚本检测到 OpenWrt 直接退出，服务单元也依赖 systemd。若在 Loongnix/Debian 上与 iStore 的容器共存：CasaOS 网关会自动占用 80–89 中最先空闲的口（80 被 LuCI 占用则取 81），不硬冲突但会争 Web 入口；两者共用 Docker daemon，同名容器、宿主端口会碰撞；local-storage 的 udevil/devmon 自动挂载与 OpenWrt 热插拔也可能重复挂载。CasaOS 不接管宿主网络，这一点无冲突。

**判定：不是替代，是互补。** iStore 守网关/OpenWrt 层，CasaOS 做 Debian 侧的应用面板；12 个 loong64 镜像可直接复用。不要把两者塞进同一 OS。

## 4. 最小可行路线（只做应用面板）

1. **编译**：六个 Go 组件按 loong64 直编（关闭 CGO）；UI 用 `linux-all-casaos-v0.4.25`，AppStore 用 `linux-all-appstore-v0.4.5`，均免编。
2. **裁剪**：只装 gateway、message-bus、user-service、app-management、casaos 五服务；跳过 local-storage 及 rclone/mergerfs/udevil，文件与磁盘页不可用但应用页正常。网关端口设为 8081（80 留给 LuCI）。
3. **宿主**：确认 loong64 Docker ≥20 与 containerd 可用；仅在 API 报错时加 1.24 兼容覆盖。
4. **应用源**：注册自定义 loong64 store（或“自定义 Compose 安装”），只放 `yunixintel/*:loong64` 镜像；注意 arch 为空清单会被视为全架构，需剔除。
5. **验证**：五服务 `systemctl is-active`；`curl :8081/ping` 返回 pong；UI 可登录；装 memos 或 filebrowser 后容器 Up、页面 200；重启后自启；`file /usr/bin/casaos*` 全部为 LoongArch ELF。

## 5. 值不值得做

投入：代码适配 2–4 人日，集成验证 3–5 人日，之后是商店镜像的长期维护；产出是一个可复用、可上游化的 loong64 移植。收益主要在 UI 与应用生命周期管理，这部分 CasaOS 明显强于 iStore 的 Docker 页；但应用数量受限于 loong64 镜像，而这正是已有 12 个镜像的优势。建议**现在做限时 MVP**，不做磁盘/网络全功能；同时向上游提 loong64 的 goreleaser 与安装脚本 PR（riscv64 已铺路，接受度不低）。若目标只是“有个面板”，iStore dockerman 已够，可等生态更成熟；若目标是公开可用的龙芯应用面板与上游贡献，现在做性价比最高。

参考：<https://github.com/IceWhaleTech/CasaOS>、<https://github.com/IceWhaleTech/CasaOS-AppManagement>、<https://github.com/IceWhaleTech/CasaOS-LocalStorage>、<https://get.casaos.io>、<https://github.com/IceWhaleTech/CasaOS-AppStore>、<https://docs.casaos.io>

## 6. 完整功能目标（2026-10-19 追加）

用户要求 CasaOS 做**完整功能**，不停留在"应用面板 MVP"。完整版范围：

| 模块 | 组件 | 额外依赖 | 验证标准 |
|---|---|---|---|
| 应用商店/应用管理 | app-management + AppStore(v0.4.5) | Docker API | 能装/起/停我们 18 只 loong64 镜像中的任一 |
| 文件管理 | CasaOS 内置 Files | 无 | 能浏览 /DATA 并上传下载 |
| 磁盘管理 | local-storage v0.4.4 | udev、FUSE、mergerfs、rclone、smartctl、parted、ntfs-3g | 能识别 U 盘/硬盘、挂载/卸载、SMART |
| 用户/系统 | user-service + 主服务 | systemd（生产） | 登录、修改密码、系统信息 |
| 网关 | gateway | 端口 80/8081 | `/ping` pong，UI 200 |
| CLI | casaos-cli | 无 | `casaos-cli` 可执行 |

**完整版的现实约束**：
1. local-storage 的 udevil/devmon 自动挂载与宿主已有的热插拔会重复挂载——在专用龙芯 NAS 上没问题，在与 iStore 容器共存时需要关闭一方。
2. 生产形态应装进 Debian/Loongnix 宿主（systemd），而非容器；容器形态只用于测试与演示。
3. mergerfs/rclone/smartmontools/ntfs-3g 需逐个确认 loong64 可用（rclone 我们已自编；mergerfs 是 C，需编；ntfs-3g 看源）。
4. AppStore 清单里的镜像多为 x86/arm，需要维护一份"loong64 覆盖清单"（我们的 18 只优先），否则点了装不上。

**分期**：P1 网关+UI+五服务（当前）；P2 local-storage + CLI + 完整 AppStore；P3 系统集成（systemd 安装包/上游 PR）。

## 7. 实测结果（2026-10-19，P1+P2 完成）

- **编译**：7 个 LoongArch 静态 ELF 全部成功——gateway v0.4.9-alpha4、message-bus v0.4.4-3-alpha2、user-service v0.4.8、app-management v0.4.10-alpha2、local-storage v0.4.4、casaos v0.4.15、casaos-cli v0.4.4；UI v0.4.25 与 AppStore v0.4.5 的 linux-all 资产整合。
- **验证**（openEuler 24.03 loong64 容器、host 网络、挂 docker.sock、8081）：六服务 running；`/ping` → `pong from gateway service`；`/` → 200，UI 首页与 JS 正常；`/v1/users/status`、`/v1/sys/version`、`/v2/app_management/categories` 均 200。
- **P2**：自定义 AppStore 收录 18 个 `yunixintel/*:loong64` 应用；app-management 成功安装 memos（容器 healthy、18009 端口 200），验证后卸载。
- **移植坑（可上游）**：modernc libc/sqlite 与 gopsutil v3 不支持 loong64 → 升 sqlite v1.30.0、gopsutil v4；gateway 需 CASAOS_CONFIG_PATH 支持；app-management 缺 `/tmp/message-bus.sock`（非致命）；仓库需生成 codegen。
- **交付**：盒子 `/var/tmp/casaos-test/bundle` + `casaos-test-loong64.tar.gz`（82MB，sha256 `816e628c…b993`）+ REPORT.md。
- **P3 待办**：宿主 systemd 安装（local-storage 需要 lsblk/smartctl/mergerfs/udev）、UI setup wizard、设备映射（jellyfin 硬解/显卡）、上游 PR。

## 8. P3 完成（2026-10-19）

- **systemd**：7 个 unit（6 服务 + casaos.target），统一 /opt/casaos-p3，`systemd-analyze verify` 退出码 0；按 unit 手工起 6 服务验证（18081）：ping pong、UI 200、version/categories 200。宿主 /etc 未动。
- **安装包**：`casaos-p3-loong64-0.1.0.tar.gz`（82MB，sha256 `54fdd97a…b2b3`），install.sh 支持 `--prefix/--store loong64|full|none/--system`，uninstall.sh 保留 data/apps。
- **依赖**：udev/smartmontools/parted/ntfs-3g 源内有 loong64；mergerfs/udevil 源内有；rclone 用 Go 自编 v1.71.2；mergerfs 源码编译可行（g++/libfuse3-dev）。
- **AppStore**：26 个 `yunixintel/*:loong64` 已验证；`appstore-loong64-overrides.json`；默认商店仅显示可装（18 个有定义）。
- **上游 PR 清单**：sqlite v1.30、gopsutil v4、Gateway CASAOS_CONFIG_PATH、get 脚本 arch 分支。
- 产物：盒子 `/var/tmp/casaos-p3/`（tar.gz、DEPENDENCIES.md、APPSTORE-LOONG64.md、UPSTREAM-PRS.md、systemd-analyze-verify.txt）。

## 9. 生产级验证（2026-10-19，Loongnix 25 真机 172.16.100.66）

验证机：loongarch64 / Loongnix 25 / systemd 257 / 8 核 15G。共享机（另一会话占用 sdb），本次刻意不碰磁盘。

| 项 | 结果 |
|---|---|
| docker.io 安装与启动 | ✅ |
| 安装包 install.sh --prefix /opt/casaos-p3 | ✅ |
| 手工启动 5 服务（跳过 local-storage） | ✅ 8081 `/ping` pong、UI 200 |
| app-management 安装 memos（POST /v2/app_management/compose） | ✅ 容器 healthy、18009 200 |
| systemd units 安装 + `systemd-analyze verify` | ✅ |
| systemd 启动 5 服务 | ✅ 全 active running |
| gateway 重启恢复 | ✅ pong |
| enable/disable（casaos.target.wants 符号链接） | ✅ |
| local-storage / 磁盘自动挂载 | ⏸ 未测（共享机 sdb 归另一会话，避免冲突） |
| 清理 | ✅ 服务停、units 移除、memos 容器删除、8081 释放 |

**结论**：应用管理/UI/systemd 生命周期已达生产可用。**剩余唯一缺口是 local-storage 的磁盘能力验证**，需要一台独占磁盘（或专用 U 盘/数据盘）的机器；验证项：识别、挂载/卸载、SMART、重启后自动挂载。

**发布策略**：在磁盘项验证前不发布镜像与安装包；Docker Hub 上的 `yunixintel/casaos` tag 与 GitHub 预览 Release 均已撤回。

## 10. 独占验证机复测（2026-10-20，A 机 192.168.8.8）

> **P3 状态（2026-10-20）**：开发/系统集成完成——systemd 7 unit、CLI、安装/卸载、
> NBD 挂载/卸载/服务重启自挂/格式化、helper 打包修复均已验证。
> **未完成**：真实 SATA/USB 盘 SMART/udevil/真机重启验收、UI wizard 点击回归、
> 设备映射/GPU、上游 PR 提交。**发布闸门仍关闭**，CasaOS 镜像和安装包不发布。

A 机（3A6000，8 线程 / 15GiB，Loongnix 25）已成为唯一开发/验证机。原 `/restore` 空分区改为 `/build`，没有空闲物理盘，因此磁盘链路用 **8G 文件型 NBD 盘**（`qemu-nbd`）验证；它不是发布环境，但能覆盖 local-storage 的挂载/卸载/重启自挂/格式化代码路径。

| 项 | 结果 |
|---|---|
| P3 安装包 `install.sh --prefix /opt/casaos-p3` | ✅ |
| `--system` 安装 7 个 unit + `systemd-analyze verify` | ✅ 无错误 |
| `systemctl enable --now casaos.target` 后 6 服务 | ✅ 全部 active running，网关健康检查全过；验证后已停用并移除 units，保留前缀 |
| `scripts/start.sh` 起 6 服务 | ✅ 全部 running |
| `casaos-cli --help` / `version` | ✅ LoongArch 静态 ELF，version 0.4.4 |
| `uninstall.sh --system` | ✅ units 移除、程序文件删除、`data/apps` 保留 |
| 网关 8081 `/ping`、`/`、`/v1/sys/version`、`/v2/app_management/categories` | ✅ pong / 200 / 200 / 200 |
| 首次用户初始化（`/v1/users/status` → `register` → `login`） | ✅ 拿到 access_token |
| local-storage `/v1/disks` 列出系统 NVMe | ✅ |
| NBD 盘出现在 `/v1/disks` | ❌ 被 `IsDiskSupported` 传输层白名单过滤（只认 sata/nvme/sas/spi/virtio/mmc） |
| `POST /v1/storage` 挂载 `/dev/nbd0` 子分区 | ✅ `/mnt/testdisk_nbd0p1`，`o_disk` 落库 |
| 挂载点写入/读回数据 | ✅ |
| `DELETE /v1/storage` 卸载 | ✅ 卸载、目录删除、DB 记录删除 |
| 重启 local-storage 后按 UUID 自动重挂 | ✅ 日志 `previously persisted mount point` → `trying to re-mount`，数据仍在 |
| `PUT /v1/storage` 格式化 | ✅ UUID 变更、重新挂载、数据清空 |
| SMART | ⏸ NBD 不支持，需真实 SATA/USB 盘 |
| USB 自动挂载（udevil） | ⏸ 无 USB 设备 |
| 真机重启自挂 | ⏸ 需真实盘；本次以 local-storage 重启近似验证 |

### 发现的两个缺陷

1. **P3 安装包漏文件（已修）**：`share/shell/local-storage-helper.sh` 没进 bundle，挂载/格式化直接报
   `exit status 127: do_mount: 未找到命令`。已从上游
   `build/sysroot/usr/share/casaos/shell/local-storage-helper.sh` 补入 stage，并重打 tarball：
   `casaos-p3-loong64-0.1.0.tar.gz`，sha256 `6efcbb60…7bea`（旧包 `54fdd97a…b2b3` 作废）。
2. **格式化后 DB 残留旧 UUID（上游问题）**：`PUT /v1/storage` 会新增一条挂载记录，但
   `DeleteMountPointFromDB` 按 `UUID + mount_point` 过滤，只删当前 UUID，旧 UUID 行留在 `o_disk`。
   重启仍能按新 UUID 挂载，但记录会累积；建议上游改为按 mount_point 删除或 upsert。

### 仍需真实盘才能收口

- SATA/USB 盘的 `IsDiskSupported` 通过性（USB 的 `tran=usb` 是否被接受需实测）
- SMART 健康/温度
- udevil 自动挂载
- 真机重启后的自动挂载（不是仅服务重启）
- 设备映射/GPU：3A6000 无可用 GPU（`/v1/users/status` 返回 `gpus:0`），未验证
- UI setup wizard：本次用 API 完成初始化，未做浏览器点击回归

在此之前，CasaOS 镜像与安装包仍不发布。

### 真实盘验证清单（插上盘后照做）

```bash
# 1. 确认设备与传输层（USB 盘的 TRAN 通常是 usb）
lsblk -o NAME,SIZE,TYPE,TRAN,SERIAL,MOUNTPOINT
# 2. 起服务并登录拿 token（v1 要裸 token，不要 Bearer）
sudo /opt/casaos-p3/scripts/start.sh
KEY=$(curl -s http://127.0.0.1:8081/v1/users/status | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["key"])')
# 首次需注册：POST /v1/users/register {"username","password","key"}
TOK=$(curl -s -X POST http://127.0.0.1:8081/v1/users/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"casaos","password":"$CASAOS_TEST_PASSWORD"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["token"]["access_token"])')
# 3. 磁盘页应出现该盘；若 USB 盘不出现，记录 TRAN/SubSystems 作为上游缺陷证据
curl -s -H "Authorization: $TOK" http://127.0.0.1:8081/v1/disks
# 4. SMART（UI 的 health/temperature 也应变化）
sudo smartctl -a /dev/sdX
# 5. 格式化/挂载/写数据/卸载（用 UI 或 API）
# 6. 真机重启后检查自动挂载
sudo reboot
findmnt -S /dev/sdX1
sudo systemctl status casaos-local-storage --no-pager
# 7. USB 自动挂载：开启 USBAutoMount 后拔插，检查 udevil 与挂载点
```

判定：识别/格式化/挂载/卸载/重启自挂/SMART 六项全过才算磁盘能力生产可用；USB 盘额外加 udevil 拔插一项。
