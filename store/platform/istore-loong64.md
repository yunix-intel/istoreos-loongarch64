# iStoreOS 龙芯版说明（商店/详情页文案源）

适用：公版 `24.10-la5`（公开）与私人 `personal-p1-20261019`（私有）。
状态：固件已发布/已构建；商店条目仍在最后同步阶段。

## 卡片文案（zh-CN）

**iStoreOS for LoongArch64（龙芯版）**

基于 OpenWrt 24.10 与 iStoreOS 24.10.8 的龙芯固件，面向 3A5000/3A6000，
提供 LuCI、iStore 商店、Docker/Podman 容器栈与 LoongArch 应用镜像源。

龙芯版说明：
- 仅支持 `loongarch64`；x86/ARM 的 ipk、Docker 镜像与安装包不能直接使用。
- 公版 la5 对应 iStoreOS `24.10.8 r0-fb97140`；应用镜像 tag `24.10-la5` 与固件对齐。
- 内置 dockerd/containerd/docker CLI，以及 podman/crun/conmon/runc/netavark；
  Podman 的 bridge 网络需要宿主提供 `nft_conntrack`。
- iStore 中的应用来自本仓库适配的 `yunixintel/*:loong64` 镜像，不使用上游 x86/ARM 镜像。
- 商店条目会显式标注“龙芯版说明”：架构、与上游的行为差异、缺失功能、外部依赖。

缺失/受限功能：
- 原始 iStore 133 个应用并非全部可移植：8 个有明确阻塞证据（Emby、Plex、MT Photos、
  UniFi、Immich、PhotoPrism、PVE、Ubuntu），其余由固件原生包或 LoongArch 镜像覆盖。
- 部分应用需要额外容器/服务（PostgreSQL、MariaDB、Redis、MinIO 等），商店会以
  多容器或依赖说明呈现，不承诺“单容器即开即用”。
- 依赖闭源 x86 工具链、Prisma/ONNX/TensorFlow 等组件的应用不提供。
- 私人版会预置私有配置/源；公开版不包含任何私人节点、密钥或凭据。

额外依赖/注意：
- 首次启动后请先确认 WAN/LAN 与软件源，再安装商店应用。
- 安装前检查端口冲突（商店会显示宿主端口）；不要与宿主 dnsmasq 抢 53 端口。
- 应用数据默认位于 `/DATA/AppData/<app>`（CasaOS 兼容布局）或 Docker 卷，卸载前先备份。

## Card text (en-US)

**iStoreOS for LoongArch64**

LoongArch firmware based on OpenWrt 24.10 and iStoreOS 24.10.8 for 3A5000/3A6000,
with LuCI, the iStore, Docker/Podman, and a LoongArch image feed.

LoongArch-specific notes:
- `loongarch64` only; x86/ARM ipks, images, and installers are not usable.
- Public la5 tracks iStoreOS `24.10.8 r0-fb97140`; image tag `24.10-la5` matches the firmware.
- Docker and Podman stacks are included; Podman bridge networking needs host `nft_conntrack`.
- Store apps use `yunixintel/*:loong64` images built by this project, not upstream x86/ARM images.
- Every store card discloses architecture, behavior differences, missing features, and external dependencies.

Missing/limited:
- Not all 133 original iStore apps are portable; eight have documented blockers
  (Emby, Plex, MT Photos, UniFi, Immich, PhotoPrism, PVE, Ubuntu).
- Some apps require sidecars (PostgreSQL, MariaDB, Redis, MinIO) and are documented as such.
- Apps that depend on closed x86 toolchains or Prisma/ONNX/TensorFlow are not provided.
- The private build may include private feeds/config; the public build contains no private credentials.

Dependencies/notes: verify WAN/LAN and package feeds after first boot; check host port conflicts;
back up app data before uninstalling.
