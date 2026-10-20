# 命名与版本规范（2026-10-19 定稿）

## 1. 固件公版

- Tag 形如 **`24.10-laN`**，N 从 1 连续递增，不跳号。
- 当前已发：`24.10-la1`、`24.10-la2`、`24.10-la3`、`24.10-la4`、`24.10-la5`；下一个公版为 `24.10-la6`。
- `v1-loongarch64` 为早期实验版，保留作历史，不再沿用该命名。
- 只有**用公版 config 构建、无任何私人预置**的产物才能占用 `laN`；发布到 GitHub Releases。
- Release 标题：`24.10-laN：<一句话摘要>`；附件固定 5 件（img.gz / rootfs.tar.gz / opkg-feed / sha256sums / version.buildinfo）；`sha256sums` 在所有附件定稿后最后生成。

## 2. 私人构建

- 文件名形如 **`personal-pN-YYYYMMDD.img.gz`**（当前 `personal-p1-20261019.img.gz`）。
- 历史版本放 `archive/`，命名 `personal-archive-YYYYMMDD.img.gz`。
- pN 独立计数，从 p1 起；**永不上 GitHub、永不用 `laN`**。
- 私人目录：本机 `outputs/istore-la-private/`（gitignore）与盒子 `/var/tmp/`，不进公开仓库。

## 3. Docker 镜像（Docker Hub）

- 仓库：`yunixintel/<app>`。
- Tag：
  - **`loong64`**：浮动最新（推荐日常使用）。
  - **`24.10-laN`**：对应固件公版基线；仅在该公版已发布后使用。
- 镜像只发布 loong64 单架构；x86/ARM 不适用。
- **Docker 镜像没有"私人版"**：镜像本身不含任何私人配置（mihomo/easytier 配置运行时挂载）。私人内容只存在于本地固件与本地容器镜像（如 `istore:personal`），后者永不推送。
- 当前 36 只镜像已带 `24.10-la5` 标签，对应已发布的 `24.10-la5` 公版基线。
- CasaOS 镜像在磁盘能力验证完成前**不发布**（当前已撤下）。

## 4. CasaOS

- 安装包：`casaos-pN-loong64-x.y.z.tar.gz`；镜像：`yunixintel/casaos:loong64`。
- 发布前置条件：应用管理/UI/systemd **与 local-storage 磁盘能力**全部真机验证通过。
- 发布位置：GitHub Releases（独立 tag `casaos-x.y.z`），与固件版本分开。

## 5. 临时文件与构建产物

- 本机 `outputs/xfer-out/` 仅作中转，任务结束即清理；不存放唯一副本。
- 盒子 `/var/tmp/appimages/` 保留各应用构建上下文（可复现）；旧内核/旧私人镜像/工具链 tarball 用完即删。
- 发布产物只认 GitHub Releases / Docker Hub 两处；本地目录不是发布源。
