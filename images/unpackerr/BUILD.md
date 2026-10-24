# Unpackerr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/unpackerr:loong64` / `:24.10-la5`
- 大小：约 100MB（Hub 压缩；本地 292MB）
- digest：`sha256:8cc802bfdebfa16a355ee05907a2b702477d6033117eead9d009453bea21bc7e`
- 版本：Unpackerr `v0.9.9`（commit `afaf4c6`）
- 验证：
  - 启动日志 `Unpackerr v0.9.9 Starting!`
  - 首次启动自动生成 `/config/unpackerr.conf`
  - 配置假 Sonarr 后进程持续运行并轮询（连接拒绝为预期）
  - `unrar 7.13`、`7za 16.02` 可用；`pgrep` 健康检查 `healthy`

## 构建链路

1. Go 1.27.2，`CGO_ENABLED=0`，`go build .`，加版本 ldflags：
   ```
   -X golift.io/version.Version=0.9.9 -X golift.io/version.Revision=1
   ```
2. **必须升级 `golang.org/x/sys`**：v0.0.0-20211216 没有 loongarch64 的
   `ztypes_linux.go`，编译报 `undefined: Cmsghdr/Timespec/SockaddrStorage`。
   补丁见 [`patches/unpackerr-xsys.patch`](patches/unpackerr-xsys.patch)（升到 v0.35.0）。
3. 运行阶段 openEuler + `ca-certificates tzdata bash shadow util-linux procps-ng p7zip`；
   `unrar` 7.1.10 由构建阶段源码编。
4. 非 root 用户 `unpackerr` UID/GID 1123。

## 运行时契约

- **无 Web 端口、无 UI**；只通过 `UN_*` 环境变量或 `/config/unpackerr.conf` 配置。
- 卷：`/config`（配置）、`/downloads`（必须与 *arr 的完成目录同一路径/同一挂载）。
- 首次启动把示例配置复制到 `/config/unpackerr.conf`，之后不会覆盖。
- 常用环境变量示例：
  ```
  UN_SONARR_0_URL=http://sonarr:8989
  UN_SONARR_0_API_KEY=...
  UN_SONARR_0_PATHS_0=/downloads
  UN_RADARR_0_URL=http://radarr:7878
  UN_RADARR_0_API_KEY=...
  UN_RADARR_0_PATHS_0=/downloads
  ```
- 健康检查是 `pgrep -f /usr/local/bin/unpackerr`，只证明进程存在，不证明 *arr 可达。

## 遇到的问题

- **x/sys 无 loongarch64 定义**：旧依赖直接编译失败；升级到 v0.35.0 解决。
- **版本号为空**：不加 ldflags 时日志显示 `Unpackerr v Starting!`；补
  `golift.io/version.Version` 后正常。
- **配置路径**：指定不存在的 `--config` 时程序会回退到默认路径创建；entrypoint
  先复制示例到 `/config/unpackerr.conf`，保证位置可控且可写。
- **无 HTTP 健康端点**：只能用进程检查。

## 限制

- 未连接真实 Sonarr/Radarr，未验证解压→通知→删除完整链路。
- `unrar` 为闭源 freeware；也可只用 7za，但部分 RAR5 特性依赖 unrar。
- 目录映射必须与 *arr 容器完全一致，否则找不到文件。

## 运行

```bash
docker run -d --name unpackerr \
  -v /srv/unpackerr:/config \
  -v /srv/downloads:/downloads \
  -e UN_SONARR_0_URL=http://sonarr:8989 \
  -e UN_SONARR_0_API_KEY=*** \
  -e UN_SONARR_0_PATHS_0=/downloads \
  yunixintel/unpackerr:loong64
```
