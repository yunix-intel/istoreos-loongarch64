# 路线图（2026-10-18 定版）

## 已完成

- [x] iStore loongarch64 固件（la1/la2/la3/la4/la5 公开发布；la5 内置 docker+podman）
- [x] 真机验证（3A6000 全系统容器：LuCI/中文/三件套）
- [x] 单服务容器（mihomo/easytier sidecar，up.sh/compose）
- [x] 私有库（istore-la-private：模板+脚本+重打流程）
- [x] 多形态发布规范（ghcr/版本对应/红线）
- [x] **六个应用镜像**（jellyfin / navidrome / vaultwarden / uptimekuma / mihomo / easytier），已上架 Docker Hub `yunixintel/*`，见 [IMAGES.md](IMAGES.md)
- [x] **镜像池扩至 42 只**：syncthing、adguardhome、memos、gogs、filebrowser、qbittorrent-ee、it-tools、excalidraw、kopia、linkding、heimdall、nextcloud、typecho、wallabag、drawio、jackett、xteve、one-api、code-server、casaos、dpanel、shiori、jellyseerr、audiobookshelf、calibre-web、homarr、openwebui、kodexplorer、stirling-pdf、wizarr、homeassistant、sonarr、radarr、tautulli、jellystat、prowlarr、bazarr，全部上架（双 tag）；技术栈覆盖 Go/Node/.NET/Rust/C++/Python/PHP
- [x] **CasaOS 评估完成**：代码可编、安装脚本架构误判需补丁、与 iStore 互补不可同装；MVP 2–4 人日，见 [CASAOS-PLAN.md](CASAOS-PLAN.md)
- [x] **dockermanager 点绿**（LuCI 列出宿主容器，零报错；ipk 已进个人版预置）
- [x] **podman 全链路**（CGO podman + conmon/runc/crun + netavark；嵌套 `--network={none,host}` 跑通）
- [x] **固件现已内置 docker + podman**：dockerd/containerd/docker（无 seccomp）+ podman 5.8.8/CGO + crun/conmon/runc + netavark；rootfs 1.5GB，首启 enable dockerd
- [x] 三形态性能对比（mihomo、easytier：延迟/吞吐/稳定性/开销，结论见 BUILDLOG）
- [x] KVM 路线 A 实测（四组合全败，证据链与后续见 [KVM-PLAN.md](KVM-PLAN.md)）
- [x] KVM 路线 B 实测（qemu 9.2 自编，症状完全复现 → 按判据落 D：KVM 封存）
- [x] **jellyfin 缩略图已恢复**：自研 ImageSharp 编码器（缩略图/Trickplay/拼图/BlurHash + Noto CJK），jellyfin:loong64 已替换

## 进行中

- [ ] 个人版 la5 镜像 U 盘真机验证（镜像已在盒子 `/var/tmp/personal-p1-20261019.img.gz`）
- [ ] CasaOS P3 开发完成（systemd/CLI/安装卸载/NBD 磁盘链路）；真实盘验收与上游 PR 待做

## 开发完成后（冻结后执行）

- [ ] **生产级全量测试**：76 镜像逐个业务验证 + 固件真机 + CasaOS 磁盘 + 24h 稳定性，见 [PRODUCTION-TEST.md](PRODUCTION-TEST.md)

## 待排期

- [x] **CasaOS P1+P2 完成**：7 个组件编译、网关/UI 验证、18 应用商店、memos 安装实测；P3（systemd/local-storage 全盘）待排，见 CASAOS-PLAN.md
- [ ] **OpenMediaVault**：列入最后。现实判断：SaltStack+PHP+内核模块链，loong64 上工程浩大；存储管理虽全，但 3A6000 家用场景下 ksmbd + 现有方案已够用。建议：只做可行性调研，不承诺移植。

## 不做

- x86 闭源系（迅雷/emby/plex/微信插件等）：无 loong64 路，判过死刑。
- TrueNAS：FreeBSD 无 LoongArch 移植 + SCALE 只发 x86_64，无解。

## 应用镜像总池（三处来源，去重后逐个打）

原则：同一个应用只打一次，多处复用（iStore 商店 Docker 分类、CasaOS 应用页、OMV-compose 里直接引用）。

- **iStore Docker 应用（49 个，见 dig-store-v3 审计）**：jellyfin✅、navidrome✅（待验证页面细节）、vaultwarden（musl 版编译中）、uptimekuma（子代理在打）。
- **CasaOS 应用市场（bigbear-casaos 约 200+，与 iStore 高度重叠）**：去重后新增候选——AdGuardHome、Pi-hole、Home-Assistant（Python，难）、qBittorrent-Enhanced（已有 -EE 包，可直接转镜像）、Syncthing（Go 单文件，易）、Stirling-PDF（Java，易但镜像大）、Kopia（Go，易）、Wizarr、Homarr/Homer（前端静态，极易）、Jellyseerr（Node，中）、Audiobookshelf（Node，中）、Calibre-Web（Python，中）、FileBrowser（已有 Go 版，极易）、Linkding、Shiori、Wallabag（稍后排）。
- **OMV 插件（NAS 功能型，非容器）**：openmediavault-compose（直接吃我们的 loong64 镜像，无需移植）、KVM 插件（龙芯 KVM 可用但缺验证）、ZFS 插件（ZoL 在 loong64 上可编，中）、sharerootfs/sftp/rsync（官方自带，随发行版走）。
