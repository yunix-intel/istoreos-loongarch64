# 构建日志

## 2026-10-11 首次构建（toolchain→内核→包→组装，一次通过，除两个环境坑）

- 环境：WSL2 Ubuntu（x86_64），32 核 / 60GB，`wsl -u root` 装依赖（`build-essential libncurses-dev gawk unzip flex gettext` 等），构建本身用普通用户跑。
- 源码：`git clone --depth 1 https://github.com/istoreos/istoreos.git`（分支 istoreos-24.10，commit 见构建机 `~/istore-la-build/src-version.txt`）。
- 配置：`config/loongarch64-generic.config` → `make defconfig`（TARGET=loongarch64/generic，内核 6.6，LuCI 中文 + kmod-tun）。
- 结果：157 个包零编译错误；toolchain + 内核 6.6 + LuCI 全绿。

## 排障 1：kernel.org 下载卡死

- 现象：构建 1.5h 无进展，负载~0，卡在 `toolchain/kernel-headers`，`dl/linux-6.6.144.tar.xz.dl` 在 cdn.kernel.org 上以 ~17KB/s 蠕动。
- 处理：清华镜像（`mirrors.tuna.tsinghua.edu.cn/kernel/`，实测 5.3MB/s）12 秒下完 140MB 整包放到 `dl/`；kill 残留 curl 后 download.pl 验 hash 通过，构建继续。
- 教训：开编前先把 `dl/` 大包用国内镜像预下好；`pkill` 匹配串用 `[c]dn...` 写法，否则杀掉自己的 `bash -lc`（已踩）。

## 排障 2：package/install 挂（WSL PATH 污染）

- 现象：`make[2] package/install Error 1`，定格 rootfs 打包后处理。
- 病因：`find ... -execdir touch` 拒绝执行——WSL 继承的 Windows PATH 含 `Files/Git/mingw64/bin`（相对路径残留），GNU find 认为不安全。跟龙芯、代码无关。
- 处理：构建 shell 首行 `export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`，断点续跑即过。

## 2026-10-11 第二轮：加商店件（已完成，发版 v1）

- 首版 img（48M）已出，LuCI 中文齐，110 个 ipk，**缺商店**。
- 商店源定位：`luci-app-store`（v0.2.1）+ `taskd`（纯 shell，无编译）+ `luci-lib-taskd` 在 **linkease/istore** 仓库 `luci/` 下；`luci-app-quickstart` + `luci-app-istorex` 在 nas-packages-luci feed。老 `is-opkg` 已被 `taskd` 取代，不用找了。
- 动作：feeds.conf 加 `store`、`nasluci` 两行 → install 五个包 → config 打开 → `make -j32` 增量编。
- 插曲：增量后顶层 `make` 认不出 config 变了（"没活干"退出），显式 `make package/install` + `make target/install` 点名两阶段即过（先删 `.target_install` 戳）。
- 结果：**完整版 img（50M）+ 商店全进**（rootfs 里 `store.lua`/`istore_backend.lua`/`taskd` + opkg status `luci-app-store 0.2.1-r1`，共 197 个包）。`.manifest` 生成了 0 字节空文件（已知小毛病，以 opkg status 为准）。
- 发版：`v1-loongarch64`，5 个附件（img/rootfs/opkg-feed/sha256sums/version），Release 注明**未在真机验证、求测试**。

## 2026-10-11 Full check（解开 img 逐项验）

- 分区：GPT + BIOS boot + 16M EFI + 232M rootfs + 2G overlay，标准。
- EFI：`bootloongarch64.efi`。商店：rootfs 含 `store.lua`/`istore_backend.lua`/`taskd`，opkg 登记 197 包。
- **bug：rootfs 无 `/etc/config/`，loongarch64 base-files 缺 x86 的 `board.d/99-default_network`，首启无网。**
- 修：x86 原文件拷入 `target/linux/loongarch64/base-files/etc/board.d/`（见 `patches/99-default_network.loongarch64`），删戳后 `make target/install` 重打，复验 rootfs 含该文件。
- Release 已更新 img + sha256sums（17:33 版）。rootfs.tar.gz（LXC 用，走宿主网络）不受影响，未更新。

## 2026-10-11 发版校验乌龙：sha256sums 对不上

- 现象：从 GitHub 下载 img.gz 一验，FAILED。
- 病因：上传的 `sha256sums` 还是首版（17:05）的，没跟着 img 一起更新——发版流程漏了同步校验这步。
- 处理：改发**发版专用干净版**（只含 5 个附件），重新上传后下载全量复核通过。
- 教训：发版 checklist 加一条——**sums 必须在所有附件定稿后最后生成**，且只覆盖上传的文件。

## 2026-10-11 发版全量复核通过

- 从 GitHub 把 5 个附件全下回来逐字节验：img.gz / rootfs.tar.gz / opkg-feed / version.buildinfo **全部 OK**。
- 备注：Release 大文件 CDN 到本机约 130KB/s，135M 下了约 20 分钟；以后传包按此规划。

## 2026-10-12 第三轮：三件套（Tailscale / EasyTier / OpenClash）

- Tailscale：feed 版 Go staging 在 LA 上坏掉（`no Go files`）→ 宿主 Go 1.26 `GOARCH=loong64` 直编（`tailscaled` 33M + CLI 20M，`file` 实锤 ELF LoongArch 静态链接）→ 本地 bin 包。坑：goproxy 官方走不动切国内源；`/tmp` 会被清，二进制放持久目录；tarball 打完当场 `tar tz` 验（吃过 20 字节空包的亏）。
- EasyTier：官方 loongarch64 包直装，三个入门税——空 `Build/Compile`、unzip 残留预清理、zip 顶层目录落点（`PKG_BINDIR`）。`--config-file` 经 strings 实锤支持，init 优先 TOML。
- OpenClash：feed 直装（`luci-app-openclash_0.47.156`），纯 Lua/shell；mihomo 内核运行时替换（官方 loong64 abi2，静态链接已验）。
- 通病记录：feeds 增删包后必 `grep .config` 确认符号、清 `tmp/info` 残留元数据；`make -j32` 认不出变更就点名阶段（`package/install` + `make target/install`，先删戳）。

## 2026-10-12 v2 双版与 24.10-la1 发版

- 三件套全进（tailscale/easytier/openclash + store），另修：dnsmasq 二选一（留 -full）、rootfs 分区提到 512M、quickstart/istorex 因 DEPENDS 写死 x86/ARM 拿掉。
- v2-personal（本机，109M）：EasyTier 整网 TOML + verge 配置（Meta/1500/双 mesh DIRECT 置顶）+ mihomo 内核 + 中文默认 + 三件套自启，解包复验全在。永不上传。
- v2-public（`24.10-la1`）：同底、无预置、英文默认。发版前审计：解包 grep 密钥/域名/IP 全空；rootfs.tar.gz 与 opkg-feed 同查，v2preset ipk 已剔除。5 附件已传。
