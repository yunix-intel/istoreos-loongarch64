# LBrowser/Playwright 基础层未验证能力复核

日期：2026-10-25。主机：Host A `loongson-lab`（`yunix-pc`，Loongnix 25 / kernel 6.6.52-loong64 / loongarch64 / 8 核 / 31 GiB）。
镜像 `local/lbrowser-runtime:3.4.2293.2`（`sha256:ed9deac552b747c2909888ebe1aa210960608d4dfada023aee8fa74f010f10a2`，1,102,858,036 B）；浏览器为宿主 `/opt/apps/lbrowser` 只读挂载，LBrowser 3.4.2293.2 / Chromium 138.0.7204.310。
测试项目 `/tmp/lbverify2`（playwright-core 1.57.0、patchright 1.59.4）；所有 HTTP 服务只绑定容器内 `127.0.0.1:14410–14412`，未 publish 端口、未改宿主网络。未改动镜像、README 或其它文档。

## 结论

| # | 项目 | 状态 | 结论 |
|---|---|---|---|
| 1 | WebGL | PASS | WebGL1/2 可用，软件渲染；ANGLE + SwiftShader (Vulkan) |
| 2 | 视频 | PASS | VP8/Vorbis WebM 与 H.264/AAC MP4 实际播放、seek、截图均通过；HEVC/Theora/AC-3 不支持 |
| 3 | DRM | PASS（符合预期） | Widevine 不可用（4 种配置均 NotSupportedError）；仅 ClearKey 可用 |
| 4 | 非 root | PASS | uid 1000 + `--no-sandbox` 可启动、截图、PDF；需可写 `/tmp` 与输出目录 |
| 5 | 多标签 | PASS | 20 标签 × 60 轮、1200 次 goto + 1200 次截图，0 失败；内存稳定约 1.5–1.7 GiB |
| 6 | 只读根 | PASS（有条件） | `--read-only` 必须配可写 `/tmp`（tmpfs 或 TMPDIR/HOME 指向 rw 挂载） |

## 1. WebGL：PASS

命令（`/work/webgl.mjs`）：
```bash
docker run --rm --shm-size=1g -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  -v /tmp/lbverify2:/work:ro -w /work local/lbrowser-runtime:3.4.2293.2 node /work/webgl.mjs
```
- `webgl2`/`webgl` 均 `available:true`，`maxTexture=8192`；编译并链接着色器、绘制三角形成功，`readPixels=[51,178,102,255]`（与着色器 0.2/0.7/0.4 一致），`gl.getError()=0`。
- `WEBGL_debug_renderer_info`：vendor `Google Inc. (Google)`，renderer `ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (LLVM 16.0.0) (0x0000C0DE)), SwiftShader driver)`。
- 不加任何 GL 参数即通过；`--enable-unsafe-swiftshader`、`--use-angle=swiftshader` 结果相同。Playwright 1.57 在 Linux 默认不加 `--enable-unsafe-swiftshader`（`chromium.js` 只在 darwin 加），故这是 LBrowser 自身的软件回退行为。

剩余风险：纯 CPU 软件渲染，复杂 WebGL/高分辨率页面帧率低；站点可能按 renderer 字符串判定为软件渲染并降级或拒绝；未来 Chromium 收紧 SwiftShader 默认回退时需显式加 flag。

## 2. 视频：PASS

命令：
```bash
docker run --rm --shm-size=1g -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  -v /tmp/lbverify2:/work:ro -v /tmp/lbverify2/assets:/assets:ro \
  -v /tmp/lbverify2/out:/out:rw -w /work local/lbrowser-runtime:3.4.2293.2 node /work/video.mjs
```
样本为 ffmpeg 生成的 3 s 320×240：`sample.webm`（VP8+Vorbis）、`sample.mp4`（H.264 baseline+AAC）。两段均 `readyState=4`、`currentTime≈1.16 s`、`paused=false`、`error=null`；seek 到 1.5 s 成功；元素截图 26,321 / 28,273 B，画面为彩条+计时器 `00:00:01.480`（非黑屏，YAVG≈122）。
编解码（`canPlayType` / MSE）：
- 支持：VP8、VP9、Opus、Vorbis、H.264、AAC、MP3、FLAC、AV1（均 `probably` / MSE `true`）。
- 不支持：HEVC/H.265（`hvc1`）、Theora、AC-3（空串 / MSE `false`）。
剩余风险：无 GPU，4K/高码率只能软解，CPU 占用高；AV1 只做了能力探测，未做实际解码；headless 无音频设备，音频仅验证解码不报错，未验证实际出声。

## 3. DRM：PASS（符合预期，Widevine 不可用）

命令（本地 `http://127.0.0.1:14411`，`isSecureContext=true`）：
```bash
docker run --rm --shm-size=1g -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  -v /tmp/lbverify2:/work:ro -w /work local/lbrowser-runtime:3.4.2293.2 node /work/drm.mjs
```
- `navigator.requestMediaKeySystemAccess`、`MediaKeys`、`HTMLMediaElement.mediaKeys` 均存在（EME API 在）。
- `com.widevine.alpha` 在 basic / minimal / WebM-VP9 / `SW_SECURE_CRYPTO` 四种配置下全部 `NotSupportedError: Unsupported keySystem or supportedConfigurations.`。
- `/opt/apps/lbrowser` 下无 `*widevine*`/CDM 文件；主二进制只有 Chromium 的 Widevine 代码字符串，未带 CDM。
- 对照组 `org.w3.clearkey` 成功：`keySystem=org.w3.clearkey`，`createMediaKeys=true`。
结论：Netflix/Spotify/Prime Video 等依赖 Widevine 的站点不可用；ClearKey 仅供测试/自建加密内容。loong64 无授权 CDM，不建议投入绕过。

## 4. 非 root 运行：PASS

命令：
```bash
docker run --rm --user 1000:1000 -e HOME=/tmp --shm-size=1g \
  -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro -v /tmp/lbverify2:/work:ro \
  -v /tmp/lbverify2/out:/out:rw -w /work local/lbrowser-runtime:3.4.2293.2 node /work/smoke.mjs
```
- uid 1000（镜像内无此 passwd 条目）启动成功：`status=200`、截图 22,123 B、PDF 18,424 B（`%PDF-`）、输出文件属主 `1000:1000`。
- 默认 `HOME=/`（不覆盖）也能跑；关键是 `/tmp` 可写（Playwright `mkdtemp`）与输出目录可写。
- 首次失败仅因 `/out/smoke.png` 是 root 所有的旧文件（`EACCES`），清掉后通过；这是输出目录权限问题，不是浏览器问题。
权限要求：挂载树对非 root 可读可执行（`lbrowser` 755、`icudtl.dat` 644）；`/tmp` 1777 或 tmpfs；输出目录对 uid 可写；`--shm-size=1g`（或 `--disable-dev-shm-usage`）；本次均带 `--no-sandbox`，未验证去掉它后的 setuid sandbox 路径。
剩余风险：本次以 `--no-sandbox` 关闭渲染进程沙箱，抓取不受信页面时风险高于 rootless 沙箱方案；不要在同一容器运行其它可信业务。

## 5. 多标签稳定性：PASS

命令：
```bash
docker run --rm --shm-size=1g -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro \
  -v /tmp/lbverify2:/work:ro -v /tmp/lbverify2/out:/out:rw -w /work \
  -e TABS=20 -e ROUNDS=20 -e MIN_SECONDS=300 -e MAX_ROUNDS=60 \
  local/lbrowser-runtime:3.4.2293.2 node /work/multitab.mjs
```
- 20 标签，60 轮（20 轮门槛后继续跑满 60 轮），共 1,200 次 `goto` + 1,200 次截图；**失败 0**，结束 20/20 页面 `evaluate` 正常。
- 总耗时 155 s；平均每轮 2,565 ms，最大 4,335 ms；每轮 20 张截图合计约 100 KB。
- 容器 cgroup 内存：起始 176 MB → 稳定 1.46–1.63 GiB，峰值 1.66 GiB；浏览器进程 RSS 合计最高约 3.8 GiB（共享页重复计入，仅作上界）。
- 证据：`/tmp/lbverify2/out/multitab.json`、`multitab-r1/r60-tab0.png`（r60 sha256 `86227ef8...e2bdd9aa`）。
剩余风险：测试页是本地静态页，未覆盖视频/WebGL/大 DOM 站点；20 个重页面需按 2–4 GiB 预留；155 s 未达 5 分钟连续运行，但已超过“20 轮”条件（60 轮）。

## 6. 只读根文件系统：PASS（有条件）

四组对照（`smoke.mjs`）：
- A `--read-only`，无 tmpfs：FAIL，`browserType.launch: EROFS: read-only file system, mkdtemp '/tmp/playwright-artifacts-...'`。
- B `--read-only --tmpfs /tmp:rw,size=1g`：PASS，goto/截图/PDF 全过。
- C `--read-only` + `TMPDIR=/out/tmp HOME=/out/home`（均指向可写挂载）：PASS，说明根文件系统本身无需可写，只需要可写临时目录。
- D 组合 `--read-only --tmpfs /tmp --user 1000:1000`：PASS，输出属主 1000。
命令示例（B/D）：
```bash
docker run --rm --read-only --tmpfs /tmp:rw,size=1g --shm-size=1g \
  -v /opt/apps/lbrowser:/opt/apps/lbrowser:ro -v /tmp/lbverify2:/work:ro \
  -v /tmp/lbverify2/out:/out:rw -w /work local/lbrowser-runtime:3.4.2293.2 node /work/smoke.mjs
```
剩余风险：tmpfs 计入容器内存，需设大小上限；`/dev/shm` 默认 64 MB 不够，仍要 `--shm-size=1g`；若把 TMPDIR 指到磁盘挂载，注意写入量与清理。

## 7. 复现与产物

- 测试脚本：`/tmp/lbverify2/{smoke,webgl,video,drm,multitab}.mjs`；产物 JSON/截图在 `/tmp/lbverify2/out/`。
- 关键哈希：`video-webm.png 9b906f29775d30aa581ed54d67b79af6837d683d2415dd21f6907f77d377943a`、`video-mp4.png 6d19af632dca904ac80c9c5c99b0c26622e290e8ed931c87fcb84a7250d3e5b6`、`smoke.png 1f938a079f278742a22f392415381e7af01b31ff1d1f6424aab99c7927be2921`。
- Patchright 1.59.4 复核了 smoke（goto/截图/PDF）与 WebGL：结果与 Playwright 完全一致（同一 renderer、同一 `readPixels`，PDF `%PDF-`）。视频/DRM/多标签仅在 Playwright 下跑过；这三项是浏览器本体能力，预期换驱动不改变。
- 所有测试容器均为 `--rm`；未改宿主网络、未 publish 端口。
