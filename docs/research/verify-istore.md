# iStore app-meta / 自定义 feed 验收（2026-10-25）

范围：`store/istore/` 生成器与两套 feed。目标固件：iStoreOS `24.10-la5`（公开）
与 `personal-p1-20261019`（私人）。本轮没有 iStoreOS 真机，验证到 ipk 结构、
安装器渲染和在 Host A 上用同一脚本真实安装为止。

## 产物

| 产物 | 数量/说明 |
|---|---|
| `feed/public/all/meta/app-meta-*.ipk` | 115 个，只含 public variant，镜像 `yunixintel/<app>:24.10-la5` |
| `feed/private/all/meta/app-meta-*.ipk` | 115 个；Linkwarden/Karakeep 默认 private，镜像 `local/*-private`；其余应用保留公开镜像但 store_url 指向私人源 |
| `feed/{public,private}/all/nas_luci/luci-app-istore-loong64_*.ipk` | 通用安装器 + LuCI 页面 |
| `feed/{public,private}/all/meta/Packages*` | 索引；`Packages.sig` 为空，开发源需关闭签名校验 |
| `feed/{public,private}/isfeeds.conf` | 部署占位符，不再写构建机绝对路径 |

每个 app-meta 包含：

- `/usr/lib/opkg/meta/<id>.json`：iStore 元数据 + `loong64` 扩展（镜像、端口、卷、env、sidecar、设备、cap、sysctl、review）；
- `/usr/share/istore-loong64/apps/<id>.conf`：无 `jsonfilter` 时的 shell 回退；
- `/usr/libexec/istorec/<id>.sh`：转调通用安装器；
- `/etc/config/<id>`：UCI 默认值。

## 验证

| 检查 | 结果 |
|---|---|
| 静态 schema | `python store/istore/validate.py`：115 apps，`validation OK`；auto=83、needs_config=7、manual=25 |
| ipk 结构 | 外层 tar.gz 含 `debian-binary`、`data.tar.gz`、`control.tar.gz`；权限/属主固定 |
| 换行 | 所有 `.sh`/`.conf`/`control`/postinst/prerm 无 CRLF；`mkipk.py` 统一做 LF 归一化 |
| 公开/私人隔离 | public feed 的 Linkwarden/Karakeep JSON 只有 public variant；private feed 默认 private 且引用 `local/*` |
| 安装器渲染 | public Linkwarden：PostgreSQL + LBrowser sidecar、`PLAYWRIGHT_WS_URL`；private：仅 PostgreSQL、无 LBrowser、镜像 `local/linkwarden-private:2.16.3-p1` |
| 真实安装 | Host A：通用安装器安装 joplin-server → 主容器与 PG sidecar 均 `running`/healthy，`/api/ping` 200，`status-all` 正确，`rm` 删除容器但保留 `/srv/joplin-server/data` |
| 文件型配置 | Host A：通用安装器安装 gatus，先从 `luci-app` 的 `defaults/gatus/config.yaml` 播种 `/srv/gatus/config.yaml`，再启动容器；首页 200 |

## 已知限制

- 未在 iStoreOS 真机执行 `opkg install` / LuCI 点击安装；S-I4/S-I5 仍未闭环。
- `Packages.sig` 为空；生产源应签名或显式关闭 `check_signature`。
- 25 个应用标记 manual（需要 forge、设备、域名、首次 Web 向导等），安装器会给出警告，不能承诺无人值守。
- 公开版 Linkwarden/Karakeep 需要宿主 `/opt/apps/lbrowser` 已有浏览器字节；
  私人版用内置浏览器，不依赖该目录。
- 文件型配置（Caddy/Alertmanager/Gatus/Homer/Dashy/Mosquitto/Prometheus）的默认内容
  由 `luci-app-istore-loong64` 的 `/usr/share/istore-loong64/defaults/<id>/` 播种；
  app-meta 依赖该 LuCI 包，单独装 app-meta 会得到空配置文件。
- 私人镜像只允许预载，安装器遇到 `local/*` 不会 pull；feed 不包含镜像字节。

## 复现

```bash
cd store/istore && ./build-feed.sh
python validate.py
FEED_BASE_URL=https://example.invalid/istore-loong64 ./build-feed.sh
```

部署时把 `feed/public/` 或 `feed/private/` 放到 `FEED_BASE_URL` 下，把
`isfeeds.conf` 的两条 `src/gz` 加到固件；开发阶段可设 `check_signature 0`。
