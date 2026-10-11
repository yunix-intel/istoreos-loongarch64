# iStoreOS for LoongArch64

给龙芯（LoongArch，新 3A5000 / 3A6000）用的 iStore 软路由固件：OpenWrt 官方 loongarch64 底 + iStore 商店插件，完整复刻 x86 版体验。

## 状态

- [ ] WSL 交叉编译验证
- [ ] KVM 启动验证
- [ ] LuCI / 商店 / 中文验证
- [ ] Mihomo + EasyTier 验证
- [ ] 首个 Release 发布

## 快速用（等 Release）

```bash
# 龙芯机 / KVM 里，刷 combined-efi.img，浏览器开网关 IP 即 iStore
```

## 自己编（WSL2 Ubuntu，x86_64 主机交叉编译）

```bash
./scripts/build-wsl.sh   # 整编：toolchain + 内核 + 全系统 + 商店插件
```

详见 [docs/BUILD.md](docs/BUILD.md)，构建问题记 [docs/BUILDLOG.md](docs/BUILDLOG.md)。

## 仓库结构

```
config/    .config 基线（TARGET=loongarch64/generic，内核 6.6）
scripts/   一键构建脚本（WSL 可用）
patches/   LA 编译修复（每个 patch 注明原因，同步向上游提 PR）
files/     ImageBuilder/固件预置（LAN 配置、opkg 源、uci-defaults 首次启动）
docs/      构建文档 + 构建日志 + 刷机教程
```

## 上游

- 固件源码：https://github.com/istoreos/istoreos（官方树自带 `target/linux/loongarch64`）
- OpenWrt 官方 LA 镜像/软件源：https://downloads.openwrt.org/releases/24.10.2/（`targets/loongarch64` + `packages/loongarch64_generic`）

## 联系 / 反馈

- 报 bug、求适配：[Issues](https://github.com/yunix-intel/istoreos-loongarch64/issues)（附板子型号 + 日志）
- 问问题、交流：[Discussions](https://github.com/yunix-intel/istoreos-loongarch64/discussions)
- 要新功能：直接提 PR

## License

GPL-3.0（与 OpenWrt / iStoreOS 一致）
