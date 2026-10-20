# 固件发布记录

公开仓库：https://github.com/yunix-intel/istoreos-loongarch64
所有 Release 资产都可在对应 tag 页面下载；la5 为最新稳定版。

| Tag | 定位 | 主要变化 | 资产 |
|---|---|---|---|
| `v1-loongarch64` | 首个龙芯 iStore 实验版 | 验证 OpenWrt/iStore 在 3A6000 可启动 | img / rootfs / opkg-feed |
| `24.10-la1` | 英文干净版全家桶 | 首个连续编号公版；LuCI/商店基础可用 | img / rootfs / opkg-feed |
| `24.10-la2` | v3 应用源 | 21 个自建 feed 包；opkg 索引 | opkg-feed |
| `24.10-la3` | 商店全量应用源 | 全量 feed；商店应用补齐 | opkg-feed |
| `24.10-la4` | 修复版全家桶 | LuCI 可进、iptables-nft、opkg 源修复 | img / rootfs / opkg-feed |
| `24.10-la5` | docker + podman 容器栈 | dockerd/containerd/docker + podman/crun/conmon/runc/netavark；rootfs 1.5GB | img / rootfs / opkg-feed |

## 版本关系

- 公版 `laN` 连续编号；`la5` 对应 iStoreOS 24.10.8 `r0-fb97140`。
- 私人版 `personal-p1-20261019` 基于同一 `r0-fb97140` 基线，加私人预置；
  只在私有库发布，不在本公开仓库。
- Docker 应用镜像 tag `24.10-la5` 与公版 la5 对齐。

## 下载

在对应 Release 页面下载 `istoreos-...img.gz`、`...rootfs.tar.gz`、`opkg-feed-...tar.gz`
和 `sha256sums`。刷机前校验 `sha256sums`。

历史私有归档：`yunix-intel/istoreos-loongarch64-history`（PRIVATE），仅作旧 git 历史保留。
