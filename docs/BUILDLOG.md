# 构建日志

## 2026-10-11（首次构建，进行中）

- 环境：WSL2 Ubuntu（x86_64），32 核 / 60GB，`wsl -u root` 装依赖（`build-essential libncurses-dev gawk unzip flex gettext` 等），构建本身用普通用户跑。
- 源码：`git clone --depth 1 https://github.com/istoreos/istoreos.git`（commit 见 `src-version.txt`，构建机 `~/istore-la-build/`）。
- 配置：`config/loongarch64-generic.config` → `make defconfig`（TARGET=loongarch64/generic，内核 6.6，LuCI 中文 + kmod-tun；商店包名待 feeds 列出后核对）。
- 命令：`make -j32`，日志 `~/istore-la-build/build-full.log`，后台跑。
- 待填：toolchain 结果、内核结果、首个报错（如有）。
