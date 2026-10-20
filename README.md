# iStoreOS for LoongArch64

给龙芯（LoongArch，新 3A5000 / 3A6000）用的 iStore 软路由固件：OpenWrt 官方 loongarch64 底 + iStore 商店插件，完整复刻 x86 版体验。

## 状态

- [x] WSL 交叉编译（la1–la5 连续发版）
- [x] **最新公版：[24.10-la5](https://github.com/yunix-intel/istoreos-loongarch64/releases/tag/24.10-la5)**（内置 docker + podman，英文默认，无私人预置）
- [x] 真机验证（3A6000：LuCI / 商店 / 中文 / EasyTier / Mihomo）
- [x] **62 个 loong64 应用镜像已上架**：[docs/IMAGES.md](docs/IMAGES.md)（`docker pull yunixintel/<app>:loong64`）；含新增 `homer`、`paperless-ngx`、`dashy`、`watchtower`、`changedetection`、`caddy`、`dozzle`、`ntfy`、`gotify`、`node-exporter`、`prometheus`、`pihole`、`gatus`
- [x] podman 全链路（CGO podman + crun，嵌套 `--network=host/none` 跑通）
- [x] dockermanager 可用（连本机 dockerd）
- [x] CasaOS loong64 移植（应用管理/UI/systemd 真机验证；磁盘能力待独占盘）
- [ ] KVM 启动（qemu 10/9.2 均复现中断缺陷，已封存，见 [docs/KVM-PLAN.md](docs/KVM-PLAN.md)）

## 快速用

```bash
# 下载 Release 里的 img.gz，解压后写 U 盘/磁盘
zcat istoreos-*.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
# 启动后浏览器开 http://<网关IP>/ 即 iStore
```

应用镜像示例：

```bash
docker run -d --name memos --network=host -v memos:/opt/memos/data yunixintel/memos:loong64
```

镜像清单与端口/限制见 [docs/IMAGES.md](docs/IMAGES.md)；命名规范见 [docs/NAMING.md](docs/NAMING.md)。

## 文档

- [项目大纲](docs/PROJECT-OUTLINE.md)：目标、交付物、仓库分工、路线
- [固件发布记录](docs/RELEASES.md)：la1–la5/v1 的差异与资产
- [运行手册](docs/RUNBOOK.md)：全部镜像的启动命令、端口、挂载、健康检查
- [镜像构建手册](docs/IMAGE-BUILD.md)：工具链、CGO/glibc、Vite 8 x86 构建、特殊补丁
- [故障排查](docs/TROUBLESHOOTING.md)：现象→原因→修复
- [应用同步清单](docs/APP-SYNC-CHECKLIST.md)：新增镜像必须完成的文档/发布步骤
- [Podman 栈](docs/PODMAN.md)、[CasaOS P3](docs/CASAOS-P3.md)、[EasyTier/mihomo](docs/EASYTIER-MIHOMO.md)
- [OpenCV/SSIM 配方](docs/OPENCV-SSIM.md)、[生产测试计划](docs/PRODUCTION-TEST.md)
- [镜像 Dockerfile 目录](images/)：50 个 Dockerfile + 60 只机读目录

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
