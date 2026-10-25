# 私人版 / 公开版浏览器接入

## 结论

- **私人版**：LBrowser 直接烘进应用单镜像（Linkwarden/Karakeep），同容器内运行，
  不依赖 sidecar 或宿主安装。只在本机构建，**不得推送 Docker Hub / 公共 registry**。
- **公开版**：应用镜像不含浏览器；挂载宿主 `/opt/apps/lbrowser:ro`，使用
  `yunixintel/lbrowser-runtime:3.4.2293.2` sidecar（已发布，不含浏览器字节）。
- 两种方式能力一致；差异是体积、宿主依赖与更新方式。

## 私人版构建

```bash
# 1) 本地 embedded 浏览器（含浏览器字节，仅本地）
cd images/lbrowser && ./build.sh embedded
# 2) 私人单镜像
cd ../linkwarden && ./build-private.sh     # local/linkwarden-private:2.16.3-p1
cd ../karakeep  && ./build-private.sh      # local/karakeep-private:0.34.1-p1
```

要求已存在公共基线镜像 `yunixintel/linkwarden:2.16.3` / `yunixintel/karakeep:0.34.1`。
`build-private.sh` 只允许 `local/*` 镜像名，防止误推公共 Hub。

## 私人单镜像实测

| 应用 | 镜像 | 体积 | 实测 |
|---|---|---|---|
| Linkwarden | `local/linkwarden-private:2.16.3-p1` | 2.07GB | 99 迁移、`/` 200、注册登录、example.com 截图/PDF/Readability/preview、重启幂等 |
| Karakeep | `local/karakeep-private:0.34.1-p1` | 2.34GB | 健康 200、注册登录、Wikipedia 截图+PDF+HTML+banner、重启持久化/再抓取 |

两者均无 sidecar、无宿主挂载，`--shm-size=1g`；均未推送。

## 私人版 compose

- [compose/linkwarden-private.yml](compose/linkwarden-private.yml)：PostgreSQL + 单镜像
- [compose/karakeep-private.yml](compose/karakeep-private.yml)：单镜像（SQLite）

两个文件都只引用 `local/*-private`，没有浏览器 sidecar、没有宿主挂载。
运行时仍需 `shm_size: "1g"`。

## 公开版 compose

- [links.json](links.json)：私人/公开的镜像与商店源对照
- [compose/linkwarden-public.yml](compose/linkwarden-public.yml)
- [compose/karakeep-public.yml](compose/karakeep-public.yml)

两个文件都用 `yunixintel/lbrowser-runtime:3.4.2293.2` + 宿主挂载，应用镜像保持
`yunixintel/linkwarden:24.10-la5` / `yunixintel/karakeep:24.10-la5`。

## CasaOS 私人商店定义

- [../casaos-private/Apps/linkwarden/docker-compose.yml](../casaos-private/Apps/linkwarden/docker-compose.yml)
- [../casaos-private/Apps/karakeep/docker-compose.yml](../casaos-private/Apps/karakeep/docker-compose.yml)

两份定义复用公开卡片的 `x-casaos` 元数据，但镜像改为 `local/*-private`、去掉
`DISABLE_BROWSER`（Linkwarden）并设置 `shm_size: 1g`；已通过 CasaOS dry-run。
只应导入私人 CasaOS 实例，不能与公开商店同时安装同名应用。

## 注意

- embedded/private 镜像包含浏览器字节，只允许私人使用；公开仓库/商店不能分发。
- 两种方式都需要 `--shm-size=1g`。
- LBrowser DevTools 只绑 `127.0.0.1`；公开版 sidecar 内部用 `cdp-proxy.mjs` 暴露 9222，
  私人版 Karakeep 在同一容器内启动浏览器 + 代理。
- 私人版升级浏览器需要重建应用镜像；公开版更新宿主 LBrowser 包即可。
