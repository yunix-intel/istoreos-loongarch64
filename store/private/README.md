# 私人版 / 公开版浏览器接入

## 结论

- **私人版**：LBrowser 作为本地 embedded sidecar 内置，不依赖宿主安装；
  镜像只在本机构建，**不得推送 Docker Hub**（deb 无明确再分发许可）。
- **公开版**：应用镜像不含浏览器；运行时挂载宿主 `/opt/apps/lbrowser:ro`，
  使用 `yunixintel/lbrowser-runtime:3.4.2293.2` sidecar（已发布，不含浏览器字节）。
- 两种方式的 Playwright/Patchright 能力一致；差异是体积、宿主依赖与更新方式。

## 私人版构建

```bash
cd images/lbrowser
./build.sh embedded
# 生成 local/lbrowser-embedded:3.4.2293.2-local（约 1.49GB，仅本地）
```

## 私人版 compose

- [compose/linkwarden-private.yml](compose/linkwarden-private.yml)
- [compose/karakeep-private.yml](compose/karakeep-private.yml)

两个文件都用 `local/lbrowser-embedded:3.4.2293.2-local`，浏览器在容器内，
不需要宿主 `/opt/apps/lbrowser`。

## 公开版 compose

- [links.json](links.json)：私人/公开的镜像与商店源对照
- [compose/linkwarden-public.yml](compose/linkwarden-public.yml)
- [compose/karakeep-public.yml](compose/karakeep-public.yml)

两个文件都用 `yunixintel/lbrowser-runtime:3.4.2293.2` + 宿主挂载，应用镜像保持
`yunixintel/linkwarden:24.10-la5` / `yunixintel/karakeep:24.10-la5`。

## 注意

- embedded 镜像包含浏览器字节，只允许私人使用；公开仓库/商店不能分发。
- 两种 sidecar 都需要 `--shm-size=1g`。
- LBrowser DevTools 只绑 `127.0.0.1`，sidecar 内部用 `cdp-proxy.mjs` 暴露 9222。
- 私人版升级浏览器需要重建 embedded 镜像；公开版更新宿主 LBrowser 包即可。
