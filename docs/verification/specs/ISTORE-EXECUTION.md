# iStoreOS 龙芯真机执行规范（ISTORE-EXECUTION）

版本：1.0  
日期：2026-10-26  
适用：`PHASE-2-FULL-VERIFICATION.md` 阶段 C / D（E2 la5 公开版、E3 p1 私人版）  
执行会话：`istore-la5-exec`、`istore-p1-exec`  
审查入口：本规范 + `PHASE-2-FULL-VERIFICATION.md`；两者冲突时以计划的环境矩阵、判定和红线为准。

---

## 0. 硬约束与执行边界

### 0.1 本规范做什么

- 在 Host A（`ssh loongson-lab`，3A6000 / LoongArch64）上用 58G `LOONGSONISO` U 盘（当前 `/dev/sdb`）真机启动 iStoreOS：
  - 阶段 C：`24.10-la5` 公开版 + `feed/public`；
  - 阶段 D：`personal-p1-20261019` 私人版 + `feed/private`。
- 先保存 U 盘上的 Loongnix 25 ISO，再整盘写 iStoreOS；测试结束恢复 Host A 内部 NVMe 启动。
- 产出平台矩阵、115 应用矩阵、public/private 隔离审计、证据、结果和最终 G2 结论。

### 0.2 本规范绝对不做

1. **不碰 B 机 `172.16.100.66` 的 `/dev/sdb`**。本规范所有 `sdb` 均指 Host A 的 58G U 盘；禁止 SSH 到 B 机执行任何 `dd`、`mkfs`、`mount`、`parted`、`wipefs`。
2. **不格式化 Host A 内部盘**：内部 NVMe 与 `/dev/sda`（2TB，`/mnt/Data`，约 525GB 用户数据）只读识别，不挂载写、不格式化、不做 SMART 写测试。
3. **不把 QEMU 冒充真机**。QEMU TCG 只能用于 feed/opkg 包结构 smoke，不能作为 E2/E3/G2 的 PASS 证据。
4. **不把“首页 200”写成“功能通过”**；未测项必须写 `NOT TESTED` 和原因。
5. **不把 `local/*`、私人镜像、真实凭据、私人节点地址写进 public feed 或 Git**。
6. **不在未确认设备身份时写盘**；任何 `dd` 前必须通过设备 guard。

### 0.3 判定口径

沿用计划第 3 节：

| 判定 | 含义 |
|---|---|
| PASS | 有命令/截图/日志证据，结果与预期一致 |
| PARTIAL | 主路径通过，但明确列出未覆盖功能或环境限制 |
| BLOCKED | 上游/硬件/依赖阻塞，附复现命令与根因 |
| NOT TESTED | 没跑；必须写原因，不能算通过 |

### 0.4 变量表（执行前先填）

| 变量 | 值 / 占位符 | 说明 |
|---|---|---|
| `HOSTA` | `loongson-lab` | Host A SSH alias |
| `USB` | `/dev/sdb` | **每次写盘前重新确认**，不得沿用上次 |
| `USB_SERIAL` | `<从 lsblk 抄录>` | 写盘 guard 必需；填进 state |
| `USB_MODEL` | `<从 lsblk 抄录>` | 辅助确认 |
| `PC_IP` | `192.168.100.2` | Windows 测试机静态 IP（隔离直连） |
| `ISTORE_IP` | `192.168.100.1` | 以串口/`uci get network.lan.ipaddr` 实测为准 |
| `LA5_DIR` | `/mnt/Data/firmware/la5` | la5 下载目录（Host A 内部盘） |
| `LA5_IMG` | `/mnt/Data/firmware/la5/istoreos-<...>-combined-efi.img.gz` | 从 Release 资产名补全 |
| `P1_IMG` | `/mnt/Data/firmware/personal-p1-20261019.img.gz` | p1 私人镜像的持久副本；原文件在 `/build/firmware/` |
| `FEED_ROOT` | `store/istore/feed` | HTTP 根目录 |
| `EVID` | `docs/verification/evidence` | 仓库证据目录 |
| `RESULT` | `docs/verification/results` | 机读结果目录 |
| `STATE` | `verify/state` | 会话 state 目录 |

> Windows 路径示例：仓库根 `C:\Users\yunix\Documents\Codex\2026-10-01\zhe\outputs\istore-la-public`；Git Bash 下用 `/c/Users/...` 或先 `cd` 到仓库根。

---

## 1. 拓扑与总顺序

### 1.1 推荐拓扑（隔离直连，避免和实验室 192.168.8.0/24 冲突）

```text
Windows 测试机（feed HTTP + 浏览器 + 串口）
  以太网直连，静态 192.168.100.2/24
        |
        |  网线直连（不接上游路由器）
        |
Host A，USB 启动 iStoreOS
  LAN 192.168.100.1/24（iStoreOS 常见默认；以实测为准）
  /dev/sdb = 58G U 盘（测试启动盘）
  内部 NVMe / /dev/sda = 不动
```

- 直连时 Windows 不要开 Internet 共享/ICS；iStoreOS 不要接 WAN 上游。
- 若 iStoreOS 实测 LAN 是 `192.168.1.1`，把 Windows 静态地址改为 `192.168.1.2/24`；不要同时保留 `192.168.100.2`。
- 如果必须接实验室网络，先记录原网段，避免 iStoreOS DHCP 与 `192.168.8.1` 冲突；LuCI/SSH 只从 LAN 侧访问。

### 1.2 总顺序

| 阶段 | 环境 | 动作 | 退出条件 |
|---|---|---|---|
| **C0** | Host A 内部 Loongnix | 保存 Loongnix ISO、下载/校验 la5、准备 la5 预载 tar | ISO 可只读挂载；la5 SHA 正确；U 盘可写 |
| **C1** | Host A U 盘 | 写 la5、启动、基线采集 | SSH/LuCI 可达；固件版本记录 |
| **C2** | la5 iStoreOS | feed 部署、平台矩阵 | 平台矩阵完成；115 卡片可见 |
| **C3** | la5 iStoreOS | 115 应用矩阵、重启/升级/卸载 | 每应用有结果；失败分级 |
| **C4** | Host A | 关机拔 U 盘，内部 NVMe 启动 | CasaOS/`/mnt/Data` 无损 |
| **D0** | Host A 内部 Loongnix | 校验 p1、保存 private/local 镜像与 LBrowser 宿主目录 | p1 SHA/md5 正确；tar 可 load |
| **D1** | Host A U 盘 | 写 p1、启动、基线采集 | p1 SSH/LuCI 可达；私人预置已隔离 |
| **D2** | p1 iStoreOS | private feed、平台矩阵 | 115 卡片可见；private 默认变体正确 |
| **D3** | p1 iStoreOS | 115 应用矩阵、隔离审计 | 无 public 泄漏；每应用有结果 |
| **D4** | Host A | 关机拔 U 盘，内部 NVMe 启动 | CasaOS/`/mnt/Data` 无损 |

---

## 2. Step 0：保存 Loongnix ISO（只读，不写 U 盘）— 2026-10-26 已完成

目的：58G U 盘当前 `/dev/sdb1` 是 5.856GB 的 `LOONGSONISO`（iso9660，kernel `6.6.52-loong64`）。写 iStoreOS 会清空 U 盘，所以先把 **sdb1** 保存到 Host A 的 `/mnt/Data/firmware/`。

**已完成**：`/mnt/Data/firmware/loongnix25-20260820.iso`，5.5GB，sha256
`6f607035a8ea2c165eee52444fb465bf80015772084c4df58d87974666f483b9`；只读挂载确认
`live/filesystem.squashfs` 存在。执行会话只需复核哈希，不要重复 dd。

### 2.1 前置确认

```bash
ssh loongson-lab

# 记录磁盘拓扑和内部盘身份（证据）
mkdir -p ~/istore-exec-evidence
lsblk -o NAME,SIZE,SERIAL,MODEL,TRAN,FSTYPE,LABEL,MOUNTPOINTS \
  | tee ~/istore-exec-evidence/hosta-disks-before.txt

# 确认 /mnt/Data 空间（1.9T 空闲）
df -h /mnt/Data

# 确认 sdb1 是 ISO9660 且标签为 LOONGSONISO
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS /dev/sdb
sudo blkid /dev/sdb1
```

预期：

- `/dev/sdb` 约 58G，`TRAN=usb`；
- `/dev/sdb1` 约 5.856GB，`TYPE="iso9660"`，`LABEL="LOONGSONISO"`；
- `/mnt/Data` 可用空间远大于 10GB。

**若 sdb1 不是 iso9660/LOONGSONISO，或 sdb 不是 USB，停止，不要继续。**

### 2.2 只保存 sdb1，不保存整个 58G

```bash
sudo mkdir -p /mnt/Data/firmware
sudo dd if=/dev/sdb1 of=/mnt/Data/firmware/loongnix25-20260820.iso \
  bs=4M status=progress conv=fsync
sync
```

为什么只保存 `sdb1`：

- `/dev/sdb` 是 58G 整盘，包含分区表和大量未使用空间；整盘 `dd` 会生成约 58G 文件，且夹带无关分区表。
- ISO 文件系统在 `/dev/sdb1` 这个 5.856GB 分区内；保存 sdb1 即可得到可挂载/可回写的 ISO9660 镜像。
- 是否完整，不靠“文件大小像”，靠下面的只读挂载检查 `live/filesystem.squashfs`。

### 2.3 校验（源分区 vs 保存文件）

```bash
# 源分区哈希（只读）
SRC_SHA=$(sudo dd if=/dev/sdb1 bs=4M status=none | sha256sum | awk '{print $1}')
DST_SHA=$(sha256sum /mnt/Data/firmware/loongnix25-20260820.iso | awk '{print $1}')
printf 'sdb1=%s\niso =%s\n' "$SRC_SHA" "$DST_SHA" | tee /tmp/iso-hash.txt

# 两者应完全一致（只比较哈希字段，避免文件名差异）
[ "$SRC_SHA" = "$DST_SHA" ] && echo ISO_HASH_MATCH || echo ISO_HASH_MISMATCH
```

预期：`ISO_HASH_MATCH`。若不一致，重新保存；不要进入写盘步骤。

### 2.4 只读挂载确认

```bash
sudo mkdir -p /mnt/loongnix-iso
sudo mount -o loop,ro /mnt/Data/firmware/loongnix25-20260820.iso /mnt/loongnix-iso

test -f /mnt/loongnix-iso/live/filesystem.squashfs \
  && echo ISO_SQUASHFS_OK || echo ISO_SQUASHFS_MISSING

ls -lh /mnt/loongnix-iso/live/filesystem.squashfs
sudo umount /mnt/loongnix-iso
```

预期：`ISO_SQUASHFS_OK`，squashfs 文件存在且大小合理。若 `mount -o loop` 不可用，用 `isoinfo -f -i ...` 或 `7z l ...` 列出 `live/filesystem.squashfs`，但必须记录替代命令和输出。

### 2.5 证据

```bash
cp /tmp/iso-hash.txt ~/istore-exec-evidence/
sudo blkid /dev/sdb1 > ~/istore-exec-evidence/sdb1-blkid.txt
ls -lh /mnt/Data/firmware/loongnix25-20260820.iso \
  > ~/istore-exec-evidence/loongnix-iso-ls.txt
```

**回退**：Step 0 只读，不改变 U 盘；若保存失败，删除不完整文件后重试。不要为了“省空间”去写 sdb。

---

## 3. Step 1：la5 / p1 镜像获取与校验

### 3.1 la5 公开版（GitHub Release `24.10-la5`）

仓库：`https://github.com/yunix-intel/istoreos-loongarch64`  
资产：`*combined-efi.img.gz`、`sha256sums`、`version.buildinfo`（以及 rootfs/opkg-feed）。

```bash
ssh loongson-lab
LA5_DIR=/mnt/Data/firmware/la5
mkdir -p "$LA5_DIR"
cd "$LA5_DIR"

# 先看资产名（不下载）
gh release view 24.10-la5 \
  --repo yunix-intel/istoreos-loongarch64 \
  --json assets --jq '.assets[].name'

# 下载 img.gz + sha256sums（必需）
gh release download 24.10-la5 \
  --repo yunix-intel/istoreos-loongarch64 \
  --dir "$LA5_DIR" \
  --pattern '*combined-efi.img.gz' \
  --pattern 'sha256sums*'

# version.buildinfo 可能不在当前 Release 资产里；失败不阻塞，但必须记录
gh release download 24.10-la5 \
  --repo yunix-intel/istoreos-loongarch64 \
  --dir "$LA5_DIR" \
  --pattern 'version.buildinfo' || echo "NO_VERSION_BUILDINFO_ASSET"
```

没有 `gh` 时的等价做法：

```bash
curl -fsSL \
  https://api.github.com/repos/yunix-intel/istoreos-loongarch64/releases/tags/24.10-la5 \
  | python3 -c 'import sys,json; [print(a["browser_download_url"]) for a in json.load(sys.stdin)["assets"]]'
# 然后 curl -L -O <上面列出的 img.gz / sha256sums / version.buildinfo URL>
```

校验：

```bash
cd "$LA5_DIR"
SUMS=$(ls sha256sums* | head -1)
sha256sum -c "$SUMS" --ignore-missing

# gzip 完整性
gzip -t ./*combined-efi.img.gz && echo GZIP_OK

# 记录实际文件、SHA256、大小
LA5_IMG=$(ls -1 ./*combined-efi.img.gz | head -1)
sha256sum "$LA5_IMG" | tee la5-img.sha256
ls -lh "$LA5_IMG" | tee la5-img.ls
[ -f version.buildinfo ] && cat version.buildinfo | tee version.buildinfo.txt \
  || echo "version.buildinfo not present in Release assets" | tee version.buildinfo.txt
```

预期：

- `sha256sum -c` 输出 `OK`；
- `GZIP_OK`；
- la5 `img.gz` 基线约 316MB（以 `ls -lh` 实测为准）；
- `version.buildinfo` 含 `24.10-la5` / `24.10.8` / `r0-fb97140` 之一组标识（以实际内容为准，记录原文）。

**若 SHA 不匹配**：停止；不要写盘；重新下载并核对 `sha256sums` 是否在所有附件定稿后生成（历史上有过 sums 未同步的乌龙）。

### 3.2 p1 私人版（Host A `/build`）

```bash
ssh loongson-lab
ls -lh /build/firmware/personal-p1-20261019.img.gz
sha256sum /build/firmware/personal-p1-20261019.img.gz | tee /tmp/p1.sha256
md5sum    /build/firmware/personal-p1-20261019.img.gz | tee /tmp/p1.md5
gzip -t   /build/firmware/personal-p1-20261019.img.gz && echo P1_GZIP_OK
```

基线记录（BUILDLOG/GAPS）：

- 文件名 `personal-p1-20261019.img.gz`；
- 大小 **398,554,090 字节**（约 398.5MB 十进制 / 381MiB；`ls -lh` 显示 381M 是 MiB，不是矛盾）；
- md5 基线 **`a4d58f827fcb882bb46b9012d185c91e`**。

预期：`P1_GZIP_OK`；md5 与基线一致。若不一致：

1. 先确认 `/build/firmware/` 下是否有同名但被替换的文件；
2. 查 `archive/personal-pre-p1-*.img.gz`；
3. 找不到正确文件就标 `BLOCKED`，**不要拿别的镜像顶替 p1**。

保存一份到持久目录并再次校验：

```bash
sudo mkdir -p /mnt/Data/firmware
sudo cp /build/firmware/personal-p1-20261019.img.gz /mnt/Data/firmware/
sha256sum /mnt/Data/firmware/personal-p1-20261019.img.gz
```

### 3.3 本地 feed 静态校验（写盘前）

在 Windows 仓库根或 Host A 的仓库副本执行：

```bash
cd store/istore
python3 -I validate.py     # Windows 用 python -I validate.py

grep -c '^Package: ' feed/public/all/meta/Packages        # 115
grep -c '^Package: ' feed/public/all/nas_luci/Packages    # 1
grep -c '^Package: ' feed/private/all/meta/Packages       # 115
grep -c '^Package: ' feed/private/all/nas_luci/Packages   # 1

sha256sum feed/public/all/meta/Packages feed/private/all/meta/Packages
```

预期：`validation OK`；计数 115/1/115/1。若 `validate.py` 失败，先修 feed，不要带病上机。

### 3.4 基础层 tag 例外（必须按实际 tag，不要统一改成 24.10-la5）

| 镜像 | 可用 tag | 说明 |
|---|---|---|
| `yunixintel/node` | `24.10-la5`、`24.22.1`、`loong64` | 运行时 24.22.1 |
| `yunixintel/node-sharp` | `loong64`、`24.22.1` | **没有** `24.10-la5` |
| `yunixintel/lbrowser-runtime` | `loong64`、`3.4.2293.2` | **没有** `24.10-la5`；运行镜像公开可自动拉取，但宿主 `/opt/apps/lbrowser` 仍需预置浏览器字节 |

匿名校验 Docker Hub（无需 token）：

```bash
for u in \
  https://hub.docker.com/v2/repositories/yunixintel/joplin-server/tags/24.10-la5 \
  https://hub.docker.com/v2/repositories/yunixintel/lbrowser-runtime/tags/3.4.2293.2 \
  https://hub.docker.com/v2/repositories/yunixintel/node-sharp/tags/24.22.1 \
  https://hub.docker.com/v2/repositories/yunixintel/node/tags/24.10-la5
do
  printf '%s -> ' "$u"
  curl -fsS -o /dev/null -w '%{http_code}\n' "$u" || echo FAIL
done

# 预期 404 的负向检查（证明没有 24.10-la5 tag）
curl -s -o /dev/null -w '%{http_code}\n' \
  https://hub.docker.com/v2/repositories/yunixintel/lbrowser-runtime/tags/24.10-la5
curl -s -o /dev/null -w '%{http_code}\n' \
  https://hub.docker.com/v2/repositories/yunixintel/node-sharp/tags/24.10-la5
```

预期：前四个 200；后两个 404。Docker Hub 匿名可拉取，**不需要 token**；不要把任何 token 写进仓库或 feed。

---

## 4. Step 2：58G U 盘写盘（la5 / p1 各一次）

> 这是本规范唯一的“清空介质”步骤。写盘前必须完成 Step 0 的 ISO 保存与挂载验证。

### 4.1 前置确认（强制 guard）

在 Host A 内部系统执行：

```bash
ssh loongson-lab

# 1) 记录当前所有盘
lsblk -o NAME,SIZE,SERIAL,MODEL,TRAN,FSTYPE,LABEL,MOUNTPOINTS \
  | tee ~/istore-exec-evidence/disks-before-write.txt

# 2) 指定目标（每次重新确认，不要用上一次的变量）
USB=/dev/sdb
lsblk -o NAME,SIZE,SERIAL,MODEL
lsblk -dn -o NAME,SIZE,TYPE,TRAN,MODEL,SERIAL "$USB"
udevadm info --query=property --name="$USB" | grep -E 'ID_BUS|ID_MODEL|ID_SERIAL'

# 3) 记录 serial 到 state（人工抄录，写盘脚本会比对）
read -r USB_SERIAL < <(lsblk -dn -o SERIAL "$USB" | tr -d ' ')
USB_MODEL=$(lsblk -dn -o MODEL "$USB" | tr -d ' ')
echo "USB=$USB USB_SERIAL=$USB_SERIAL USB_MODEL=$USB_MODEL"
```

**必须同时满足**：

- `/dev/sdb` 的 `TRAN` 是 `usb`；
- 容量在 50GB–70GB 之间（58G 级别）；
- serial/model 与上次记录一致；
- 没有分区被挂载（`findmnt /dev/sdb*` 无输出）；
- `/mnt/Data/firmware/loongnix25-20260820.iso` 已通过 2.3/2.4；
- 目标镜像 SHA 已通过第 3 节。

写盘 guard（可复制执行）：

```bash
set -eu
USB=${USB:-/dev/sdb}
case "$USB" in
  /dev/sda|/dev/nvme*|/dev/mmcblk*) echo "ABORT: internal/blocked device $USB"; exit 1;;
esac
[ "$(lsblk -dn -o TYPE "$USB" | tr -d ' ')" = "disk" ] || { echo "ABORT: not a whole disk"; exit 1; }
[ "$(lsblk -dn -o TRAN "$USB" | tr -d ' ')" = "usb" ] || { echo "ABORT: not USB"; exit 1; }
SIZE_BYTES=$(sudo blockdev --getsize64 "$USB")
[ "$SIZE_BYTES" -ge 50000000000 ] && [ "$SIZE_BYTES" -le 70000000000 ] \
  || { echo "ABORT: size $SIZE_BYTES not 58G class"; exit 1; }
[ -z "${USB_SERIAL:-}" ] || [ "$(lsblk -dn -o SERIAL "$USB" | tr -d ' ')" = "$USB_SERIAL" ] \
  || { echo "ABORT: serial mismatch"; exit 1; }
# 整盘或其分区有挂载点就拒绝
lsblk -no MOUNTPOINT "$USB" 2>/dev/null | grep -q . && { echo "ABORT: mounted"; exit 1; } || true
findmnt -rn -S "$USB" -o TARGET 2>/dev/null | grep -q . && { echo "ABORT: mounted"; exit 1; } || true
echo "GUARD_OK $USB $SIZE_BYTES"
```

**若 guard 失败，停止。** 不要 `sudo dd`；先查 `/dev/disk/by-id/` 和 `lsblk` 重新定位 U 盘。

### 4.2 写盘

> 写盘只在 Host A **内部 Loongnix** 执行。一旦从 U 盘启动 iStoreOS，`/dev/sdb` 就是运行中的启动盘，禁止再对它执行 `dd`/`mkfs`/分区操作。

```bash
# la5 阶段
LA5_DIR=/mnt/Data/firmware/la5
IMG=${IMG:-$(ls -1 "$LA5_DIR"/*combined-efi.img.gz | head -1)}

# p1 阶段改成：
# IMG=/mnt/Data/firmware/personal-p1-20261019.img.gz

file -b "$IMG"
gzip -t "$IMG"

# 卸载可能自动挂载的 U 盘分区
sudo umount ${USB}?* 2>/dev/null || true
sudo swapoff ${USB}?* 2>/dev/null || true

# 按文件类型写：gzip 先解压，raw 直接 dd
case "$(file -b "$IMG")" in
  *gzip*)
    gzip -dc "$IMG" | sudo dd of="$USB" bs=4M status=progress conv=fsync
    ;;
  *)
    sudo dd if="$IMG" of="$USB" bs=4M status=progress conv=fsync
    ;;
esac
sync
sudo blockdev --flushbufs "$USB" 2>/dev/null || true
```

预期：`dd` 正常结束、无 `No space left`/`Input/output error`；`sync` 返回 0。

### 4.3 写后校验（必须做）

```bash
if file -b "$IMG" | grep -q gzip; then
  SRC_SHA=$(gzip -dc "$IMG" | sha256sum | awk '{print $1}')
  SIZE=$(gzip -dc "$IMG" | wc -c)
else
  SRC_SHA=$(sha256sum "$IMG" | awk '{print $1}')
  SIZE=$(stat -c%s "$IMG")
fi

DST_SHA=$(sudo head -c "$SIZE" "$USB" | sha256sum | awk '{print $1}')
echo "size=$SIZE"
echo "src=$SRC_SHA"
echo "dst=$DST_SHA"
[ "$SRC_SHA" = "$DST_SHA" ] && echo WRITE_VERIFY_OK || echo WRITE_VERIFY_FAIL
```

预期：`WRITE_VERIFY_OK`。若 FAIL：不要启动；重新写盘；连续两次失败换 U 盘/换口。

分区与文件系统确认：

```bash
sudo partx -u "$USB" 2>/dev/null || sudo blockdev --rereadpt "$USB" 2>/dev/null || true
sudo partx -s "$USB" || true
lsblk -f "$USB" | tee ~/istore-exec-evidence/usb-after-write.txt
sudo blkid ${USB}* 2>/dev/null | tee -a ~/istore-exec-evidence/usb-after-write.txt
```

预期：能看到 EFI 分区和 rootfs 分区（具体分区号以镜像布局为准）；`lsblk -f` 的 FSTYPE 与镜像一致。

记录到 state：

```yaml
usb:
  device: /dev/sdb
  serial: "<USB_SERIAL>"
  size_bytes: <SIZE_BYTES>
  image: "<IMG>"
  image_sha256: "<SRC_SHA>"
  write_verify: OK
```

### 4.4 启动 U 盘

1. `sync`，`sudo poweroff`；**完全断电后再拔/插 U 盘**，不要热拔。
2. 开机按主板 POST 画面提示的 Boot Menu 键（常见 F11/F7/F12，以屏幕提示为准），选 USB 的 UEFI 项。
3. 若没有显示输出，用串口或 iKVM；不要盲改 BIOS。
4. 首次启动记录：
   - 串口日志（115200 8N1）保存为 `evidence/<env>/boot/serial.log`；
   - 屏幕/iKVM 启动菜单和 LuCI 首页截图；
   - `dmesg` 中存储/USB/网络错误。

### 4.5 恢复 Host A 内部启动（每次测试结束都做）

```bash
# 在 iStoreOS 内
sync
poweroff
# 断电，拔掉 58G U 盘
# 开机，Boot Menu 选内部 NVMe（Loongnix）
```

内部系统起来后：

```bash
ssh loongson-lab
uptime
findmnt /
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
df -h /mnt/Data
systemctl is-active casaos.target
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/ping
```

预期：

- 根文件系统是内部 NVMe，不是 U 盘；
- `/mnt/Data` 已挂载，UUID `678b4321-d7aa-46a1-b53a-e80013fe6ad9`（以实测为准）；
- `casaos.target` active；gateway `/ping` 200；
- CasaOS 数据与 soak 文件仍在。

若内部启动失败：

- 进 BIOS 把内部 NVMe 调到第一启动项；
- 用内部系统/救援盘检查 `efibootmgr -v`，确认没有把 iStoreOS 条目设成唯一启动项；
- 不要重装 Host A；不要格式化任何内部盘。

### 4.6 写盘风险与回退

| 风险 | 预防 | 回退 |
|---|---|---|
| 写错盘（内部盘） | guard 检查 `TRAN=usb`、容量、serial、挂载；禁止 `/dev/sda`、`/dev/nvme*` | 立即停止，不再写；保留现场；内部盘从备份/快照恢复；P0 事故 |
| 写盘中断电 | 写前确认电源；`conv=fsync`；写后校验 | U 盘重刷；内部盘不受影响 |
| U 盘坏块 | 写后 `head -c` 哈希；连续失败换盘 | 换 U 盘；保留原 ISO |
| 启动失败 | 串口/iKVM；写后校验；换 USB 口 | 重刷；内部启动；不改 BIOS 其他项 |
| 误拔 U 盘 | 写盘/启动中不拔；结束后 `poweroff` | 重刷；检查 `dmesg` I/O error |

---

## 5. Step 3：la5 / p1 启动后的网络、IP、SSH、串口、LuCI 与版本基线

### 5.1 串口/显示

- 串口参数：`115200 8N1`，无流控。
- Linux 控制机：

```bash
sudo picocom -b 115200 /dev/ttyUSB0
# 或
sudo screen -L -Logfile evidence/serial.log /dev/ttyUSB0 115200
```

- Windows：PuTTY，COMx，115200 8N1，开启 Session Logging 到 `evidence/<env>/boot/serial.log`。
- 设备端控制台可能是 `ttyS0`；不需要在设备内改串口配置。

### 5.2 发现 IP 并设置测试机

优先从串口/显示器执行：

```bash
uci get network.lan.ipaddr
ip -4 addr show
ip route
```

常见默认：`192.168.100.1`（iStoreOS）或 `192.168.1.1`（OpenWrt 默认）。**以实测为准**。

Windows 静态地址（PowerShell，管理员）：

```powershell
Get-NetAdapter | Format-Table Name,InterfaceDescription,Status
# 以实际网卡名为准，例如 "Ethernet"
$if = "Ethernet"
Set-NetIPInterface -InterfaceAlias $if -Dhcp Disabled
New-NetIPAddress -InterfaceAlias $if -IPAddress 192.168.100.2 -PrefixLength 24
Test-NetConnection 192.168.100.1 -Port 80
```

回退：

```powershell
Remove-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.100.2 -Confirm:$false
Set-NetIPInterface -InterfaceAlias "Ethernet" -Dhcp Enabled
```

如果 iStoreOS 是 `192.168.1.1`，把 `192.168.100.2` 换成 `192.168.1.2`，`192.168.100.1` 换成 `192.168.1.1`。

无串口时从 Windows 侧探测：

```powershell
arp -a | Select-String "192.168.100|192.168.1"
Get-NetNeighbor -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.100.*"}
```

### 5.3 SSH

```bash
# 设备端（串口/ LuCI 终端）先确认 dropbear
/etc/init.d/dropbear status
uci show dropbear
# 如未启用
/etc/init.d/dropbear enable
/etc/init.d/dropbear start

# 设置 root 密码（只写入 /build/verify-secrets，不进 Git）
passwd
```

从 Windows/Git Bash：

```bash
ssh root@192.168.100.1
```

自动化用密钥（推荐）：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/istore-test -N ''
cat ~/.ssh/istore-test.pub | ssh root@192.168.100.1 \
  'mkdir -p /etc/dropbear && cat >> /etc/dropbear/authorized_keys && chmod 600 /etc/dropbear/authorized_keys'
ssh -i ~/.ssh/istore-test root@192.168.100.1 'uname -a'
```

凭据存放：

```bash
mkdir -p /build/verify-secrets
chmod 700 /build/verify-secrets
# 文件 0600；不要写进仓库、截图、feed
```

### 5.4 LuCI

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.100.1/cgi-bin/luci/
```

预期：`200` 或 `302`。浏览器打开 `http://192.168.100.1/`，完成首启密码/登录，截图：

- `evidence/<env>/platform/luci-login.png`
- `evidence/<env>/platform/luci-overview.png`

### 5.5 固件版本基线采集

在设备上执行并保存：

```bash
OUT=/tmp/istore-baseline.txt
{
  echo "== date"; date -u
  for f in /etc/openwrt_release /etc/openwrt_version /etc/os-release \
           /etc/istoreos_release /etc/version.buildinfo /etc/istore/version; do
    [ -f "$f" ] && { echo "== $f"; cat "$f"; }
  done
  echo "== uname"; uname -a
  echo "== pagesize"; getconf PAGESIZE
  echo "== cmdline"; cat /proc/cmdline
  echo "== board"; ubus call system board
  echo "== arch"; opkg print-architecture
  echo "== docker"; docker version 2>&1
  echo "== podman"; podman version 2>&1
  echo "== df"; df -h
} | tee "$OUT"
```

从 Windows 取回：

```bash
scp root@192.168.100.1:/tmp/istore-baseline.txt \
  docs/verification/evidence/la5/baseline/istore-baseline.txt
```

预期与记录：

- `DISTRIB_ARCH="loongarch64"`；
- la5 基线：`24.10.8` / `r0-fb97140`（以 `/etc/openwrt_release` 原文为准）；
- p1：同一基线 + 私人预置标识；不能出现公开版没有的“私人节点/密钥”被打印到证据里（只记录版本字段）；
- kernel `6.6.52-loong64`（以 `uname -a` 为准）；
- 页大小 `16384`（以 `getconf PAGESIZE` 为准）；
- Docker/Podman 实际版本写入 `VERSION-MATRIX`，不要抄计划表。

如果设备上没有 `/etc/version.buildinfo`，它是 Release 附件而不是必然安装到设备的文件；用 Release 的 `version.buildinfo` 与 `/etc/openwrt_release` 对照，并记录“设备端无该路径”。

### 5.6 容器栈基线

```bash
docker version
docker info --format 'server={{.ServerVersion}} driver={{.Driver}} root={{.DockerRootDir}}'
podman version
podman info --format 'arch={{.Host.Arch}} version={{.Version.Version}}'
ls -l /etc/init.d/dockerd
/etc/init.d/dockerd enabled && echo DOCKERD_ENABLED

docker run --rm --network=none yunixintel/node:24.10-la5 node -v
podman run --rm --network=none --security-opt seccomp=unconfined \
  --cgroups=disabled --runtime crun yunixintel/node:24.10-la5 node -v
```

预期：

- Docker CLI + server 可用；`DockerRootDir` 在持久分区（不是 `/tmp` tmpfs）；
- `node -v` 输出 `v24.22.1`（`24.10-la5` tag 指向 24.22.1；若实际不是，记录实际值）；
- Podman `host/none` 可运行；**bridge 网络**可能因宿主缺 `nft_conntrack` 失败，属已知限制，单独记 `PARTIAL`/`BLOCKED`，不要算应用失败。

### 5.7 网络/防火墙基线

```bash
ip -4 addr show
ip route
uci show network | grep -E 'lan|wan|proto|ipaddr|netmask'
cat /etc/resolv.conf
nslookup openwrt.org 2>&1 | head
fw4 check 2>&1 || true
nft list ruleset 2>/dev/null | head -80
uci show firewall | head -80
```

从 Windows：

```powershell
Test-NetConnection 192.168.100.1 -Port 22
Test-NetConnection 192.168.100.1 -Port 80
```

预期：

- LAN 地址可访问；SSH/LuCI 端口开放；
- `fw4 check` 无语法错误；
- 若有 WAN，WAN 侧不应直接暴露 SSH/LuCI；隔离直连拓扑下 WAN 负向测试记 `NOT TESTED`（没有 WAN）。

### 5.8 p1 私人预置隔离（先于接实验室网络）

p1 基于 v2-personal 预置，可能自带 EasyTier/mihomo 等自启。**在把 p1 接入任何实验室/上游网络之前**，用串口或隔离直连检查：

```bash
ps | grep -E 'easytier|mihomo|tailscale|clash' | grep -v grep
uci show easytier 2>/dev/null | head -40
uci show mihomo 2>/dev/null | head -40
/etc/init.d/easytier status 2>/dev/null || true
/etc/init.d/mihomo status 2>/dev/null || true
```

若发现自启并连接私人网络：

```bash
# 先记录，再停（这是配置变更，需在 state 记 before/after）
/etc/init.d/easytier stop 2>/dev/null || true
/etc/init.d/easytier disable 2>/dev/null || true
/etc/init.d/mihomo stop 2>/dev/null || true
/etc/init.d/mihomo disable 2>/dev/null || true
```

回退：`/etc/init.d/easytier enable && /etc/init.d/easytier start`（mihomo 同理）。只在用户确认需要恢复私人预置时执行。

**证据脱敏**：p1 截图/日志不得出现私人节点地址、订阅 URL、密钥；必要时打码或只保留字段名。

---

## 6. Step 4：public / private feed 部署

### 6.1 服务端：Windows HTTP server（推荐）

```powershell
cd C:\Users\yunix\Documents\Codex\2026-10-01\zhe\outputs\istore-la-public\store\istore\feed
python -m http.server 8000 --bind 0.0.0.0
```

Windows 防火墙放行 8000（管理员 PowerShell）：

```powershell
New-NetFirewallRule -DisplayName "iStore feed 8000" -Direction Inbound `
  -Protocol TCP -LocalPort 8000 -Action Allow
```

取 PC IP：

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.100.*"}
```

本机自测：

```bash
curl -s http://127.0.0.1:8000/public/all/meta/Packages | head
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/public/all/meta/Packages
```

Linux 替代：

```bash
cd store/istore/feed
python3 -m http.server 8000 --bind 0.0.0.0
# 或
busybox httpd -f -p 8000 -h .
```

**HTTP 根固定为 `store/istore/feed`**，所以 URL 是：

- public meta：`http://192.168.100.2:8000/public/all/meta`
- public luci：`http://192.168.100.2:8000/public/all/nas_luci`
- private meta：`http://192.168.100.2:8000/private/all/meta`
- private luci：`http://192.168.100.2:8000/private/all/nas_luci`

如果你改用仓库根作 HTTP 根，URL 要加 `store/istore/feed/` 前缀；不要两套混用。

### 6.2 设备端：`customfeeds.conf` 精确内容

先备份：

```bash
cp /etc/opkg/customfeeds.conf /etc/opkg/customfeeds.conf.bak.$(date +%F-%H%M%S)
cp /etc/opkg.conf /etc/opkg.conf.bak.$(date +%F-%H%M%S)
```

public feed：

```bash
cat > /etc/opkg/customfeeds.conf <<'EOF'
# istore la5 public feed (local HTTP)
src/gz istore-loong64-meta http://192.168.100.2:8000/public/all/meta
src/gz istore-loong64-luci http://192.168.100.2:8000/public/all/nas_luci
EOF
```

private feed：

```bash
cat > /etc/opkg/customfeeds.conf <<'EOF'
# istore p1 private feed (local HTTP)
src/gz istore-loong64-meta http://192.168.100.2:8000/private/all/meta
src/gz istore-loong64-luci http://192.168.100.2:8000/private/all/nas_luci
EOF
```

关闭签名校验（开发/内网 feed，`Packages.sig` 为空）：

```bash
if grep -q '^option check_signature' /etc/opkg.conf; then
  sed -i 's/^option check_signature.*/option check_signature 0/' /etc/opkg.conf
else
  echo 'option check_signature 0' >> /etc/opkg.conf
fi
grep -n 'check_signature' /etc/opkg.conf
```

> 计划里把 `check_signature 0` 写在 `customfeeds.conf`；opkg 实际读取 `/etc/opkg.conf` 的全局选项更稳妥。若你的固件只在 `customfeeds.conf` 生效，也可把该行追加到 `customfeeds.conf`，但必须记录实际文件。

### 6.3 `opkg update` 与 feed 可见性

```bash
opkg update 2>&1 | tee /tmp/opkg-update.log

# 预期两个自定义 feed 都下载成功；官方源失败单独记录，不阻塞自定义 feed
grep -E 'istore-loong64-(meta|luci)' /tmp/opkg-update.log

opkg list | awk '/^app-meta-/{print $1}' | wc -l        # 115
opkg list | grep -E '^luci-app-istore-loong64 ' || true
```

预期：115 个 `app-meta-*`；`luci-app-istore-loong64` 可见。private feed 的 app-meta 版本应带 `-p1`（例如 `app-meta-gogs_1.0.0-r20261025-p1`）；public feed 为 `1.0.0-r20261025`。若 `opkg update` 报 `Signature check failed`，检查 6.2 的 `check_signature`；若 404，检查 HTTP 根/URL；若连接拒绝，检查 Windows 防火墙和 `PC_IP`。

### 6.4 安装通用安装器与 app-meta

```bash
# 依赖预检：docker-deps 缺失时，通用包会装不上
opkg list | grep -E '^docker-deps ' || echo "docker-deps MISSING"
opkg list-installed | grep -E '^docker |^dockerd |^containerd ' || true

# 若 docker-deps 缺失：从 la5 Release 的 opkg-feed 资产补装（不要改 feed 的 Depends）
# 1) 在 Host A 下载 opkg-feed-loongarch64_generic.tar.gz
# 2) 解包到 /tmp/opkg-feed，找到 docker-deps_*.ipk
# 3) opkg install /tmp/opkg-feed/docker-deps_*.ipk
# 4) 仍失败则标 P1/BLOCKED，不要用“删依赖”绕过

opkg install luci-app-istore-loong64 2>&1 | tee /tmp/install-luci-istore.log
opkg list-installed | grep luci-app-istore-loong64

# 代表性 app-meta（单容器）
opkg install app-meta-gogs 2>&1 | tee /tmp/install-app-meta-gogs.log
ls -l /usr/lib/opkg/meta/gogs.json
ls -l /usr/libexec/istorec/gogs.sh
```

预期：安装成功；`gogs.json` 和 wrapper 存在且可执行。

**让 115 个卡片可见（确定性方法）**：app-meta 只是元数据包（几十 KB，不含镜像）。iStore/通用页面以 `/usr/lib/opkg/meta/*.json` 为数据源；批量安装 115 个 app-meta：

```bash
for p in $(opkg list | awk '/^app-meta-/{print $1}'); do
  opkg install "$p" 2>&1 | tee -a /tmp/install-all-app-meta.log || echo "FAIL $p"
done

ls /usr/lib/opkg/meta/*.json | sed 's#.*/##;s#\.json##' | sort > /tmp/meta-now.txt
# 与 feed 的 115 个 app 名单比对；系统自带 meta 会让总数略多，不能只看总数
grep -c . /tmp/meta-now.txt
```

预期：本 feed 的 115 个 app 全部在 `/tmp/meta-now.txt` 中；总数可能因系统自带 meta 略多于 115，**不能把“总数 115”当成唯一证据**。用名单比对：

```bash
# Windows/仓库侧生成 feed 名单
ls store/istore/feed/public/all/meta/app-meta-*.ipk \
  | sed 's#.*app-meta-##;s#_1\.0\.0.*##' | sort > /tmp/feed-apps.txt
wc -l /tmp/feed-apps.txt    # 115
```

说明：

- 如果固件 iStore 直接读取 feed 索引、不要求预装 app-meta，可跳过批量安装；但“本 feed 的 115 个 app 都能在 `/usr/lib/opkg/meta/` 找到”仍是硬验收。
- 如果 iStore UI 仍不足 115：记录 iStore 版本、后端日志、`/usr/lib/opkg/meta/` 名单比对结果，标 `BLOCKED`；**不要用通用页面 115 冒充 iStore 商店 115**。

### 6.5 安装/升级/卸载动作

```bash
id=gogs
/usr/libexec/istorec/$id.sh render   > /tmp/$id.render
/usr/libexec/istorec/$id.sh config   > /tmp/$id.config
/usr/libexec/istorec/$id.sh pull     > /tmp/$id.pull.log 2>&1 || true
/usr/libexec/istorec/$id.sh install  > /tmp/$id.install.log 2>&1
echo "install_exit=$?"

/usr/libexec/istorec/$id.sh status-all | tee /tmp/$id.status-all
/usr/libexec/istorec/$id.sh ports      | tee /tmp/$id.ports
/usr/libexec/istorec/$id.sh url        | tee /tmp/$id.url
/usr/libexec/istorec/$id.sh logs 80    | tee /tmp/$id.logs
```

预期：`install_exit=0`；`status-all` 主容器 `running`；无 sidecar 的应用不出现 sidecar 容器；端口与 `ports` 一致。

### 6.6 public 依赖：LBrowser 运行时自动拉取 + 宿主目录预置

public 的 Linkwarden/Karakeep 需要：

1. 镜像 `yunixintel/lbrowser-runtime:3.4.2293.2`（公开，安装器会自动 pull；只有 `local/*` 才禁止 pull）；
2. 宿主目录 `/opt/apps/lbrowser`（sidecar 以 `ro` 挂载）。

在 Host A 内部系统准备 tar：

```bash
ssh loongson-lab

docker image inspect yunixintel/lbrowser-runtime:3.4.2293.2 \
  > ~/istore-exec-evidence/lbrowser-image-inspect.txt
docker save yunixintel/lbrowser-runtime:3.4.2293.2 \
  -o /build/base-images-la5.tar
sha256sum /build/base-images-la5.tar

ls -ld /opt/apps/lbrowser
tar czf /build/lbrowser-app.tar.gz -C /opt/apps lbrowser
sha256sum /build/lbrowser-app.tar.gz
```

把两个 tar 放到 Windows 第二 HTTP 根（例如 `xfer-out`，端口 8001）：

```powershell
cd C:\Users\yunix\Documents\Codex\2026-10-01\zhe\outputs\xfer-out
python -m http.server 8001 --bind 0.0.0.0
```

设备上：

```bash
cd /tmp
wget -O base-images-la5.tar http://192.168.100.2:8001/base-images-la5.tar
wget -O lbrowser-app.tar.gz http://192.168.100.2:8001/lbrowser-app.tar.gz
# 若无 wget：
# uclient-fetch -O base-images-la5.tar http://192.168.100.2:8001/base-images-la5.tar

sha256sum base-images-la5.tar lbrowser-app.tar.gz   # 与 Host A 记录比对
docker load -i base-images-la5.tar
docker image inspect yunixintel/lbrowser-runtime:3.4.2293.2
mkdir -p /opt/apps
tar xzf lbrowser-app.tar.gz -C /opt/apps
ls -ld /opt/apps/lbrowser
```

预期：镜像 inspect 成功；`/opt/apps/lbrowser` 存在且可读。**缺任一条件，public Linkwarden/Karakeep 的 install 必须标 `BLOCKED`，不得假 PASS。**

### 6.7 private 预载：`local/*` 单镜像

在 Host A 内部系统：

```bash
ssh loongson-lab

docker image inspect local/linkwarden-private:2.16.3-p1 \
                     local/karakeep-private:0.34.1-p1
docker save local/linkwarden-private:2.16.3-p1 \
            local/karakeep-private:0.34.1-p1 \
  -o /build/private-images.tar
sha256sum /build/private-images.tar
```

把 `private-images.tar` 放到 Windows `xfer-out`，设备上：

```bash
cd /tmp
wget -O private-images.tar http://192.168.100.2:8001/private-images.tar
sha256sum private-images.tar
docker load -i private-images.tar
docker image inspect local/linkwarden-private:2.16.3-p1 \
                     local/karakeep-private:0.34.1-p1
```

预期：两个 `local/*` 镜像存在。安装器遇到 `local/*` 只 inspect，不会 pull；缺失时 install 失败并提示预加载。**private 版不推 Hub、不复制进 feed。**

### 6.8 public/private 隔离审计

#### 构建产物审计（Windows/Host A 仓库）

```bash
cd store/istore

# public 不得含 local/*、私人仓库 URL
python3 -I - <<'PY'
import glob,io,json,sys,tarfile
bad=[]
for ipk in glob.glob('feed/public/all/meta/app-meta-*.ipk'):
    with tarfile.open(ipk) as t:
        m=next(x for x in t.getmembers() if x.name.endswith('data.tar.gz'))
        data=t.extractfile(m).read()
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
        for m in t.getmembers():
            if m.name.endswith('.json'):
                j=json.load(t.extractfile(m))
                s=json.dumps(j,ensure_ascii=False)
                if 'local/' in s or 'istore-la-private' in s:
                    bad.append((j.get('name'), 'local/' if 'local/' in s else 'private-url'))
print('PUBLIC_BAD', bad) if bad else print('PUBLIC_CLEAN')
sys.exit(1 if bad else 0)
PY

# private：Linkwarden/Karakeep 默认 private + local/*
python3 -I - <<'PY'
import glob,io,json,sys,tarfile
for app in ('linkwarden','karakeep'):
    ipk=glob.glob(f'feed/private/all/meta/app-meta-{app}_*.ipk')[0]
    with tarfile.open(ipk) as t:
        m=next(x for x in t.getmembers() if x.name.endswith('data.tar.gz'))
        data=t.extractfile(m).read()
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
        m=next(x for x in t.getmembers() if x.name.endswith(f'{app}.json'))
        j=json.load(t.extractfile(m))
    L=j['loong64']
    assert L.get('default_variant')=='private', (app,L.get('default_variant'))
    images=[v.get('image') for v in L.get('variants',[])]
    assert any(i.startswith('local/') for i in images), (app,images)
    print(app,'OK',L.get('default_variant'),images)
PY

# 不得有真实 token/密钥样式
grep -R -I -E 'dckr_pat_|ghp_|github_pat_|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY' \
  feed/ || echo NO_SECRET_PATTERN
```

#### 设备端审计

la5（public）：

```bash
# 不应有 local/*
grep -R "local/" /usr/lib/opkg/meta/*.json /usr/share/istore-loong64/apps/*.conf 2>/dev/null \
  && echo "FAIL: public has local/*" || echo "PASS: public clean"

# 不应有私人仓库 URL
grep -R "istore-la-private" /usr/lib/opkg/meta /usr/share/istore-loong64 2>/dev/null \
  && echo "FAIL: private url in public" || echo "PASS: no private url"

# 不应有 token/密钥
grep -R -I -E 'dckr_pat_|ghp_|github_pat_|BEGIN [A-Z ]*PRIVATE KEY' \
  /usr/lib/opkg/meta /usr/share/istore-loong64 /etc/config 2>/dev/null \
  && echo "FAIL: secret pattern" || echo "PASS: no secret pattern"
```

p1（private）：

```bash
# 只有 linkwarden/karakeep 允许 local/*
grep -R "local/" /usr/lib/opkg/meta/*.json /usr/share/istore-loong64/apps/*.conf 2>/dev/null \
  | grep -v -E 'linkwarden|karakeep' \
  && echo "FAIL: unexpected local/*" || echo "PASS: only linkwarden/karakeep local"

# Linkwarden/Karakeep 默认 private
for app in linkwarden karakeep; do
  echo "== $app"
  jsonfilter -i /usr/lib/opkg/meta/$app.json -e '@.loong64.default_variant'
  jsonfilter -i /usr/lib/opkg/meta/$app.json -e '@.loong64.variants[*].image'
done
```

预期：

- la5：`PUBLIC_CLEAN` / `PASS: public clean`；
- p1：`default_variant=private`，variants 含 `local/linkwarden-private:2.16.3-p1`、`local/karakeep-private:0.34.1-p1`；
- 两边都没有 token/密钥样式。

任何 `FAIL`：停止安装/发布，按 P0 隐私事故处理；修 feed 后重跑审计。

### 6.9 feed 回退

```bash
# 恢复 opkg 配置
cp /etc/opkg.conf.bak.* /etc/opkg.conf
cp /etc/opkg/customfeeds.conf.bak.* /etc/opkg/customfeeds.conf
opkg update
```

- 若 custom feed 把官方源搞坏：恢复备份后只保留官方源，先确认 `opkg update` 正常，再逐行加自定义 feed。
- 若 public feed 有 `local/*`：不要“临时改 JSON”上机；重建 feed 并重跑审计。

---

## 7. Step 5：iStore 平台矩阵

每个模块都要有命令/UI 步骤、预期、证据路径。平台失败先修平台，再继续应用矩阵。

### 7.1 平台矩阵总表

| 模块 | 操作 | 预期 | 证据 |
|---|---|---|---|
| LuCI 登录 | 浏览器 `/`，首启密码，登录/登出 | 200/302；会话正常 | `platform/luci-login.png`、`luci-overview.png` |
| 网络 | `ip -4 addr`、`ip route`、`uci show network`、`nslookup` | LAN 可达；有 WAN 时默认路由/DNS 正常 | `platform/network.txt` |
| 防火墙 | `fw4 check`、`nft list ruleset`、`uci show firewall`；PC 测 22/80 | 无语法错误；LAN 放行；WAN 不暴露 | `platform/firewall.txt`、`nmap.txt` |
| opkg | `opkg update`、`opkg list`、装/卸 app-meta | 115 可见；安装/卸载无残留 | `platform/opkg-*.log` |
| Docker | `docker version/info`、`docker run` node | server/client 可用；node v24.22.1 | `platform/docker.txt` |
| Podman | `podman version/info`、none/host 运行、bridge 负向 | none/host OK；bridge 已知限制 | `platform/podman.txt` |
| 存储 | `block info`、`df -h`、`mount`、LuCI 挂载点 | 只读识别；不写内部盘；`/srv` 可写 | `platform/storage.txt`、截图 |
| 共享 | `opkg list-installed | grep samba/nfs`、`smbclient -L`、`showmount -e` | 有服务则列出；无则 NOT TESTED | `platform/share.txt` |
| 用户 | LuCI System→Administration；`passwd`；SSH key | 改密/登录/密钥可用；多用户不支持 | `platform/users.txt`（脱敏） |
| 终端 | `command -v ttyd`；LuCI 终端；SSH | 终端可开；SSH 可用 | `platform/terminal.png` |
| 日志 | `logread`、`dmesg`、LuCI 系统/内核日志 | 无持续 error/panic；警告记录 | `platform/logs.txt` |
| 重启 | `sync; reboot`；等待；`uptime`、`docker ps`、LuCI | 正常回来；dockerd 自启；应用持久化 | `platform/reboot.txt` |
| 商店 115 | `/usr/lib/opkg/meta/` 名单与 feed 115 比对；iStore UI；通用页 | 115 名单齐全（总数可略多）；搜索/分类/详情可用 | `platform/store-115.png`、`meta-count.txt` |
| 安装/升级/卸载 | gogs/joplin 生命周期；`rm`/`purge` | 安装 running；数据保留；purge 仅显式 | `platform/lifecycle.txt` |

### 7.2 网络与防火墙

```bash
ip -4 addr show | tee /tmp/platform-network.txt
ip route | tee -a /tmp/platform-network.txt
uci show network | tee -a /tmp/platform-network.txt
cat /etc/resolv.conf | tee -a /tmp/platform-network.txt
nslookup openwrt.org 2>&1 | tee -a /tmp/platform-network.txt

fw4 check 2>&1 | tee /tmp/platform-firewall.txt
nft list ruleset 2>/dev/null | tee -a /tmp/platform-firewall.txt
uci show firewall | tee -a /tmp/platform-firewall.txt
```

Windows：

```powershell
Test-NetConnection 192.168.100.1 -Port 22 | Tee-Object platform-ssh.txt
Test-NetConnection 192.168.100.1 -Port 80 | Tee-Object platform-http.txt
```

预期：LAN 侧 22/80 可达；`fw4 check` 返回 0；没有把 LuCI/SSH 暴露到 WAN 的规则。隔离直连无 WAN，WAN 负向测试记 `NOT TESTED`。

### 7.3 opkg

```bash
opkg update
opkg list-installed | wc -l
opkg list | awk '/^app-meta-/{print $1}' | wc -l   # 115
opkg install app-meta-gogs
opkg remove app-meta-gogs
opkg list-installed | grep app-meta-gogs || echo REMOVED
```

预期：update 成功；115 可见；安装/卸载成功。不要 `opkg upgrade` 全量升级；不要移除 `docker`、`luci-base`、`dropbear` 等基础包。

### 7.4 Docker / Podman

```bash
docker version | tee /tmp/platform-docker.txt
docker info --format '{{.ServerVersion}} {{.Driver}} {{.DockerRootDir}}' | tee -a /tmp/platform-docker.txt
docker ps -a | tee -a /tmp/platform-docker.txt
docker run --rm --network=none yunixintel/node:24.10-la5 node -v | tee -a /tmp/platform-docker.txt

podman version | tee /tmp/platform-podman.txt
podman info --format '{{.Host.Arch}} {{.Version.Version}}' | tee -a /tmp/platform-podman.txt
podman run --rm --network=none --security-opt seccomp=unconfined \
  --cgroups=disabled --runtime crun yunixintel/node:24.10-la5 node -v \
  | tee -a /tmp/platform-podman.txt

# bridge 负向（预期可能失败，记录而不是当应用失败）
podman run --rm --network=bridge --security-opt seccomp=unconfined \
  --cgroups=disabled --runtime crun yunixintel/node:24.10-la5 true \
  | tee -a /tmp/platform-podman.txt || echo PODMAN_BRIDGE_KNOWN_LIMIT
```

预期：Docker 可运行；Podman none/host 可运行；bridge 若失败，记录 `nft_conntrack`/内核模块缺失，标 `PARTIAL`。

Docker socket 安全检查（给后面 portainer/dozzle/dpanel/watchtower 用）：

```bash
ls -l /var/run/docker.sock /root/docker.sock 2>/dev/null
docker -H unix:///root/docker.sock ps 2>&1 | head
```

预期：socket 存在；`-H unix:///root/docker.sock` 能列出容器。不要把这个 socket 暴露到公网。

### 7.5 存储（非破坏性）

```bash
block info | tee /tmp/platform-storage.txt
cat /proc/partitions | tee -a /tmp/platform-storage.txt
df -h | tee -a /tmp/platform-storage.txt
mount | tee -a /tmp/platform-storage.txt
docker info --format '{{.DockerRootDir}}' | tee -a /tmp/platform-storage.txt
```

预期与红线：

- 能看到 U 盘/overlay；`/srv` 可写；Docker root 在持久分区。
- 若看到内部盘 `/dev/sda*`、`/dev/nvme*` 被自动挂载：**立即 `umount` 并记录**；不要格式化、不要写测试文件。
- 格式化/分区/挂载写测试本阶段 **NOT TESTED**：没有独立空盘；Host A 内部盘受保护；U 盘是启动盘不能格式化。
- 只做 LuCI “挂载点”页面只读截图。

```bash
# 如发现内部盘被挂载，先记录再卸载
mount | grep -E '/dev/(sda|nvme)' | tee -a /tmp/platform-storage.txt
# 逐条确认后：
# umount /dev/sda1
```

### 7.6 共享

```bash
opkg list-installed | grep -E 'samba|nfs' | tee /tmp/platform-share.txt
uci show samba4 2>/dev/null | tee -a /tmp/platform-share.txt
/etc/init.d/samba4 status 2>/dev/null | tee -a /tmp/platform-share.txt
```

Windows：

```powershell
net view \\192.168.100.1
```

Linux：

```bash
smbclient -L //192.168.100.1 -N
showmount -e 192.168.100.1
```

预期：若固件已带 Samba/NFS，能列出共享；若未安装，记 `NOT TESTED`（原因：iStoreOS 基础镜像未带/官方源不可达），不要为了测试去装一堆包。若安装并创建测试共享：

```bash
mkdir -p /srv/share-test
echo hello > /srv/share-test/hello.txt
# 在 LuCI 添加共享 /srv/share-test（先备份 /etc/config/samba4）
# 从 Windows 读回 hello.txt
```

回退：删除测试共享配置，恢复 `/etc/config/samba4` 备份，`/etc/init.d/samba4 restart`。

### 7.7 用户、终端、日志、重启

用户：

```bash
passwd
cat /etc/passwd | cut -d: -f1,3,7 | head
```

- 测试 root 改密→登出→新密码登录；测试 SSH key；记录到 `/build/verify-secrets`（0600），不截图密码。
- OpenWrt/LuCI 默认单 root，多用户/RBAC 记 `NOT TESTED`（原因：固件无多用户管理），不要伪造。

终端：

```bash
command -v ttyd || true
uci show ttyd 2>/dev/null || true
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.100.1/cgi-bin/luci/admin/system/terminal
```

若 `ttyd` 不存在：可尝试 `opkg install luci-app-ttyd`（官方源可达时）；否则记 `NOT TESTED`，SSH 终端已覆盖。

日志：

```bash
logread | tail -100 | tee /tmp/platform-logs.txt
dmesg | tail -100 | tee -a /tmp/platform-logs.txt
logread | grep -iE 'error|fail|panic|oom' | tail -50 | tee -a /tmp/platform-logs.txt
dmesg | grep -iE 'error|fail|panic|usb|mmc' | tail -50 | tee -a /tmp/platform-logs.txt
```

预期：无持续 error/panic；USB/存储错误单列。LuCI Status→System Log/Kernel Log 截图。

重启：

```bash
sync
uptime | tee /tmp/platform-reboot-before.txt
reboot
# 等待 90–120 秒
```

从 Windows 重新连：

```bash
ssh -i ~/.ssh/istore-test root@192.168.100.1 \
  'uptime; docker ps; /usr/libexec/istorec/gogs.sh status-all; ls -l /srv/gogs'
```

预期：设备回来；`uptime` 小于几分钟；dockerd 自启；已装应用容器 running；数据目录存在。若没回来：串口/iKVM；若 dockerd 未自启，`/etc/init.d/dockerd enable && start`，记 P1/PARTIAL。

### 7.8 商店 115 与生命周期

```bash
ls /usr/lib/opkg/meta/*.json | wc -l | tee /tmp/platform-meta-count.txt
ls /usr/lib/opkg/meta/*.json | sed 's#.*/##;s#\.json##' | sort > /tmp/platform-meta-list.txt
wc -l /tmp/platform-meta-list.txt
# 与 feed 的 115 名单比对（见 6.4）；总数可能略多，名单不能少
```

浏览器：

1. 打开 LuCI 菜单里的 iStore（路径可能是 `/cgi-bin/luci/admin/store`，用菜单实际项为准）。
2. 确认 115 个卡片、分类、搜索、详情、图标（默认图标可接受，记 P3）。
3. 打开通用页 `/cgi-bin/luci/admin/services/istore-loong64`，确认 115 行。
4. 截图：`platform/store-list.png`、`platform/store-detail.png`、`platform/store-search.png`。

生命周期（gogs 单容器 + joplin 带 PG sidecar）：

```bash
id=gogs
opkg install app-meta-$id
/usr/libexec/istorec/$id.sh install
/usr/libexec/istorec/$id.sh status-all
/usr/libexec/istorec/$id.sh url
# 浏览器打开，写测试数据
/usr/libexec/istorec/$id.sh install          # 升级/重建
/usr/libexec/istorec/$id.sh rm
test -d /srv/$id && echo DATA_KEPT
/usr/libexec/istorec/$id.sh status-all
# 重装
/usr/libexec/istorec/$id.sh install
# purge 负向：默认不删数据
/usr/libexec/istorec/$id.sh purge
test -d /srv/$id && echo PURGE_DEFAULT_KEPT
# 只有明确同意测试数据可删时才执行：
# ISTORE_PURGE_DATA=1 /usr/libexec/istorec/$id.sh purge
```

预期：install running；升级后数据仍在；`rm` 删除容器但保留 `/srv/$id`；`purge` 默认保留；显式 flag 才删除。记录每一步 exit code 和 `status-all`。

---

## 8. Step 6：115 应用矩阵

### 8.1 单应用通用流程（每张卡都按此执行）

```text
预检 → opkg install app-meta → render/config → pull → install
→ status-all / ports / url → HTTP/UI 核心功能 → 重启持久化
→ 升级/重建 → 卸载 rm（数据保留）→ 清理
```

每步证据：

| 步骤 | 命令/动作 | 预期 | 证据 |
|---|---|---|---|
| 预检 | `docker manifest inspect yunixintel/<id>:24.10-la5`（或 `docker pull`） | manifest 200 / 拉取成功 | `pull.log` |
| 元数据 | `opkg install app-meta-<id>` | 安装成功 | `opkg.log` |
| 渲染 | `.../render`、`.../config` | 镜像/tag/端口/卷/sidecar 正确；public 无 `local/*` | `render.txt`、`config.txt` |
| 安装 | `.../install` | exit 0；主容器 running | `install.log`、`status-all.txt` |
| 端口 | `.../ports`、`netstat -ltnup` | 端口实际监听，无冲突 | `ports.txt` |
| 功能 | `curl -D headers -o body URL`；浏览器 | 预期 HTTP/正文/UI | `headers.txt`、`ui-*.png` |
| 重启 | `sync; reboot`；重连 | 容器自启，数据仍在 | `reboot-status.txt` |
| 升级 | 再 `install` 或重装 app-meta | 容器重建，数据仍在 | `upgrade.txt` |
| 卸载 | `.../rm` | 容器删除，`/srv/<id>` 保留 | `uninstall.txt` |
| 清理 | `docker image rm ...`（按需） | 释放空间，不删 base 镜像 | `cleanup.txt` |

**public 断言**：

```bash
! grep -q 'local/' /tmp/<id>.render && echo PUBLIC_RENDER_CLEAN
```

**private 断言**（Linkwarden/Karakeep）：

```bash
grep -q 'local/linkwarden-private:2.16.3-p1' /tmp/linkwarden.render
! grep -q 'lbrowser' /tmp/linkwarden.render
jsonfilter -i /usr/lib/opkg/meta/linkwarden.json -e '@.loong64.default_variant'   # private
```

### 8.2 la5 批次（public feed；共 115）

| 批次 | 数量 | 应用 | 重点 | 预计 |
|---|---:|---|---|---:|
| **L-B0** 基础/数据 | 6 | `postgres` `redis` `mariadb` `minio` `memcached` `mosquitto` | 镜像/默认环境/端口/持久化；无 sidecar | 1.5h |
| **L-B1** 单容器低风险 | 40 | `heimdall` `wizarr` `ntfy` `gotify` `apprise-api` `komga` `memos` `linkding` `shiori` `firefly-iii` `freshrss` `actual-budget` `homebox` `mealie` `vikunja` `readeck` `syncthing` `filebrowser` `nextcloud` `kodexplorer` `sftpgo` `gogs` `it-tools` `one-api` `code-server` `openwebui` `gitea` `nocodb` `webvirtcloud` `hermes` `registry` `node-red` `uptimekuma` `changedetection` `grafana` `vaultwarden` `pocket-id` `nginx-proxy-manager` `homer` `dashy` | 登录/首启、3 个核心功能、重启 | 8h |
| **L-B2** 媒体/下载 | 22 | `jellyfin` `navidrome` `excalidraw` `drawio` `xteve` `jellyseerr` `audiobookshelf` `calibre-web` `tautulli` `stirling-pdf` `chinesesubfinder` `lanraragi` `mymind` `qbittorrent-ee` `jackett` `sonarr` `radarr` `prowlarr` `bazarr` `autobrr` `metube` `sabnzbd` | 媒体路径/库扫描/播放或 API；*arr 连接 | 5h |
| **L-B3** 多服务/sidecar | 14 | `joplin-server` `miniflux` `jellystat` `bookstack` `piwigo` `matomo` `ente-server` `ente-web` `penpot-backend` `penpot-frontend` `linkwarden` `karakeep` `paperless-ngx` `homarr` | sidecar 健康/启动顺序/secrets；LBrowser | 6h |
| **L-B4** host 网络/特权/反代 | 17 | `mihomo` `easytier` `adguardhome` `homeassistant` `node-exporter` `pihole` `homebridge` `owntone` `dpanel` `portainer` `watchtower` `dozzle` `woodpecker-agent` `caddy` `headscale` `authelia` `wg-easy` | host 网络/端口冲突/docker.sock/设备/内核 | 5h |
| **L-B5** manual/设备/备份/首启 | 16 | `go2rtc` `mediamtx` `phpmyadmin` `typecho` `wallabag` `unpackerr` `prometheus` `gatus` `alertmanager` `smartctl-exporter` `scrutiny` `kopia` `rest-server` `backrest` `zigbee2mqtt` `woodpecker-server` | 前置条件/设备/首启向导/已知限制 | 4h |

### 8.3 p1 批次（private feed；应用集合同 la5，差异如下）

| 批次 | 数量 | 与 L-Bn 的差异 | 预计 |
|---|---:|---|---:|
| **P-B0** | 6 | 同一批应用；private feed；其余应用仍用公开镜像 | 1.5h |
| **P-B1** | 40 | 同一批应用；private feed；验证 `store_url` 指向私人源但镜像仍是 `yunixintel/*:24.10-la5` | 8h |
| **P-B2** | 22 | 同一批应用；同上 | 5h |
| **P-B3** | 14 | **Linkwarden/Karakeep 默认 private、镜像 `local/*`、无 LBrowser sidecar、无需 `/opt/apps/lbrowser`**；其余 sidecar 同 public | 6h |
| **P-B4** | 17 | 同一批应用；private preset 先隔离；host 网络/端口冲突同 public | 5h |
| **P-B5** | 16 | 同一批应用；private feed | 4h |

> P-Bn 的应用清单逐项同 L-Bn，但 p1 必须重新生成 `results/p1/<app>.json` 和 `evidence/p1/<app>/`，不能复用 la5 结果；p1 的 feed、镜像 variant、默认配置不同，复用即造假。

p1 的 Linkwarden/Karakeep 必查：

```bash
for app in linkwarden karakeep; do
  echo "== $app"
  jsonfilter -i /usr/lib/opkg/meta/$app.json -e '@.loong64.default_variant'
  /usr/libexec/istorec/$app.sh render > /tmp/$app.render
  grep -E 'local/|lbrowser|PLAYWRIGHT|CRAWLER_STORE_PDF' /tmp/$app.render || true
done
```

预期：

- `default_variant=private`；
- Linkwarden render 有 `local/linkwarden-private:2.16.3-p1`，无 `lbrowser`/`PLAYWRIGHT_WS_URL`；
- Karakeep render 有 `local/karakeep-private:0.34.1-p1`，无 `lbrowser`，含 `CRAWLER_STORE_PDF=true`；
- 若 render 出现 `lbrowser`：说明 variant 没生效，检查 `/etc/config/<id>` 的 `option variant` 和旧 conffile，必要时：
  ```bash
  cp /etc/config/linkwarden /tmp/linkwarden.conf.bak
  uci set linkwarden.main.variant='private'
  uci commit linkwarden
  ```

### 8.4 host 网络与端口冲突（安装顺序）

先查当前监听：

```bash
netstat -ltnup 2>/dev/null || ss -ltnup
```

| 端口/资源 | 冲突应用 | 规则 |
|---|---|---|
| 53/tcp+udp | `dnsmasq`、`pihole`、`adguardhome` | 同时只能一个；host 网络应用先停 dnsmasq 再测，测完恢复 |
| 80/tcp | `pihole`、`caddy`、`adguardhome`（Web 可能 3000） | 一次一个；Caddy 保留 80/443，其他改高位或停 |
| 443/tcp | `caddy`、`nginx-proxy-manager` | 二者不要同时占 443；NPM 管理口 81 |
| 8123/tcp | `homeassistant` | host 网络；不要与其他 8123 冲突 |
| 8581/51826 | `homebridge` | host 网络；配对码测试 |
| 3689 | `owntone` | 需要 avahi/dbus；host 网络 |
| 8554/8555/1984 | `go2rtc`；`mediamtx` 也用 8554 | 二者二选一；先 `ports` 查看 |
| 51820/udp、51821 | `wg-easy` | 需要 NET_ADMIN/WireGuard 模块 |
| 9000/9001 | `minio` | B0 已占；不要再装第二个 MinIO |
| 5000 | `registry` | 与其它 5000 应用冲突 |
| docker.sock | `dpanel` `portainer` `watchtower` `dozzle` `woodpecker-agent` | 等同宿主 root；只装可信应用；不公网暴露 |

host 网络应用逐个测试：

```bash
# 示例：先停 dnsmasq，再测 pihole；测完恢复
/etc/init.d/dnsmasq stop
/usr/libexec/istorec/pihole.sh install
/usr/libexec/istorec/pihole.sh status-all
# 测试 DNS/Web
/etc/init.d/dnsmasq start

# 切换到 adguardhome 前先移除 pihole
/usr/libexec/istorec/pihole.sh rm
/usr/libexec/istorec/adguardhome.sh install
```

前置确认：停 dnsmasq 会短暂断 DNS；只在隔离直连环境做，记录 before/after；回退 `dnsmasq start`。若用户不允许停 dnsmasq，pihole/adguardhome 记 `BLOCKED`（53 被占）。

NPM/Caddy 顺序注意：`nginx-proxy-manager` 在 L-B1 先装时可能先占 443；到 L-B4 测 `caddy` 前先看：

```bash
/usr/libexec/istorec/nginx-proxy-manager.sh ports
/usr/libexec/istorec/caddy.sh ports
netstat -ltnup | grep -E ':(80|443|81)[[:space:]]' || true
```

若冲突：临时 `.../nginx-proxy-manager.sh rm` 或把 NPM 管理口/HTTPS 改高位，测完 Caddy 后恢复；记录实际端口，不要假设“自动改高位”一定发生。

### 8.5 sidecar 检查

| 应用 | sidecar | 检查 |
|---|---|---|
| `joplin-server` | `joplin-server-pg` | `status-all` 双 running；`/api/ping` 200 |
| `miniflux` | `miniflux-pg` | PG healthy；Web 登录 |
| `jellystat` | `jellystat-pg` | PG healthy；Web 200 |
| `linkwarden` public | `linkwarden-pg` + `linkwarden-lbrowser` | PG healthy；LBrowser `serve`；`PLAYWRIGHT_WS_URL` |
| `linkwarden` private | `linkwarden-pg` | 无 LBrowser；`local/*` |
| `karakeep` public | `karakeep-lbrowser` | LBrowser `serve`；截图/PDF |
| `karakeep` private | 无 | 单镜像；`CRAWLER_STORE_PDF=true` |
| `bookstack` | `bookstack-db` (MariaDB) | DB healthy；`/login` 200 |
| `piwigo` | `piwigo-db` | DB healthy；安装页 |
| `matomo` | `matomo-db` | DB healthy；Web 安装向导 |
| `ente-server` | `ente-pg` + `ente-minio` | PG/MinIO healthy；bucket 手工创建 |
| `penpot-backend` | `penpot-postgres` + `penpot-redis` | 与 frontend 共用 `istore-penpot` 网络 |

检查命令：

```bash
id=joplin-server
/usr/libexec/istorec/$id.sh status-all
/usr/libexec/istorec/$id.sh sidecars
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E "$id|pg|db|redis|minio|lbrowser"
docker logs --tail 80 <sidecar-name>
```

预期：sidecar 先 healthy，主容器再 running；secrets 在 `/etc/istore-loong64/secrets/<id>.env`（0600），不要打印。

### 8.6 manual/设备类应用

| 应用 | 前置条件 | 可自动验证 | 预期判定 |
|---|---|---|---|
| `mihomo` | 配置文件/订阅 | 安装、配置渲染、端口 | 无配置 `PARTIAL`/`BLOCKED` |
| `easytier` | TOML/网络 | 安装、配置渲染 | 无配置 `PARTIAL`/`BLOCKED` |
| `adguardhome` | 53 可用 | Web 3000、DNS 查询 | 与 dnsmasq 冲突则 `BLOCKED` |
| `pihole` | 53/80 可用 | Web/DNS | 与 dnsmasq 冲突则 `BLOCKED` |
| `kopia` | 首启建仓库/账号 | UI 200、Basic 认证 | 未建仓库 `PARTIAL` |
| `typecho` | 首启向导 | 安装页/建管理员 | `PARTIAL` 直到完成向导 |
| `wallabag` | 首启向导 | 安装页/登录 | `PARTIAL` |
| `phpmyadmin` | 外部 MySQL/MariaDB | UI 200 | 无外部 DB `PARTIAL` |
| `rest-server` | htpasswd/仓库 | API/认证 | 无用户 `PARTIAL` |
| `backrest` | 首启建账号/仓库 | UI 200 | `PARTIAL` |
| `bookstack` | MariaDB + artisan 管理员 | `/login` 200 | 未建管理员 `PARTIAL` |
| `matomo` | MariaDB + Web 向导 | 安装页 | `PARTIAL` |
| `zigbee2mqtt` | USB 协调器 `/dev/ttyACM0` | UI/MQTT | 无设备 `BLOCKED`/`NOT TESTED` |
| `smartctl-exporter` | `/dev/sd*`、SYS_RAWIO | `/metrics` 200 | 无设备 `BLOCKED`；USB 桥可能不支持 SMART |
| `scrutiny` | `/dev/sd*`、collector | Web/API | 无设备 `BLOCKED` |
| `go2rtc` | 摄像头/流 | API 1984、端口 | 无流 `PARTIAL`；与 mediamtx 冲突 |
| `mediamtx` | 摄像头/流 | API 9997、端口 | 无流 `PARTIAL`；与 go2rtc 冲突 |
| `headscale` | 域名/HTTPS | CLI/API | 无域名 `PARTIAL`/`BLOCKED` |
| `authelia` | 域名/HTTPS/反代 | 登录页 | 无 HTTPS 域名 `PARTIAL`/`BLOCKED` |
| `woodpecker-server` | Gitea/GitHub forge OAuth | 启动/健康 | 无 forge `BLOCKED` |
| `woodpecker-agent` | server secret + docker.sock | 健康/连接 | 无 server `BLOCKED` |
| `ente-server` | MinIO bucket | API/健康 | 未建 bucket `PARTIAL` |
| `ente-web` | `ENTE_API_ORIGIN` | 静态页/API | 未配 origin `PARTIAL` |
| `wg-easy` | WireGuard 模块/NET_ADMIN | UI 51821、握手 | 无模块 `BLOCKED`；有模块可 `PARTIAL` |
| `unpackerr` | *arr + 路径 | 进程健康 | 无 *arr `PARTIAL`/`NOT TESTED` |
| `caddy` | 默认 Caddyfile | 8080/HTTP 200 | 改配置后 `PARTIAL` |
| `prometheus` | 默认 scrape 配置 | 9090/API | 目标不可达 `PARTIAL` |
| `gatus` | 默认 config | 首页/健康 | 端点未配 `PARTIAL` |
| `alertmanager` | 默认 config | 9093/API | 无告警通道 `PARTIAL` |
| `penpot-frontend` | 与 backend 同网络 | 首页 | 缺 backend `PARTIAL` |
| `linkwarden` public | PG + LBrowser + `/opt/apps/lbrowser` | 注册/书签/截图 | 缺 LBrowser `BLOCKED` |
| `karakeep` public | LBrowser + `/opt/apps/lbrowser` | 首管理员/书签/截图 | 缺 LBrowser `BLOCKED` |

设备检查命令：

```bash
ls -l /dev/ttyACM0 /dev/serial/by-id/* 2>/dev/null
lsmod | grep -E 'wireguard|usbserial|cdc_acm' || true
ip link add wgtest type wireguard 2>/dev/null && ip link del wgtest && echo WG_OK || echo WG_MISSING
smartctl -a /dev/sda 2>&1 | head -40   # 只读；内部盘不做写测试
```

### 8.7 浏览器 UI 证据

- 每个 UI 类应用至少 2 张：登录后首页 + 核心功能页。
- 命名：`evidence/<env>/<app>/ui-login.png`、`ui-core.png`。
- 截图前隐藏/打码密码、token、私人节点地址。
- HTTP 证据：

```bash
mkdir -p evidence/<env>/<app>
URL=http://192.168.100.1:<port>/
curl -sS -D evidence/<env>/<app>/headers.txt -o evidence/<env>/<app>/body.html \
  -w '%{http_code}\n' "$URL" | tee evidence/<env>/<app>/status.txt
sha256sum evidence/<env>/<app>/body.html
```

- API 类至少 3 个端点；记录 method/path/status/关键字段，不记录凭据。

### 8.8 重启持久化

```bash
sync
reboot
# 等待 90–120 秒
ssh -i ~/.ssh/istore-test root@192.168.100.1 \
  'uptime; docker ps; /usr/libexec/istorec/<id>.sh status-all; ls -l /srv/<id>'
```

预期：容器 running；数据文件/数据库记录仍在；LuCI/商店仍可用。若容器未自启：

- 检查 `docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' <container>` 是否 `unless-stopped`；
- 检查 `/etc/init.d/dockerd enabled`；
- 记 P2/P1，不要用“手动 start 成功”冒充“自启通过”。

### 8.9 升级/卸载/数据保留

- 升级：先记录镜像 digest；`/usr/libexec/istorec/<id>.sh pull` + `install`；若 digest 不变，标 `PARTIAL`（没有新镜像可升级）。
- 卸载：`rm` 后 `test -d /srv/<id>`；数据保留为 PASS。
- `purge`：默认不删；只有明确同意删除测试数据时才 `ISTORE_PURGE_DATA=1`。执行前备份证据；purge 不可回退。
- 重装：`install` 后验证原数据仍被使用（数据库/配置文件）。

### 8.10 已知限制负向测试（抽样必做）

| 应用 | 负向测试 | 预期 |
|---|---|---|
| `karakeep` | 不配 Meilisearch，调用搜索 API | 500/明确错误，不是假装成功 |
| `karakeep` public | 不预置 `/opt/apps/lbrowser` | 安装器会拉运行镜像，但浏览器字节缺失导致抓取失败；记录 BLOCKED，不是假 PASS |
| `linkwarden` public | 无 `/opt/apps/lbrowser` | 运行镜像可拉，浏览器字节缺失导致截图/PDF 失败；记录 BLOCKED |
| `openwebui` | 不接外部 LLM | 聊天不可用；UI 200 只能算 PARTIAL |
| `paperless-ngx` | 无 Redis/worker | 文档处理失败；记录依赖缺失 |
| `pihole`/`adguardhome` | dnsmasq 占 53 | 启动失败/端口冲突；不是应用 bug |
| `go2rtc`/`mediamtx` | 同时装 | 8554 冲突；二选一 |
| `wg-easy` | 无 WireGuard 模块 | UI 可开但隧道失败；BLOCKED/PARTIAL |
| `zigbee2mqtt` | 无协调器 | 容器退出；BLOCKED |
| `woodpecker-server` | 无 forge | 无法启动；BLOCKED |
| `scrutiny`/`smartctl-exporter` | USB 桥/无设备 | 无法读 SMART；BLOCKED/PARTIAL |

---

## 9. 证据、结果、报告、state

### 9.1 目录

```text
docs/verification/
  specs/ISTORE-EXECUTION.md              # 本文件
  VERSION-MATRIX.md / .json              # 实际版本
  results/la5/<app>.json                 # la5 机读结果
  results/p1/<app>.json                  # p1 机读结果
  evidence/la5/<app>/...                 # 关键证据（截图/头/日志摘录）
  evidence/p1/<app>/...
  evidence/la5/platform/...
  evidence/p1/platform/...
  reports/ISTORE-LA5.md
  reports/ISTORE-P1.md
  reports/ISTORE-ISOLATION-AUDIT.md
verify/state/istore-la5-exec.yaml
verify/state/istore-p1-exec.yaml
```

设备端原始大日志：

```text
/srv/verify-evidence/la5/<app>/
/srv/verify-evidence/p1/<app>/
```

测试结束前用 `scp -r root@192.168.100.1:/srv/verify-evidence/la5 <Windows xfer-out>` 取回；仓库只放摘要和关键证据，避免膨胀。

### 9.2 结果 JSON 模板

```json
{
  "app": "gogs",
  "env": "la5",
  "batch": "L-B1",
  "verdict": "PASS",
  "severity": "P3",
  "image": "yunixintel/gogs:24.10-la5",
  "digest": "sha256:...",
  "install": {"exit": 0, "status_all": "running"},
  "checks": [
    {"id": "http", "expect": 200, "actual": 200, "evidence": "evidence/la5/gogs/headers.txt"},
    {"id": "core", "expect": "repo create", "actual": "ok", "evidence": "ui-core.png"}
  ],
  "restart": {"container": "running", "data": "kept"},
  "upgrade": {"digest_before": "...", "digest_after": "...", "data": "kept"},
  "uninstall": {"rm": "containers_removed", "data_dir": "kept", "purge": "not_run"},
  "known_limits": ["..."],
  "not_covered": ["..."],
  "evidence_dir": "docs/verification/evidence/la5/gogs/"
}
```

### 9.3 state YAML 模板

`verify/state/istore-la5-exec.yaml`：

```yaml
session: istore-la5-exec
phase: C
env: la5
status: in_progress        # in_progress | blocked | done
firmware:
  tag: 24.10-la5
  image: /mnt/Data/firmware/la5/<...>combined-efi.img.gz
  sha256: "<...>"
  buildinfo: "<...>"
usb:
  device: /dev/sdb
  serial: "<...>"
  size_bytes: <...>
  write_verify: OK
feed:
  base_url: http://192.168.100.2:8000
  public_packages: 115
  public_clean: true
current_batch: L-B1
completed_batches: [L-B0]
failed: []
retest: []
last_completed: "<app/step>"
updated: "2026-10-26T00:00:00Z"
notes: ""
```

`istore-p1-exec.yaml` 同结构，`env: p1`，增加：

```yaml
private:
  p1_md5: "a4d58f827fcb882bb46b9012d185c91e"
  local_images_loaded: [linkwarden-private, karakeep-private]
  default_variant_verified: true
  preset_isolated: true
```

### 9.4 报告模板

`reports/ISTORE-LA5.md` / `ISTORE-P1.md`：

```markdown
# ISTORE-<ENV> 真机报告

## 结论
G2: PASS/PARTIAL/BLOCKED（引用失败项）

## 环境与版本
固件/内核/页大小/Docker/Podman/feed SHA/iStore 版本

## 平台矩阵
逐模块 PASS/PARTIAL/BLOCKED/NOT TESTED + 证据链接

## 批次结果
B0–B5：数量、PASS/PARTIAL/BLOCKED/NOT TESTED、失败清单

## 应用失败清单
app | 批次 | 现象 | 根因 | 证据 | 判定

## 隔离审计
public clean / private default / secret scan

## 证据索引
results/、evidence/、raw logs 路径

## 未测项
每项原因
```

`ISTORE-ISOLATION-AUDIT.md` 单独记录 public/private 审计命令、输出、结论。

### 9.5 提交规则

- 每完成一个批次：写结果、更新 state、写批次摘要，commit。
- 只提交仓库内证据摘要；不提交 `/build`、私有 tar、镜像、密码、token、私人节点地址。
- 提交前：
  ```bash
  git status
  grep -R -I -E 'dckr_pat_|ghp_|github_pat_|BEGIN [A-Z ]*PRIVATE KEY' \
    docs/verification verify/state || true
  ```
- 不把 `results/` 里的真实密码写进去；账号只写 `secret_ref`。

---

## 10. 失败分级与停线

| 级别 | 定义 | 处理 |
|---|---|---|
| **P0 安全/隐私** | 写错盘/内部盘被写、private 泄漏到 public、凭据进 Git、bootloader 损坏 | 立即停线；回退；写事故记录；不得继续测试 |
| **P1 平台阻塞** | 无法启动/SSH/LuCI/opkg/docker/feed；`docker-deps` 缺失；115 卡片不可见 | 暂停该阶段；先修平台；不得把平台问题记成应用失败 |
| **P2 应用失败** | 单应用安装/健康/核心功能/持久化失败 | 记录结果，继续同批；同批 P2 超过 10% 暂停定位 |
| **P3 次要** | 默认图标、文案、布局、非核心功能 | 记录，不阻塞 |

判定映射：

- P0/P1 → `BLOCKED`；
- P2 → `FAIL`/`PARTIAL`（按是否主路径）；
- P3 → `PASS` + note；
- 未执行 → `NOT TESTED` + 原因。

**不要**：

- 失败后无限重试同一命令；最多 2 次，然后记录根因。
- 用 `docker start` 手动拉起后写“自启通过”。
- 用通用 LuCI 页面冒充 iStore 商店。
- 用 QEMU 结果补真机缺口。

---

## 11. 预计工时

| 阶段 | la5 | p1 | 说明 |
|---|---:|---:|---|
| C0/D0 准备（ISO/镜像/tar） | 1.0h | 1.5h | p1 多 private/local 预载 |
| C1/D1 写盘 + 首启 + 基线 | 1.5h | 1.5h | 含串口/LuCI/版本 |
| C2/D2 平台矩阵 | 4.0h | 3.0h | p1 复用部分结论 |
| B0 基础/数据 | 1.5h | 1.5h | 6 应用 |
| B1 单容器低风险 | 8.0h | 8.0h | 42 应用 |
| B2 媒体/下载 | 5.0h | 5.0h | 22 应用 |
| B3 多服务/sidecar | 6.0h | 6.0h | 12 应用 |
| B4 host/特权/反代 | 5.0h | 5.0h | 17 应用 |
| B5 manual/设备/备份 | 4.0h | 4.0h | 16 应用 |
| 复测/报告/隔离审计 | 4.0h | 4.0h | 失败项复测 |
| 恢复 Host A | 0.5h | 0.5h | 关机/内部启动 |
| **合计** | **40.5h** | **40.0h** | 约 5 天/环境（8h/日） |

压缩口径：只跑 83 个 `auto` + 25 manual 的“可自动部分” + 7 needs_config，可压到约 3 天/环境；但最终报告必须列明未覆盖项，不能把压缩写成全量通过。

---

## 12. 风险与回退矩阵

| 风险 | 触发/影响 | 预防 | 回退 |
|---|---|---|---|
| U 盘写错（内部盘） | `dd` 打到 `/dev/sda`/NVMe | guard：`TRAN=usb`、容量、serial、挂载检查；禁止内部设备名 | 立即停止；保留现场；内部盘从备份/快照恢复；P0 |
| 启动失败/无显示 | 无法进 iStoreOS | 写后哈希；串口/iKVM；换 USB 口；确认 UEFI 启动项 | 重刷；内部 NVMe 启动；不改 BIOS 其他项 |
| 内部盘被自动挂载 | iStoreOS block-mount 挂 `/dev/sda1` | 启动后立即 `mount` 检查；记录并 `umount`；禁自动挂载 | 验证 `/mnt/Data` UUID；CasaOS 恢复；不格式化 |
| USB 拔插/掉盘 | 写盘/运行中拔掉 | 写盘/启动中不拔；结束 `poweroff`；`sync` | 重刷；`dmesg` 查 I/O error；必要时 fsck 副本 |
| Docker 拉取失败 | 网络/DNS/429/tag 不存在 | 匿名 manifest 预检；固定 tag；预载 tar；磁盘余量 | 重试 2 次；用 `3.4.2293.2`/`24.22.1`；缺镜像标 BLOCKED |
| 磁盘不足 | 115 镜像/日志占满 overlay | 每应用 `rm`/`image rm`；`df -h` 阈值 5GB；不写内部盘 | 暂停批次；清理测试数据；申请独立盘；不格式化 |
| public 泄漏 private | public feed 含 `local/*`/私人 URL | 构建后 Python 审计；设备端 grep；每次批次前跑 | 阻断发布；重建 feed；重跑审计；P0 |
| 端口冲突 | 53/80/443/8123/8554 | 安装前 `netstat`/`ports`；host 应用逐个 | 停冲突服务/改高位/二选一；记录 PARTIAL |
| 网络网段冲突 | iStoreOS LAN 与实验室 192.168.8.x 冲突 | 隔离直连；PC 静态；不接上游 | 改 LAN/PC 静态；恢复原网络配置 |
| p1 私人预置外联 | EasyTier/mihomo 自启连接私人网 | 串口先查；隔离直连；停/禁自启 | `enable/start` 恢复；只在用户确认后 |
| 凭据进 Git | 密码/token/私钥 | `/build/verify-secrets` 0600；提交前 grep；截图打码 | 立即移除；轮换凭据；P0 |
| 误碰 B 机 sdb | SSH 到 172.16.100.66 操作 | 本规范禁止；所有命令限定 Host A | 停止；按 B 机备份恢复；P0 |

---

## 13. 最终验收清单

- [ ] Loongnix ISO 已保存到 `/mnt/Data/firmware/loongnix25-20260820.iso`，源/文件 SHA 一致，只读挂载见 `live/filesystem.squashfs`。
- [ ] la5 `img.gz` + `sha256sums` 校验通过，`version.buildinfo` 记录。
- [ ] p1 `/build/firmware/personal-p1-20261019.img.gz` 的 SHA/md5/大小记录；与基线不符已查清或 BLOCKED。
- [ ] 58G U 盘写前 guard 通过（`TRAN=usb`、58G 级、serial 记录），写后 `WRITE_VERIFY_OK`。
- [ ] la5/p1 均能 SSH/LuCI，固件版本/kernel/页大小/Docker/Podman 已采集。
- [ ] public feed 115 meta + 1 LuCI；private feed 115 meta + 1 LuCI。
- [ ] public 审计 `PUBLIC_CLEAN`；private Linkwarden/Karakeep `default_variant=private` + `local/*`。
- [ ] 平台矩阵 14 个模块全部有 PASS/PARTIAL/BLOCKED/NOT TESTED 和证据。
- [ ] 115 应用在 la5 与 p1 各有结果 JSON；批次 B0–B5 完成或有明确停线原因。
- [ ] host 网络/端口冲突、sidecar、manual/设备应用、浏览器 UI、重启持久化均有记录。
- [ ] 结果/证据/report/state 路径齐全；无凭据/私人地址进 Git。
- [ ] 测试结束 Host A 内部 NVMe 启动，CasaOS 与 `/mnt/Data` 无损。
- [ ] 最终 G2 结论：PASS/PARTIAL/BLOCKED，未测项列明，不用 QEMU 或“首页 200”冒充。
