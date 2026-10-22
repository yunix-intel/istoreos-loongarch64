# Apprise API 2.0.1 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/apprise-api:loong64` / `:24.10-la5`
- 大小：1.03GB，`linux/loong64`
- digest：`sha256:6db7f09275ca63b200cc8dca6115aa101508a5541c1b0c0b24a58b083d7a9002`
- 版本：Apprise API 2.0.1 / Apprise 2.0.1 / Python 3.11.6
- 验证：`/` 200、`/status` 返回 `OK`、stateless `/notify/` 已进入通知流程、
  健康检查 healthy。

## 构建

```bash
docker build -t apprise-api:loong64 .
docker tag apprise-api:loong64 yunixintel/apprise-api:loong64
docker tag apprise-api:loong64 yunixintel/apprise-api:24.10-la5
docker push yunixintel/apprise-api:loong64
docker push yunixintel/apprise-api:24.10-la5
```

上游 Dockerfile 基于 Python 3.14，但 Apprise API 2.0.1 在 openEuler 的 Python 3.11
上可正常运行。为了避开 loong64 上耗时的 Rust/cryptography 源码编译：

- 系统包提供 `python3-cryptography 42.0.2`、`python3-gevent 22.10.2`；
- `constraints.txt` 固定这两者，pip 直接复用系统包；
- 其余依赖从 PyPI 安装；`pycares`、`PyYAML`、`PGPy`、`slixmpp` 在构建阶段源码编译，
  因此必须安装 `cmake`（否则 `pycares` 报 `CMake >= 3.5 is required`）。

镜像沿用上游的 nginx + supervisor + gunicorn 结构。

## 两个 nginx 适配坑

1. 上游在 Debian 镜像里会预建：
   - `/etc/nginx/server-override.conf`
   - `/etc/nginx/location-override.conf`

   openEuler 的 nginx 不会自动创建，缺失时 nginx 启动报
   `open() "/etc/nginx/server-override.conf" failed (2: No such file or directory)`。
   本镜像在构建时创建空文件。

2. supervisor 会把 nginx 降权到 `apprise` 用户；`/var/log/nginx` 必须可写，
   否则报 `could not open error log file ... Permission denied`。
   本镜像创建 `/var/log/nginx` 并设为 0777。

## 运行

```bash
docker run -d --name apprise-api -p 8000:8000 \
  -v apprise-config:/config \
  -v apprise-attach:/attach \
  -v apprise-plugins:/plugin \
  yunixintel/apprise-api:loong64
```

- Web UI：`http://<host>:8000/`。
- 状态：`GET /status` 返回 `OK`。
- 配置、附件、插件分别持久化到 `/config`、`/attach`、`/plugin`。
- 默认 PUID/PGID 为 1000，可用环境变量覆盖；容器内 supervisor 负责降权。
- 可设置 `APPRISE_STATELESS_URLS`、`APPRISE_BASE_URL`、`HTTP_PORT` 等上游变量。

## 注意

- 镜像包含 nginx、supervisor 和构建期 Python 工具链，体积约 1.03GB；如需更小可做
  builder/runtime 两阶段清理。
- 无内置 TLS；公网必须放在 Caddy/Nginx 反向代理后。
- 默认无认证；多人/公网环境应启用 Apprise API 的认证配置。
- `/notify/` 是 stateless 接口；`/notify/<key>` 需要先保存对应配置，否则返回
  “There was no configuration found”。
- 测试通知使用 `json://localhost` 时，因本机没有 JSON 接收端会返回 424，这是
  预期失败，不代表 API 未工作；日志已显示 `Notifying 1 service(s)`。

## 验证命令

```bash
curl -fsS http://127.0.0.1:8000/status
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/
curl -X POST -d 'urls=json://localhost&body=test message' \
  http://127.0.0.1:8000/notify/
docker exec apprise-api ls -la /config
```
