# 原始 iStore 商店覆盖率（133 app-meta）

对照源：[STORE-APP-LIST.md](STORE-APP-LIST.md)。统计时间：2026-10-23。

口径：只统计原始商店 133 个 app-meta。仓库镜像池包含一批商店之外的补充应用，
因此“镜像数”与“商店覆盖数”不是同一个数字。

## 总览

- 原始商店：**133** 个 app-meta
- 可用：**113**；死刑：**20**；待定：**0**
- 已有 Docker 镜像覆盖：**29**（原 22 + 本轮 7）
- 固件内原生/LuCI 应用（不需要镜像）：**76**
- 确认阻塞、无可靠 loong64 路径：**8**
- 确认还差且可做：**0**
- 我们的镜像池共 **87** 个镜像（新增 8 个：7 个应用，Penpot 拆 backend/frontend）

## 本轮新增的 7 个应用

| iStore 应用 | 镜像 | 状态 |
|---|---|---|
| `chinesesubfinder` | `yunixintel/chinesesubfinder` | 已发布，UI/健康检查通过 |
| `lanraragi` | `yunixintel/lanraragi` | 已发布，UI/Redis/健康检查通过 |
| `owntone` | `yunixintel/owntone` | 已发布，Web/健康检查通过 |
| `mymind` | `yunixintel/mymind` | 已发布，静态站点/健康检查通过 |
| `webvirtcloud` | `yunixintel/webvirtcloud` | 已发布，登录页/静态资源/健康检查通过 |
| `penpot` | `yunixintel/penpot-backend` + `yunixintel/penpot-frontend` | 已发布，迁移/绘图 API/健康检查通过 |
| `hermes` | `yunixintel/hermes` | 已发布，WebUI/健康检查通过 |

构建细节见各自 `images/<app>/BUILD.md`。

## 已覆盖的 29 个

| iStore 应用 | 我们的镜像 |
|---|---|
| `chinesesubfinder` | `yunixintel/chinesesubfinder` |
| `codeserver` | `yunixintel/code-server` |
| `dpanel` | `yunixintel/dpanel` |
| `drawio` | `yunixintel/drawio` |
| `excalidraw` | `yunixintel/excalidraw` |
| `gogs` | `yunixintel/gogs` |
| `heimdall` | `yunixintel/heimdall` |
| `hermes` | `yunixintel/hermes` |
| `homeassistant` | `yunixintel/homeassistant` |
| `homebox` | `yunixintel/homebox` |
| `ittools` | `yunixintel/it-tools` |
| `jackett` | `yunixintel/jackett` |
| `jellyfin` | `yunixintel/jellyfin` |
| `kodexplorer` | `yunixintel/kodexplorer` |
| `lanraragi` | `yunixintel/lanraragi` |
| `memos` | `yunixintel/memos` |
| `mymind` | `yunixintel/mymind` |
| `navidrome` | `yunixintel/navidrome` |
| `nextcloud` | `yunixintel/nextcloud` |
| `oneapi` | `yunixintel/one-api` |
| `openwebui` | `yunixintel/openwebui` |
| `owntone` | `yunixintel/owntone` |
| `penpot` | `yunixintel/penpot-backend` + `yunixintel/penpot-frontend` |
| `qbittorrent-ee` | `yunixintel/qbittorrent-ee` |
| `typecho` | `yunixintel/typecho` |
| `uptimekuma` | `yunixintel/uptimekuma` |
| `vaultwarden` | `yunixintel/vaultwarden` |
| `webvirtcloud` | `yunixintel/webvirtcloud` |
| `xteve` | `yunixintel/xteve` |

## 8 个阻塞应用

证据与替代方案见 [BLOCKED-APPS.md](BLOCKED-APPS.md)。

| iStore 应用 | 阻塞原因 |
|---|---|
| `emby` | 闭源二进制，上游仅 amd64/arm/arm64 |
| `immich` | 需要 VectorChord/pgvecto.rs + ONNX Runtime，均无 loong64 |
| `mtphotos` | 闭源，上游仅 amd64/arm64 |
| `photoprism` | 编译期依赖 libvips 与 TensorFlow C 库，均无 loong64 |
| `plex` | 闭源二进制，上游仅 amd64/arm/arm64 |
| `pve` | `META_ARCH:=x86_64`，PVE 内核/KVM 为 x86 虚拟化 |
| `ubuntu` | Kasm Ubuntu 镜像仅 amd64，KasmVNC 无 loong64 |
| `unifi` | 强依赖 MongoDB，MongoDB 无 loong64 |

## 76 个固件内原生/LuCI 应用（不需要 Docker 镜像）

`51ddns`, `airplay2`, `alist`, `aliyundrive-webdav`, `ap-modem`, `arcadia`, `aria2`, `arpbind`, `autotimeset`, `clouddrive2`, `cloudreve`, `cpulimit`, `ddnsgo`, `demon`, `diskman`, `dockermanager`, `emmc-health`, `eqos`, `feishunet`, `floatip`, `frpc`, `frps`, `gowebdav`, `hd-idle`, `htreader`, `istoredup`, `istorepanel`, `istorerouter`, `istorex`, `lan-scanner`, `lan-wake`, `lingti-gameacc`, `luci-app-picoclaw`, `lucky`, `mfun`, `miair-next`, `modem`, `msd_lite`, `multiaccountdial`, `natpierce`, `netdata`, `nginx`, `nlbwmon`, `npc`, `nps`, `nut`, `openclawmgr`, `openfog`, `openlist`, `poweroff`, `pushbot`, `rclone`, `rebatedog`, `rtbwmon`, `rtp2httpd`, `runmynas`, `serverchan`, `sftp`, `shadowrt`, `smartdns`, `socat`, `sunpanel`, `syncdial`, `systools`, `tailscale`, `transmission`, `udpxy`, `uhttpd`, `ups-manager`, `vlmcsd`, `vsftpd`, `wan-mac`, `webcontrol`, `xlnetacc`, `xunlei`, `zerotier`

> 这些应用由 la5 固件 feed/LuCI 提供，或已经是系统标配；不应按“缺镜像”计算。

## 结论

- 按原始商店口径，113 个可用应用中：**29 个有 loong64 镜像**、**76 个由固件原生提供**、
  **8 个有明确技术阻塞**。
- 15 个原缺口应用已全部处理：7 个完成并发布，8 个给出可复现的阻塞证据。
- 阻塞项如果未来出现 loong64 的 MongoDB / ONNX Runtime / TensorFlow / libvips /
  KasmVNC 或上游闭源镜像，可按 [BLOCKED-APPS.md](BLOCKED-APPS.md) 重新评估。
