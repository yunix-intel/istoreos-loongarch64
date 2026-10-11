# 构建日志

## 2026-10-11（首次构建，进行中）

- 环境：WSL2 Ubuntu（x86_64），32 核 / 60GB，`wsl -u root` 装依赖（`build-essential libncurses-dev gawk unzip flex gettext` 等），构建本身用普通用户跑。
- 源码：`git clone --depth 1 https://github.com/istoreos/istoreos.git`（commit 见 `src-version.txt`，构建机 `~/istore-la-build/`）。
- 配置：`config/loongarch64-generic.config` → `make defconfig`（TARGET=loongarch64/generic，内核 6.6，LuCI 中文 + kmod-tun；商店包名待 feeds 列出后核对）。
- 命令：`make -j32`，日志 `~/istore-la-build/build-full.log`，后台跑。
- 待填：toolchain 结果、内核结果、首个报错（如有）。

## 2026-10-11 14:3x 排障：kernel.org 下载卡死

- 现象：构建 1.5h 无进展，负载~0，卡在 `toolchain/kernel-headers`，`dl/linux-6.6.144.tar.xz.dl` 在 cdn.kernel.org 上以 ~17KB/s 蠕动。
- 处理：清华镜像（`mirrors.tuna.tsinghua.edu.cn/kernel/`，实测 5.3MB/s）12 秒下完 140MB 整包放到 `dl/`；kill 掉残留 curl 后 download.pl 验 hash 通过（证明镜像站文件与官方 bit 一致），构建继续推进到 musl/gcc-final。
- 教训：开编前先把 `dl/` 大包（kernel/gcc/binutils）用国内镜像预下好；以后构建机放一份 `mirror=Math` 说明。另：`pkill` 匹配串要用 `[c]dn...` 写法，否则会杀掉自己所在的 `bash -lc`（已踩）。
