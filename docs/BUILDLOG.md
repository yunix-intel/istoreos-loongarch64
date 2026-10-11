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

## 2026-10-11 第二轮：加商店件（已完成，发版）

- 首版 img（48M）已出，LuCI 中文齐，110 个 ipk，**缺商店**。
- 商店源定位：`luci-app-store`（v0.2.1）+ `taskd`（纯 shell，无编译）+ `luci-lib-taskd` 在 **linkease/istore** 仓库 `luci/` 下；`luci-app-quickstart` + `luci-app-istorex` 在 nas-packages-luci feed。老 `is-opkg` 已被 `taskd` 取代，不用找了。
- 动作：feeds.conf 加 `store`、`nasluci` 两行 → install 五个包 → config 打开 → `make -j32` 增量编。
- 插曲：增量后顶层 `make` 认不出 config 变了（"没活干"退出），显式 `make package/install` + `make target/install` 点名两阶段即过。
- 结果：**完整版 img（50M）+ 商店全进**（rootfs 里 `store.lua`/`istore_backend.lua`/`taskd` + opkg status `luci-app-store 0.2.1-r1`，共 197 个包）。`.manifest` 生成了 0 字节空文件（已知小毛病，以 opkg status 为准）。
- 发版：`v1-loongarch64`，5 个附件（img/rootfs/opkg-feed/sha256sums/version），Release 注明**未在真机验证、求测试**。

## 2026-10-11 Full check（解开 img 逐项验）与首启网络修复

- 分区：GPT + BIOS boot + 16M EFI + 232M rootfs + 2G overlay，标准。
- EFI：`bootloongarch64.efi`。商店：rootfs 含 `store.lua`/`istore_backend.lua`/`taskd`，opkg 登记 197 包、`luci-app-store 0.2.1-r1`。
- **bug：rootfs 无 `/etc/config/`，loongarch64 base-files 缺 x86 的 `board.d/99-default_network`，首启无网。**
- 修：x86 原文件拷入 `target/linux/loongarch64/base-files/etc/board.d/`（见 `patches/99-default_network.loongarch64`），删 `.target_install` 戳后 `make target/install` 重打，复验 rootfs 含该文件。
- Release 已更新 img + sha256sums（17:33 版）。rootfs.tar.gz（LXC 用，走宿主网络）不受影响，未更新。

## 2026-10-11 发版校验乌龙：sha256sums 对不上

- 现象：从 GitHub 下载 img.gz 一验，FAILED。
- 病因：上传的 `sha256sums` 还是首版（17:05）的，没跟着 img 一起更新——发版流程漏了同步校验这步。
- 处理：重生成全量 sums 后发现另一个问题：构建系统的 sums 含未上传的中间文件（buildinfo/kernel.bin），用户一验满屏 FAILED。于是改发**发版专用干净版**（只含 5 个附件），重新上传后下载全量复核通过。
- 教训：发版 checklist 加一条——**sums 必须在所有附件定稿后最后生成**，且只覆盖上传的文件。
