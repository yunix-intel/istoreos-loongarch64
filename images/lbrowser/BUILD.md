# LoongArch64 LBrowser / Playwright 基础层

## 结论

- **许可证不清晰，禁止再分发，未推送 Docker Hub。**
- 可用的本地交付方式是：运行时镜像只装依赖，运行时把宿主的
  `/opt/apps/lbrowser` 以只读方式挂进容器。
- 本地镜像：
  - `local/lbrowser-runtime:3.4.2293.2` / `:loong64`
    - ID `sha256:ed9deac552b747c2909888ebe1aa210960608d4dfada023aee8fa74f010f10a2`
    - 大小 1,102,858,036 B（约 1.03 GiB），`linux/loong64`
    - 不含 LBrowser 文件，只含 openEuler 运行库、Node、CDP 代理和入口脚本。
  - `local/lbrowser-embedded:3.4.2293.2-local`（仅本地测试，禁止分发）
    - ID `sha256:f34d87bf757d5d62c5a9f3ef4028f21c02d6c0b5d187b034c5761b3fd00362ab`
    - 大小 1,489,767,588 B（约 1.39 GiB），`linux/loong64`
    - 内含解包后的 LBrowser 370 MB。
- 没有 Registry digest，因为两种镜像都没有 push。

## 许可证核查

核查对象：

- `lbrowser_3.4.2293.2-1.stable_loong64.deb`
- `dpkg-deb -I` 的 control 字段
- deb payload（`dpkg-deb -c` / `dpkg-deb -x`）
- 已安装的 `/opt/apps/lbrowser` 与 `/usr/share/doc/lbrowser`

结果：

- control 只有 `Package/Version/Depends/Description` 等字段，没有
  `License`、`Copyright` 或 `Homepage` 授权声明。
- deb payload **没有** `LICENSE`、`COPYING`、`copyright`、`NOTICE` 或 EULA；
  `/usr/share/doc/lbrowser/` 只有 `changelog.gz`。
- `/opt/apps/lbrowser/lbrowser.sh` 和 `postinst` 里保留了 Chromium 的
  “BSD-style license found in the LICENSE file”，但包内并没有这个 LICENSE 文件。
- `/usr/share/appdata/lbrowser.appdata.xml` 有：
  `project_license = BSD-3-Clause and LGPL-2.1+ and Apache-2.0 and IJG and MIT and GPL-2.0+ and ISC and OpenSSL and (MPL-1.1 or GPL-2.0 or LGPL-2.0)`。
  这是上游 Chromium 组件许可证的 SPDX 表达式，不等于 Loongson 对整包再分发的明确授权，
  也没有随包提供各许可证文本和 copyright 清单。

因此按“许可证不清晰”处理：**不推送任何含 LBrowser 的镜像；应用侧改为宿主挂载。**
`local/lbrowser-runtime` 虽然不含 LBrowser 字节，也按保守策略不推送，避免被误当成可直接分发的浏览器镜像。

如后续 Loongnix 提供明确的再分发许可与完整 notices，可用
`INSTALL_LBROWSER=1` 构建内置镜像，再按
`yunixintel/lbrowser:loong64` / `:3.4.2293.2` 推送；当前不做。

## 版本与校验和

| 组件 | 版本 | 说明 |
|---|---|---|
| LBrowser deb | `3.4.2293.2-1.stable` | `loong64` |
| Chromium | `138.0.7204.310` | Playwright `browser.version()` 与 `Browser.getVersion` 一致 |
| 基础镜像 | `yunixintel/node:24.22.1` | ID `sha256:906a4264d6e6...`，Node 24.22.1 / npm 11.19.1 |
| 运行时 OS | openEuler 24.03 LTS-SP4 | glibc 2.38 |

deb 来源：

```text
https://pkg.loongnix.cn/loongnix/25/pool/main/l/lbrowser/lbrowser_3.4.2293.2-1.stable_loong64.deb
SHA-256 2ecfb08bd35b0aadf13bc2d09ac35175d9825caf3c82d0859e5acb00b7dd5b6a
大小    100,355,388 B
```

Dockerfile 的 embedded 分支会在解包前执行 `sha256sum -c`；不匹配则构建失败。

## 运行时依赖

openEuler 24.03 软件包：

```text
alsa-lib at-spi2-atk at-spi2-core avahi-libs ca-certificates cairo
cups-libs dbus-libs expat fontconfig freetype gdk-pixbuf2 glib2
gnutls gtk2 gtk3 iproute kmod-libs krb5-libs libX11 libXcomposite
libXcursor libXdamage libXext libXfixes libXi libXinerama libXrandr
libXrender libatomic libdrm libffi libjpeg-turbo libpng libstdc++
libxcb libxkbcommon mesa-libgbm nspr nss pango pcre2 pulseaudio-libs
systemd-libs tzdata dejavu-fonts google-noto-sans-cjk-sc-fonts
```

- 已用 `ldd /opt/apps/lbrowser/lbrowser` 检查，容器内无 `not found`。
- 额外装了 DejaVu + Noto Sans CJK SC，避免中文页面截图出现方块。
- 没有 GPU 直通；Chromium 走 SwiftShader/软件渲染即可完成截图和 PDF。
- `dpkg` 只出现在构建 embedded 载荷的临时阶段，最终镜像不装 `dpkg`/Perl。

## 构建

```bash
cd images/lbrowser

# 推荐：不含浏览器载荷，运行时挂载宿主 LBrowser
./build.sh mount

# 仅本地测试：下载 deb、校验 SHA-256、解包到 /opt/apps/lbrowser
./build.sh embedded
```

`build.sh` 使用 `DOCKER_BUILDKIT=0` 和 `--network=host`，与仓库其它 LoongArch 镜像一致。

Dockerfile 结构：

1. `lbrowser-deb` 阶段：默认只创建空目录；`INSTALL_LBROWSER=1` 时安装
   `dpkg`、下载 deb、校验、`dpkg-deb -x`。
2. 运行阶段：安装运行库；从上一阶段复制 `/opt/apps/lbrowser/`（默认空）；
   复制 `cdp-proxy.mjs` 和 `docker-entrypoint.sh`；设置
   `PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH=/opt/apps/lbrowser/lbrowser`。

## 用法

### 直接启动浏览器

```bash
docker run --rm \
  -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  --shm-size=1g \
  local/lbrowser-runtime:3.4.2293.2 \
  /opt/apps/lbrowser/lbrowser --version
# LBrowser 3.4.2293.2
```

### Node/Playwright 直接拉起

```js
import { chromium } from 'playwright-core';

const browser = await chromium.launch({
  executablePath: '/opt/apps/lbrowser/lbrowser',
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
```

注意：`PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH` 不是 Playwright 自身的变量。
Linkwarden 会读取它并转成 `executablePath`；Playwright core 不会自动读取。
因此直接用 Playwright/Patchright 时必须显式传 `executablePath`。

### 作为远程 CDP 浏览器（Linkwarden/Karakeep sidecar）

```bash
docker run -d --name lbrowser \
  --shm-size=1g \
  -p 9222:9222 \
  -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  local/lbrowser-runtime:3.4.2293.2 serve
```

- `serve` 启动无头 LBrowser，并启动 CDP 反向代理，监听 `0.0.0.0:9222`。
- LBrowser 138 即使传 `--remote-debugging-address=0.0.0.0` 也只绑定
  `127.0.0.1`；`cdp-proxy.mjs` 负责监听 `0.0.0.0`、转发到
  `127.0.0.1:9223`，并改写 `/json/version`、`/json/list` 中的
  `webSocketDebuggerUrl`，否则跨容器连接会指向错误地址。
- 已验证在 Docker bridge/NAT 下，`http://host.docker.internal:19222`
  可被 Playwright 和 Patchright 的 `connectOverCDP` 使用。

## 测试记录（2026-10-25，Host A / loong64）

测试环境：`local/lbrowser-runtime:3.4.2293.2` + 只读挂载宿主
`/opt/apps/lbrowser`；`--network=host`、`--shm-size=1g`。
测试项目为临时 npm 项目，`playwright-core@1.57.0`、`patchright@1.59.4`。

### Playwright 1.57.0

```json
{
  "browserVersion": "138.0.7204.310",
  "status": 200,
  "title": "Example Domain",
  "contentBytes": 2373,
  "screenshotBytes": 89886,
  "pdfBytes": 92439,
  "pdfSupported": true,
  "errors": []
}
```

- `goto('https://example.com')`：成功，HTTP 200。
- `content()`：成功，内容包含 `Example Domain`。
- `screenshot()`：成功，PNG 89,886 B。
- `pdf()`：成功，`%PDF-` 魔数正确，92,439 B。
- 内置镜像分支也跑过同一测试，结果一致（PDF 同样通过）。

### Patchright 1.59.4

```json
{
  "browserVersion": "138.0.7204.310",
  "status": 200,
  "title": "Example Domain",
  "contentBytes": 2373,
  "screenshotBytes": 89886,
  "errors": []
}
```

- 兼容，launch/goto/content/screenshot 全部通过。
- Patchright 的 PDF 未测试（本次不要求）；其底层仍走 Chromium CDP，
  预期可用但未作为结论。

### CDP 远程连接（跨 Docker NAT）

`local/lbrowser-embedded:3.4.2293.2-local serve` + `-p 19222:9222`，
客户端使用 `connectOverCDP('http://host.docker.internal:19222')`：

```json
{
  "engine": "playwright-core",
  "browserVersion": "138.0.7204.310",
  "status": 200,
  "title": "Example Domain",
  "contentBytes": 2373,
  "screenshotBytes": 89863,
  "errors": []
}
```

Patchright 走同一 CDP 端点也通过（`engine: "patchright"`，其余字段相同）。
这验证了 Karakeep 的 `BROWSER_WEB_URL` 和 Linkwarden 的
`PLAYWRIGHT_WS_URL`（其实现实际调用 `connectOverCDP`）所需的协议路径。

## 接入方式

### Linkwarden

推荐直接挂载并让 worker 自己拉起 LBrowser：

```yaml
services:
  linkwarden:
    volumes:
      - /opt/apps/lbrowser:/opt/apps/lbrowser:ro
    environment:
      PLAYWRIGHT_LAUNCH_OPTIONS_EXECUTABLE_PATH: /opt/apps/lbrowser/lbrowser
      # 可选：BROWSER_TIMEOUT / BROWSER_LIFECYCLE
```

如果 Linkwarden 容器不能直接执行宿主的 LBrowser（不同 libc/架构隔离），
改用 sidecar：

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

注意：

- Linkwarden 的 `PLAYWRIGHT_WS_URL` 实际传给 `chromium.connectOverCDP`，
  因此写 `http://...`，不要写 `ws://...`。
- `DISABLE_BROWSER=true`（或 `DISABLE_PRESERVATION=true`）会跳过网页保存/
  截图/PDF，不是“使用外部浏览器”的开关；仅在完全不需要保留功能时使用。
- 直连模式要求 Linkwarden 镜像本身是 loong64 且能访问挂载路径。

### Karakeep

当前 Karakeep 使用 `BROWSER_WEB_URL`，不是 `PLAYWRIGHT_WS_URL`：

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

- Karakeep 的 crawler 用 Patchright `connectOverCDP` 连接
  `BROWSER_WEB_URL`；已用 Patchright 跨 NAT 验证。
- `BROWSER_WEBSOCKET_URL` 是 Playwright server 协议（`chromium.connect`），
  不是原始 CDP；不要把它指向本 sidecar 的 9222。
- 旧文档/旧版本可能提到 `PLAYWRIGHT_WS_URL`；当前源码的 schema 是
  `BROWSER_WEB_URL` / `BROWSER_WEBSOCKET_URL`。
- `CRAWLER_HEADLESS_BROWSER` 默认已是 `true`，显式写出便于审计。

## 体积、无头与跨 NAT 注意事项

- 镜像体积（未压缩、本地）：
  - runtime：1,102,858,036 B（1.03 GiB）
  - embedded：1,489,767,588 B（1.39 GiB）
- LBrowser 载荷：约 370 MB（`/opt/apps/lbrowser`），deb 96 MB。
- 必须加 `--shm-size=1g`（或至少 512 MB）；默认 64 MB 的 `/dev/shm`
  在复杂页面/多标签下容易崩溃。启动参数已带 `--disable-dev-shm-usage` 兜底。
- 以 root 运行时 Chromium 需要 `--no-sandbox`；`serve` 模式已包含。
  若改成非 root，建议保留 `--no-sandbox` 并确认挂载目录可读。
- 无头模式使用 `--headless=new`；Playwright 直接 launch 时由 Playwright
  传入无头参数，测试已通过。
- LBrowser 的 DevTools 只监听 `127.0.0.1`，跨容器必须走 `cdp-proxy.mjs`；
  直接用 `-p 9222:9222` 暴露原始 9222 是连不上的。
- 代理会改写 JSON 中的 host:port；WebSocket upgrade 原样转发。
  如果放在反向代理/Ingress 后面，需允许 WebSocket upgrade 并保持长连接。
- 未启用 GPU；截图/PDF 走软件渲染。需要 WebGL/视频解码的场景需另行验证。
- 时区/语言：镜像设置 `LANG=C.UTF-8`；页面 locale 由浏览器默认值决定，
  如需固定可在 launch/context 里设置 `locale`、`timezoneId`。

## 未验证

- Linkwarden / Karakeep 的完整业务链路（创建书签、实际归档、PDF 入库）。
  本次验证到浏览器核心与 CDP 连接层。
- 非 root 用户、只读根文件系统、SELinux/AppArmor 限制下的运行。
- WebGL、视频、DRM、GPU 加速、大页面/长时间多标签稳定性。
- `lbrowserdriver_3.4.2293.2` 包（未安装、未测试）。
- Docker Hub 推送、Registry digest、跨架构 manifest；本次按许可证结论不推送。
- Patchright 的 PDF 输出。

## 文件

- `Dockerfile`：两阶段；默认无浏览器载荷，`INSTALL_LBROWSER=1` 为本地测试分支
- `build.sh`：`mount` / `embedded` 构建入口
- `docker-entrypoint.sh`：默认透传命令；`serve` 启动无头浏览器 + CDP 代理
- `cdp-proxy.mjs`：CDP HTTP/WebSocket 反向代理与 URL 改写
- `test/playwright-smoke.mjs`：Playwright 1.57 直连测试
- `test/patchright-smoke.mjs`：Patchright 1.59 直连测试
- `test/cdp-smoke.mjs`：跨 NAT 的 `connectOverCDP` 测试（可选 `CDP_ENGINE=patchright`）
