# LoongArch 基础层：sharp 与浏览器

本页记录两个可复用基础层。它们不是普通应用，商店不直接展示。

## 1. `yunixintel/node-sharp`（已发布）

| 项 | 值 |
|---|---|
| 镜像 | `yunixintel/node-sharp:24.22.1` / `:loong64` |
| digest | `sha256:b7dd366c629d363df4d8737317f8425478eb770b52c50fbca4bab332a5c49f49` |
| 大小 | 446MB（本地）/ 约 150MiB（Hub） |
| 组件 | Node 24.22.1、libvips 8.18.7、sharp 0.35.5 |
| 验证 | `sharp.versions` 正确；resize + WebP/JPEG/PNG 输出非空；`ldd` 无缺失 |

用途：Karakeep、Linkwarden、Joplin 等依赖 sharp 的 Node 应用，不再各自编 libvips。

复用方式：

```dockerfile
# 方式 A：直接作为基础镜像
FROM yunixintel/node-sharp:24.22.1

# 方式 B：复制到现有 Node 镜像
COPY --from=yunixintel/node-sharp:24.22.1 /opt/vips /opt/vips
COPY --from=yunixintel/node-sharp:24.22.1 /opt/node_modules/sharp /opt/node_modules/sharp
ENV NODE_PATH=/opt/node_modules \
    LD_LIBRARY_PATH=/opt/vips/lib \
    SHARP_FORCE_GLOBAL_LIBVIPS=1
```

限制：只启用 JPEG/PNG/WebP/TIFF/EXIF/LCMS；HEIF/JXL/PDF/SVG 未启用。
详细记录见 [../images/node-sharp/BUILD.md](../images/node-sharp/BUILD.md)。

## 2. LBrowser / Playwright 基础层（本地，不发布）

**许可证不清晰，禁止再分发。** 包内没有 LICENSE/COPYING/copyright，
只有 upstream Chromium 的 SPDX 表达式，不能视为 Loongson 的再分发授权。
因此 Docker Hub 上没有 `yunixintel/lbrowser`。

本地构建：

```bash
cd images/lbrowser
./build.sh mount      # 运行时镜像，不含浏览器字节
./build.sh embedded   # 仅本地测试，内含浏览器，禁止分发
```

浏览器从宿主挂载：

```bash
docker run --rm --shm-size=1g \
  -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  local/lbrowser-runtime:3.4.2293.2 \
  /opt/apps/lbrowser/lbrowser --version
```

### 嵌入 vs 挂载

| 方式 | 体积 | 依赖 | 分发 | 更新 |
|---|---|---|---|---|
| 宿主挂载 `/opt/apps/lbrowser:ro` | 运行时层 1.03GB + 宿主 370MB | 宿主已安装 LBrowser | 不分发浏览器字节 | 宿主包更新 |
| 嵌入镜像（本地） | 1.49GB | 无宿主依赖 | 许可证不清晰，禁止公开分发 | 重建镜像 |
| 外部 browserless | 应用镜像小 | 需另一台机器 | 外部服务 | 独立更新 |

嵌入镜像已实测 Playwright 1.57（含 PDF）与 Patchright 1.59 全过；技术上可行，
但多约 370MB 且浏览器安全更新滞后。正式商店仍用宿主挂载或 sidecar。

### 实测结果

- Playwright 1.57.0：`goto`、`content()`、`screenshot()`、`pdf()` 全过；
  Chromium 138.0.7204.310。
- Patchright 1.59.4：`launch/goto/content/screenshot` 通过；PDF 未测。
- 跨 Docker NAT 的 `connectOverCDP`：两种引擎都通过。

### 浏览器能力（2026-10-25 复验）

- WebGL1/2 可用（ANGLE + SwiftShader，软件渲染）。
- 视频：VP8/Vorbis、H.264/AAC 播放/seek/截图通过；HEVC/Theora/AC-3 不支持。
- DRM：Widevine 不可用；ClearKey 可用。Netflix/Spotify 等不可用。
- 非 root：uid 1000 + `--no-sandbox` 可运行，需可写 `/tmp` 与输出目录。
- 稳定性：20 标签 × 60 轮、1200 次 goto+截图，0 失败，峰值 1.66 GiB。
- 只读根：必须配可写 `/tmp`（tmpfs）或 TMPDIR/HOME。

详见 [../docs/research/verify-lbrowser.md](research/verify-lbrowser.md)。

### Linkwarden 接入

```yaml
services:
  lbrowser:
    image: local/lbrowser-runtime:3.4.2293.2
    command: ["serve"]
    shm_size: "1g"
    volumes:
      - /opt/apps/lbrowser:/opt/apps/lbrowser:ro
  linkwarden:
    environment:
      PLAYWRIGHT_WS_URL: http://lbrowser:9222
```

- `PLAYWRIGHT_WS_URL` 实际走 `connectOverCDP`，写 `http://` 而不是 `ws://`。
- 也可以让 worker 直接拉起挂载的 LBrowser：
  `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH=/opt/apps/lbrowser/lbrowser`。

### Karakeep 接入

```yaml
services:
  chrome:
    image: local/lbrowser-runtime:3.4.2293.2
    command: ["serve"]
    shm_size: "1g"
    volumes:
      - /opt/apps/lbrowser:/opt/apps/lbrowser:ro
  web:
    environment:
      BROWSER_WEB_URL: http://chrome:9222
      CRAWLER_HEADLESS_BROWSER: "true"
```

- Karakeep 的 Patchright 使用 `BROWSER_WEB_URL` + `connectOverCDP`；
  不要把它指向 `BROWSER_WEBSOCKET_URL`（那是 Playwright server 协议）。
- 不需要归档时可完全不配浏览器，书签 CRUD 正常，截图/PDF 标记 unavailable。

### 注意

- 必须 `--shm-size=1g`（至少 512MB）。
- LBrowser DevTools 只监听 `127.0.0.1`；跨容器必须走 `cdp-proxy.mjs` 改写 URL，
  直接映射 9222 连不上。
- 无 GPU；截图/PDF 走软件渲染；WebGL/视频/DRM 未验证。
- 完整依赖、测试和未验证项见 [../images/lbrowser/BUILD.md](../images/lbrowser/BUILD.md)。
