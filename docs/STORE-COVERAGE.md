# 原始 iStore 商店覆盖率（133 app-meta）

对照源：[STORE-APP-LIST.md](STORE-APP-LIST.md)。统计时间：2026-10-22。

口径：只统计原始商店 133 个 app-meta；我们的 79 个 Docker 镜像中，有一批是商店之外的补充应用。

## 总览

- 原始商店：**133** 个 app-meta
- 可用：**113**；死刑：**20**；待定：**0**
- 已有 Docker 镜像覆盖：**22**
- 固件内原生/LuCI 应用（不需要镜像）：**76**
- 容器/混合、需逐条确认：**4**（`owntone`、`pve`、`ubuntu`、`hermes`）
- **确认还差的容器应用：11；若 4 个待确认项也按容器计，最多 15**
- 我们的镜像池共 79 个，其中商店之外的应用：**57** 个

## 已覆盖的 22 个

| iStore 应用 | 我们的镜像 |
|---|---|
| `codeserver` | `yunixintel/code-server` |
| `dpanel` | `yunixintel/dpanel` |
| `drawio` | `yunixintel/drawio` |
| `excalidraw` | `yunixintel/excalidraw` |
| `gogs` | `yunixintel/gogs` |
| `heimdall` | `yunixintel/heimdall` |
| `homeassistant` | `yunixintel/homeassistant` |
| `homebox` | `yunixintel/homebox` |
| `ittools` | `yunixintel/it-tools` |
| `jackett` | `yunixintel/jackett` |
| `jellyfin` | `yunixintel/jellyfin` |
| `kodexplorer` | `yunixintel/kodexplorer` |
| `memos` | `yunixintel/memos` |
| `navidrome` | `yunixintel/navidrome` |
| `nextcloud` | `yunixintel/nextcloud` |
| `oneapi` | `yunixintel/one-api` |
| `openwebui` | `yunixintel/openwebui` |
| `qbittorrent-ee` | `yunixintel/qbittorrent-ee` |
| `typecho` | `yunixintel/typecho` |
| `uptimekuma` | `yunixintel/uptimekuma` |
| `vaultwarden` | `yunixintel/vaultwarden` |
| `xteve` | `yunixintel/xteve` |

## 还差的 11 个容器应用

| iStore 应用 | 说明 | 结论 |
|---|---|---|
| `chinesesubfinder` | Go，需 qBittorrent 等配套，可移植 | 可做 |
| `emby` | 闭源二进制，无 loong64 | 阻塞 |
| `immich` | ML/ONNX 无 loong64，完整版受阻；可做无 ML 精简版 | 受限 |
| `lanraragi` | Perl + Redis 可选，可移植 | 可做 |
| `mtphotos` | 闭源/仅 x86/ARM 镜像，无源码 | 阻塞 |
| `mymind` | 上游闭源/无 loong64，待确认 | 待确认 |
| `penpot` | Clojure/Java + PostgreSQL + Redis，工程量大 | 可评估 |
| `photoprism` | TensorFlow/ONNX，loong64 受阻 | 受限 |
| `plex` | 闭源二进制，无 loong64 | 阻塞 |
| `unifi` | Java Controller + MongoDB，工程量大 | 可评估 |
| `webvirtcloud` | Python/Django + libvirt，可移植 | 可做 |

## 76 个固件内原生/LuCI 应用（不需要 Docker 镜像）

`51ddns`, `airplay2`, `alist`, `aliyundrive-webdav`, `ap-modem`, `arcadia`, `aria2`, `arpbind`, `autotimeset`, `clouddrive2`, `cloudreve`, `cpulimit`, `ddnsgo`, `demon`, `diskman`, `dockermanager`, `emmc-health`, `eqos`, `feishunet`, `floatip`, `frpc`, `frps`, `gowebdav`, `hd-idle`, `htreader`, `istoredup`, `istorepanel`, `istorerouter`, `istorex`, `lan-scanner`, `lan-wake`, `lingti-gameacc`, `luci-app-picoclaw`, `lucky`, `mfun`, `miair-next`, `modem`, `msd_lite`, `multiaccountdial`, `natpierce`, `netdata`, `nginx`, `nlbwmon`, `npc`, `nps`, `nut`, `openclawmgr`, `openfog`, `openlist`, `poweroff`, `pushbot`, `rclone`, `rebatedog`, `rtbwmon`, `rtp2httpd`, `runmynas`, `serverchan`, `sftp`, `shadowrt`, `smartdns`, `socat`, `sunpanel`, `syncdial`, `systools`, `tailscale`, `transmission`, `udpxy`, `uhttpd`, `ups-manager`, `vlmcsd`, `vsftpd`, `wan-mac`, `webcontrol`, `xlnetacc`, `xunlei`, `zerotier`

> 这些应用由 la5 固件 feed/LuCI 提供，或已经是系统标配；不应按“缺镜像”计算。

## 4 个待确认的容器/混合应用

`owntone`、`pve`、`ubuntu`、`hermes` 在 iStore 里可能是原生包、容器或混合形态；
需要核对 app-meta 定义后再决定是否补镜像。


## 结论

- 按原始商店口径，113 个可用应用中，镜像覆盖 22 个；剩下 91 个里 76 个是固件原生应用、4 个待确认、**11 个确认需要补容器镜像（最多 15）**。
- 11 个中可优先做的是 `chinesesubfinder`、`lanraragi`、`webvirtcloud`；`penpot`/`unifi` 可评估；`immich`/`photoprism` 受 ML 限制；`emby`/`plex`/`mtphotos`/`mymind` 受闭源或架构限制。