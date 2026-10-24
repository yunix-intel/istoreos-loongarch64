# Backrest v1.14.1 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/backrest:loong64` / `:24.10-la5`
- 大小：约 160MB（Hub 压缩）
- digest：`sha256:955cae89f999a900b2d1af1f9270f1ab8f188a836db4339a504dfe56ae4c79eb`
- 版本：Backrest v1.14.1 + restic 0.19.1
- 验证：
  - Web UI `/` 200、健康检查 healthy
  - `restic version` = 0.19.1（linux/loong64）
  - 首次启动完成 SQLite oplog 迁移、auth secret 生成、任务调度
  - 未做实际仓库初始化和备份/恢复（需在 UI 建账号/仓库）

## 构建链路

1. 前端：React/Vite，在 x86 WSL2 用 Node 24 构建 `webui/dist`。
   pnpm 11 会因 `esbuild/@parcel/watcher` 的 build script 报
   `ERR_PNPM_IGNORED_BUILDS`；用 `pnpm install --ignore-scripts` 后
   `pnpm rebuild esbuild @parcel/watcher`，再 `pnpm run build`。
2. 后端：Go 1.27.2，`CGO_ENABLED=0`，`//go:embed dist` 把 UI 编进二进制。
3. restic：源码 v0.19.1，`CGO_ENABLED=0 -tags release` 编 loong64。
4. 运行阶段 openEuler + `ca-certificates tzdata curl shadow util-linux openssh-clients`。
5. 运行用户 `backrest` UID/GID 1108；`/data`、`/config`、`/cache`。

## 遇到的问题

- **pnpm 11 ignored builds**：不批准 `esbuild`/`@parcel/watcher` 的 build script
  会让 `pnpm install` 非零退出；用 `--ignore-scripts` + `pnpm rebuild` 解决。
- **restic 必须在 PATH 且版本匹配**：Backrest 0.19.x 要求 restic 0.19.1；
  镜像把自编 restic 放 `/usr/local/bin/restic`，并设 `BACKREST_RESTIC_COMMAND`。
- **路径**：`BACKREST_DATA=/data`、`BACKREST_CONFIG=/config/config.json`、
  `XDG_CACHE_HOME=/cache`；三者都要持久化。
- **默认无认证**：首次启动生成 auth secret，但需要用户在 UI 创建账号/密码；
  公网必须加反代认证。

## 运行

```bash
docker run -d --name backrest -p 9898:9898 \
  -v backrest-data:/data \
  -v backrest-config:/config \
  -v backrest-cache:/cache \
  yunixintel/backrest:loong64
```

- Web UI：`http://<host>:9898/`。
- 首次打开创建管理员账号；然后添加 restic 仓库（本地路径/S3/SFTP 等）。
- `/data` 存操作日志/索引，`/config` 存配置与 auth secret，`/cache` 存缓存。
- 备份源目录需要额外 `-v` 挂载；容器内路径要出现在仓库/计划里。
- 默认无 TLS；公网放在反代之后。
- 当前只验证到 UI/restic；完整备份/恢复需在 UI 里配置后测试。
