# 项目大纲：iStoreOS for LoongArch64

## 1. 目标

在龙芯 3A5000/3A6000（LoongArch64）上提供一套可日常使用的软路由/NAS 软件栈：

1. **iStoreOS 固件**：OpenWrt 底 + iStore 商店，公版 `laN` 连续发版，私人版 `personal-pN-YYYYMMDD`。
2. **应用镜像池**：`yunixintel/*:loong64`，覆盖媒体、下载、网盘、开发、监控、通知、NAS 工具。
3. **CasaOS 侧应用面板**：Debian/systemd 形态，与 iStoreOS 互补，不同装。
4. **容器栈**：dockerd/containerd/docker CLI + podman/crun/conmon/netavark + dockerman。
5. **网络组件**：EasyTier 组网、mihomo 代理，固件/容器/全系统三种形态。
6. **可复现文档**：构建配方、启动手册、故障排查、验证证据全部入库。

## 2. 交付物

| 交付物 | 位置 | 状态 |
|---|---|---|
| 公版固件 la5 | GitHub Release `24.10-la5` | 已发布 |
| 私人固件 p1 | 私有库 `/build/firmware/personal-p1-20261019.img.gz` | 已构建，U 盘待验 |
| 62 个应用镜像 | Docker Hub `yunixintel/*` | 已推送，生产级全量测试待做 |
| CasaOS P3 安装包 | 私有库 `casaos-p3/` + 构建机 tarball | 功能验证完成，真实盘待验 |
| Podman/dockerman | la5 固件内 | 已真机验证 |
| EasyTier/mihomo | 私有库模板 + 固件 feed | 已做稳定性/性能测试 |
| KVM 方案 | `docs/KVM-PLAN.md` | 判定封存（中断缺陷） |
| 文档体系 | 本仓库 `docs/` | 持续同步 |

## 3. 仓库分工

- **公开库** `yunix-intel/istoreos-loongarch64`：固件源码/config/patches/feeds-pkg、应用
  Dockerfile/构建配方、运行手册、故障排查、构建日志、路线图。
- **私有库** `yunix-intel/istore-la-private`：私人固件重打脚本、EasyTier/mihomo 模板、
  CasaOS P3 材料、推送脚本；真实配置/密钥不入库。
- **Docker Hub** `yunixintel/*`：镜像本体；仓库描述指向公开文档。

## 4. 文档地图

| 文档 | 内容 |
|---|---|
| [IMAGES.md](IMAGES.md) | 60 个镜像的清单、大小、验证、限制 |
| [RUNBOOK.md](RUNBOOK.md) | 启动命令、端口、挂载、健康检查、启动注意 |
| [IMAGE-BUILD.md](IMAGE-BUILD.md) | 每个镜像的构建方式、工具链、特殊补丁 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 现象→原因→修复，按前端/CGO/应用/浏览器/容器分类 |
| [BUILDLOG.md](BUILDLOG.md) | 按日期的完整构建/踩坑时间线 |
| [RELEASES.md](RELEASES.md) | la1–la5/v1 的定位、差异与 Release 资产 |
| [NAMING.md](NAMING.md) | 固件/镜像/私有版本命名规则 |
| [PODMAN.md](PODMAN.md) | podman/crun/dockerman 栈与 OpenWrt 打包坑 |
| [CASAOS-P3.md](CASAOS-P3.md) | CasaOS 组件、补丁、安装/运行、磁盘验证 |
| [EASYTIER-MIHOMO.md](EASYTIER-MIHOMO.md) | 组网/代理的容器与固件运行方式、密钥政策 |
| [OPENCV-SSIM.md](OPENCV-SSIM.md) | cv2/numpy/SSIM 可复用配方 |
| [KVM-PLAN.md](KVM-PLAN.md) | KVM 路线与封存依据 |
| [PRODUCTION-TEST.md](PRODUCTION-TEST.md) | 开发冻结后的全量生产测试计划 |
| [GAPS.md](GAPS.md) / [ROADMAP.md](ROADMAP.md) | 缺口盘点与路线图 |
| [../images/](../images/) | 50 个 Dockerfile + 60 只机读目录 `catalog.json` |
| [APP-SYNC-CHECKLIST.md](APP-SYNC-CHECKLIST.md) | **新增/更新应用的强制同步清单** |
| [PRIVACY-REVIEW.md](PRIVACY-REVIEW.md) | 转公开前的隐私/历史/大文件审计清单 |

## 5. 新应用的强制同步流程

从今天起，每新增或更新一个应用镜像，必须完成
[APP-SYNC-CHECKLIST.md](APP-SYNC-CHECKLIST.md) 的全部条目，才算“完成”：

1. 可复现构建材料（Dockerfile 或明确配方）
2. 启动手册（端口/挂载/环境/健康检查/注意事项）
3. 新踩的坑写入 TROUBLESHOOTING 与 BUILDLOG
4. 更新 IMAGES 清单、catalog.json、README 计数
5. 打双 tag、推送、Hub 架构/标签校验
6. 记录验证证据（命令、日志、HTTP/健康状态）

禁止只推镜像不写文档；禁止把真实密钥/节点地址写入公开库。

## 6. 当前状态（2026-10-20）

- 固件：la1–la5 连续发版；la5 内置 docker+podman；私人 p1 已构建。
- 镜像：62 个仓库，全部 `loong64` + `24.10-la5`；新增 homer、paperless-ngx、dashy、
  watchtower、changedetection、caddy、dozzle、ntfy、gotify、node-exporter、prometheus、pihole、gatus。
- CasaOS P3：systemd/CLI/安装卸载、NBD 挂载/卸载/重启自挂/格式化通过；真实盘待验。
- Podman：host/none 网络真机通过；bridge 需宿主 nft_conntrack。
- 已知缺口：CasaOS 真实盘 SMART/USB、固件 U 盘首启、生产级全量测试、10 个早期镜像
  未保留 Dockerfile（配方已补）。

## 7. 下一步

1. Pi-hole 生产化：gravity/adlists、上游 DNS/DHCP、重启持久化验证。
2. CasaOS 真实盘验证后解禁发布。
3. p1/la5 U 盘真机首启验证。
4. 开发冻结后执行 PRODUCTION-TEST。
