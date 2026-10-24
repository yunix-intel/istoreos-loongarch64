# SABnzbd (loong64) 构建记录

## 结论

- 镜像：`yunixintel/sabnzbd:loong64` / `:24.10-la5`
- 大小：约 139MB（Hub 压缩；本地 390MB）
- digest：`sha256:1e20dee897ea488f801a76a5a0dcc2677ae396b7f9716bbc118780b808ea7d81`
- 版本：SABnzbd `5.1.3`（commit `a647f73`）
- 验证：
  - `/` 303→`/wizard/` 200；API `mode=version` 返回 `{"version":"5.1.3"}`
  - `par2 create` + `par2 verify` 通过
  - `unrar` 7.13 可执行；`7za` 16.02；`nice`/`ionice` 可用
  - Python 3.11.6，JSON 模块 ujson 5.13.0；Docker health `healthy`

## 构建链路

1. 基础：openEuler 24.03 + 系统 Python 3.11.6；不源码编 Python。
2. Python 依赖：`python3 -m venv --system-site-packages /opt/venv`，然后
   安装 `requirements.txt`，但过滤掉 `orjson` 与 `cryptography`：
   - `orjson` 需要 Rust，SABnzbd 自动回退到 `ujson`；
   - `cryptography` 用 openEuler 的 `python3-cryptography 42.0.2`（避免 Rust）。
3. par2cmdline 0.8.1 源码编。旧 `config.guess` 不识别 loongarch64，configure 必须加
   `--build=loongarch64-unknown-linux-gnu`。
4. unrar 7.1.10 源码（rarlab）编出 `unrar 7.13 freeware`，装到 `/usr/local/bin`。
   许可证为 freeware，允许原样分发；镜像内保留二进制并在此说明来源。
5. 运行阶段复制 venv、par2、unrar 和整个 SABnzbd 源码；UID/GID 1112。

## 运行时契约

- 端口：8080；UI 根路径 `/`，首次进入 `/wizard/`。
- 卷：`/config`（`sabnzbd.ini`、日志、admin）、`/downloads`（含 `Downloads` 子目录）。
- 环境：`SABNZBD_CONFIG=/config`、`HOME=/config`、`TZ`；entrypoint 固定
  `--server 0.0.0.0:8080 --browser 0 --config-file /config/sabnzbd.ini`。
- API key 在 `/config/sabnzbd.ini` 的 `api_key`；API 路径 `/api?mode=...&apikey=...`。
- 健康检查 `curl -fsSL http://127.0.0.1:8080/`（跟随 303 到 wizard）。

## 遇到的问题

- **UI 路径变了**：5.x 不再使用 `/sabnzbd/` 前缀，健康检查打 `/sabnzbd/` 会 404；
  改为跟随根路径重定向。
- **par2 configure 不认龙芯**：`cannot guess build type`，需显式 `--build`。
- **orjson/cryptography 的 Rust 依赖**：分别用 ujson 回退和系统 cryptography 解决，
  没有在镜像内引入 Rust 工具链。
- **requirements 版本随 tag 变化**：5.1.3 的 ujson 是 5.13.0、sabctools 9.6.3，
  且没有 httptools；不要按 master 的版本假设。

## 限制

- 未配置真实 Usenet 服务器，未做完整 NZB 下载/修复/解压链路；只验证了 API、par2、unrar 可用。
- 无 orjson，JSON 走 ujson（功能等价，性能略低）。
- `unrar` 为免费但闭源工具；若发行政策不允许，可移除并让 SABnzbd 仅用 7zip。

## 运行

```bash
docker run -d --name sabnzbd -p 8080:8080 \
  -v /srv/sabnzbd/config:/config \
  -v /srv/downloads:/downloads \
  yunixintel/sabnzbd:loong64
```

首次打开 `http://<host>:8080/` 进入向导，配置新闻服务器与下载目录后用 API key 对接
Sonarr/Radarr 等。
