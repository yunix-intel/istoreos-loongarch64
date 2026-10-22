# 原始 iStore 应用中无法移植到 LoongArch64 的条目

本文记录 [STORE-COVERAGE.md](STORE-COVERAGE.md) 中 15 个缺口应用的最终结论。
其中 7 个已构建并推送；下表中 8 个在 2026-10-23 复核后确认**当前没有可靠的
loong64 构建路径**，因此不发布镜像，避免给出“能拉但跑不起来”的假覆盖。

复核方法：

```bash
crane manifest <image>:<tag> | jq '.manifests[].platform'
```

## 结论表

| 应用 | 上游镜像 | 上游架构 | 阻塞原因 | loong64 替代 |
|---|---|---|---|---|
| Emby | `emby/embyserver:latest` | amd64/arm/arm64 | 闭源二进制，无 loong64 版本 | Jellyfin（已发布） |
| Plex | `plexinc/pms-docker:latest` | amd64/arm/arm64 | 闭源二进制，无 loong64 版本 | Jellyfin（已发布） |
| MT Photos | `mtphotos/mt-photos:latest` | amd64/arm64 | 闭源，官方只发 x86/ARM | 无；可用 Immich 类方案但见下 |
| UniFi Controller | `lscr.io/linuxserver/unifi-controller:latest` | amd64/arm64 | Java 可移植，但强依赖 MongoDB；MongoDB 无 loong64，FerretDB 兼容性不足 | 无 |
| Immich | `ghcr.io/immich-app/immich-server:release` | amd64/arm64 | 数据库要求 `pgvecto.rs`/VectorChord 扩展；ML 容器依赖 ONNX Runtime；两者均无 loong64 | 无完整替代 |
| PhotoPrism | `photoprism/photoprism:latest` | amd64/arm64 | 编译期依赖 libvips（`vips.pc`）与 TensorFlow C 头/库；openEuler 24.03 无 `vips-devel`，TensorFlow 无 loong64 | 无 |
| Proxmox VE | iStore 元包 | 仅 x86_64 | `META_ARCH:=x86_64`；PVE 内核/KVM 栈是 x86 虚拟化 | WebVirtCloud（已发布，管理远程 KVM） |
| Ubuntu 桌面 | `linkease/desktop-ubuntu2-standard-amd64` | 仅 amd64 | KasmVNC + Ubuntu 用户态，镜像名即标明 amd64；无 loong64 Kasm 基础镜像 | 无；可用 Loongnix 桌面 + noVNC 自行搭建 |

## 逐项说明

### Emby / Plex / MT Photos

三者都是闭源分发的媒体服务器。Docker Hub 清单只有 `linux/amd64`、
`linux/arm`、`linux/arm64`，没有源码可用于交叉编译。LoongArch64 无法运行
x86 二进制（除非 QEMU 用户态模拟，性能与硬件转码都不可接受，且不满足
“原生 loong64 镜像”的仓库定位）。

**替代**：Jellyfin 已发布 `yunixintel/jellyfin:loong64`，API/Web 均验证通过。

### UniFi Controller

UniFi Network Application 是 Java 应用，理论上 JVM 可跨架构；实际阻塞在数据库：
它要求 MongoDB 3.6–4.4 的 wire protocol 与聚合/事务行为，而 MongoDB 官方没有
loong64 构建。用 FerretDB 把 MongoDB 协议转成 PostgreSQL 看似可行，但 UniFi
使用了大量 FerretDB 未覆盖的命令与索引语义，属于“能启动、不能稳定管理设备”的
状态，因此不发布。

### Immich

Immich v2 的 compose 栈包含：

- `immich-server`：Node/TypeScript，可尝试源码构建；
- `immich-machine-learning`：Python + ONNX Runtime，ONNX Runtime 无 loong64；
- PostgreSQL + `pgvecto.rs`/VectorChord：向量扩展无 loong64 构建；
- Redis。

即使只跑 server 并关闭 ML，数据库扩展仍缺失，迁移会失败。源码移植工作量
远超单个应用镜像，暂不纳入。

### PhotoPrism

Go 主体可以编译，但两个 cgo 依赖无法满足：

```text
# github.com/davidbyttow/govips/v2/vips
Package vips was not found in the pkg-config search path.
# github.com/wamuir/graft/tensorflow
fatal error: tensorflow/c/c_api.h: No such file or directory
```

openEuler 24.03 的 OS/everything 仓库没有 `vips-devel`；TensorFlow 官方不提供
loong64 C 库。关闭 `disable-tensorflow` 只是运行期开关，不能去掉编译期链接。
自行编译 libvips 可行，但 TensorFlow 仍是硬阻塞。

### Proxmox VE

iStore 元包明确写死 `META_ARCH:=x86_64`。PVE 依赖 x86 虚拟化（VT-x/AMD-V）、
x86 内核模块与 QEMU 加速栈，不是“换个基础镜像”能解决的问题。

**替代**：本次发布的 WebVirtCloud 可以在龙芯上作为 libvirt/KVM 的管理面板，
管理远程 x86 KVM 宿主机。

### Ubuntu 桌面

iStore 的 Ubuntu 应用由 `ubuntu2.sh` 部署
`linkease/desktop-ubuntu2-standard-amd64`，即 Kasm Technologies 的
Ubuntu 桌面镜像，只有 amd64。KasmVNC 的服务端组件也没有 loong64 构建。
用 Loongnix/Debian loong64 桌面加 noVNC 可以搭出“网页桌面”，但那不是 Ubuntu，
不应冒充该应用。

## 文档与索引处理

- 这 8 个应用**不写入** `images/catalog.json`、`docs/IMAGES.md`、
  `docs/RUNBOOK.md` 的镜像清单，避免用户误以为可拉取。
- 它们保留在 [STORE-COVERAGE.md](STORE-COVERAGE.md) 的缺口统计中，状态标为
  “blocked（有证据）”。
- 若上游未来发布 loong64 资产或关键依赖（MongoDB、ONNX Runtime、TensorFlow、
  libvips、KasmVNC）出现 loong64 构建，可按本仓库的构建记录重新评估。
