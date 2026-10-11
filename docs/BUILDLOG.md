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

## 2026-10-11 第二轮：加商店件（进行中）

- 首版 img（`istoreos-loongarch64-*-combined-efi.img.gz`，48M）已出，LuCI 中文齐，110 个 ipk，**缺商店**。
- 商店源定位：`luci-app-store`（v0.2.1）+ `taskd`（纯 shell，无编译）+ `luci-lib-taskd` 在 **linkease/istore** 仓库 `luci/` 下；`luci-app-quickstart` + `luci-app-istorex` 在 nas-packages-luci feed。老 `is-opkg` 已被 `taskd` 取代，不用找了。
- 动作：feeds.conf 加 `store`、`nasluci` 两行 → install 五个包 → config 打开 → `make -j32` 增量编（toolchain 现成，只编新包+重组装）。
