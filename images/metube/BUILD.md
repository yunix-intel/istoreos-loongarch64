# MeTube (loong64) 构建记录

## 结论

- 镜像：`yunixintel/metube:loong64` / `:24.10-la5`
- 大小：约 441MB（Hub 压缩；本地 1.28GB）
- digest：`sha256:7321b0bf78051861f46cff63f491d073643eec631748e2b017cfcd519197526f`
- 版本：MeTube `2026.10.23`（commit `0f3fc1d`）
- 验证：
  - UI `/` 200；Python 3.13.7；yt-dlp 2026.10.21；Node 24.22.1
  - API `POST /add` 添加 YouTube 短视频，25 秒内 `finished`，`/downloads/Me at the zoo.webm` 464KB 合并完成
  - 进程以 UID/GID 1111 运行；Docker health `healthy`

## 构建链路

1. 前端：x86_64 WSL2，Node 24.22.1 + pnpm 12.6.0（`packageManager` 锁定）：
   ```bash
   cd ui
   pnpm install --frozen-lockfile
   pnpm run build        # @angular/build:application → dist/metube/browser
   ```
2. 后端：openEuler 24.03 容器内源码编 Python 3.13.7 到 `/usr/local`，
   再用 pip 安装：
   `aiohttp`、`python-socketio`、`yt-dlp`、`certifi`、`mutagen`、`pycryptodomex`、
   `requests`、`urllib3`、`websockets`、`yt-dlp-ejs`。
   不装 `yt-dlp[default]` 的 `brotli`/`curl-cffi`/`deno`：前两者在 loong64 构建失败，
   后者无 loong64 资产；JS runtime 用镜像自带的 Node 24。
3. 运行阶段 openEuler + `ffmpeg 6.1.1`（系统包）+ Node 24（复制 `yunixintel/node:24.22.1`
   的 `/opt/node24`）；UID/GID 1111。
4. 两处源码补丁：
   - `patches/metube-watchfiles.patch`：去掉 `watchfiles`（Rust 扩展无 loong64 轮子），
     用 1 秒轮询目录 mtime 的 `awatch` 替代；调用方本来就比较文件签名，行为等价。
   - `patches/metube-entrypoint.patch`：`PUID/PGID` 优先于 shell 的 `UID`；
     无 `bgutil-pot` 时跳过 POT provider；默认注入 `YTDL_OPTIONS={"js_runtimes":{"node":{}}}`。

## 运行时契约

- 端口：8082（避开 CasaOS 的 8081）。
- 卷：`/downloads`（下载文件、`.metube` 状态、临时文件）。
- 环境变量：
  ```
  PUID=1111 PGID=1111 UMASK=022
  DOWNLOAD_DIR=/downloads
  STATE_DIR=/downloads/.metube
  TEMP_DIR=/downloads
  PORT=8082
  ```
- 首次启动 entrypoint 会 `chown -R` 下载目录；宿主目录建议预先 `chown 1111:1111`。
- yt-dlp 默认用 Node 24 作为 JS runtime；如用户显式设置 `YTDL_OPTIONS`，以用户值为准。

## 遇到的问题

- **Python 版本**：上游要求 `>=3.13`，openEuler 24.03 只有 3.11，必须源码编 3.13.7。
- **watchfiles 无 loong64 轮子**：Rust/maturin 无 loong64 预编译；改用轮询补丁。
- **brotli 构建失败**：`brotli`/`brotlicffi` 内置的 C 代码使用 GCC `model` 属性，
  LoongArch GCC 报 `invalid argument of 'model' attribute`；放弃 Brotli，HTTP 仍可用 gzip。
- **aria2 不存在**：openEuler 仓库没有 aria2 包；MeTube 源码也未调用它，直接移除。
- **Docker ENV 吞引号**：`ENV YTDL_OPTIONS={"js_runtimes":{"node":{}}}` 落盘后变成
  `{js_runtimes:{node:{}}}`，导致 JSON 解析失败；改为 entrypoint 里用单引号赋值。
- **`UID` 特殊变量**：`PUID="${UID:-$PUID}"` 在 bash 下 `UID=0` 恒成立，
  把进程跑成 root；补丁改为 `PUID="${PUID:-$UID}"`。
- **Angular 输出路径**：新版输出在 `dist/metube/browser`，必须复制到
  `/app/ui/dist/metube/browser`，少一层就报 `does not exist`。

## 限制

- 未编译 `bgutil-pot`（PO token provider），部分 YouTube 视频可能缺格式或需要登录 cookies；
  可自行配置远程 provider 或挂载 cookies。
- 无 Brotli 解压；不影响常规下载。
- ffmpeg 为 openEuler 6.1.1，不是上游的 8.1 静态包；常规合并/转码可用，
  未验证旧版对 YouTube HLS 的精确 seek 行为。

## 运行

```bash
docker run -d --name metube -p 8082:8082 \
  -v /srv/downloads:/downloads \
  -e PUID=1111 -e PGID=1111 \
  yunixintel/metube:loong64
```

Web UI：`http://<host>:8082/`；健康检查 `/`。添加 URL 后文件写入 `/downloads`。
