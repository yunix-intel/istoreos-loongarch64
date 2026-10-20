# Mosquitto 2.0.20 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/mosquitto:loong64` / `:24.10-la5`
- 大小：290MB，`linux/loong64`
- digest：`sha256:d55c57993a215185f687a345cc17c981d9eab9b7a7238e022451597147ededce`
- 版本：Mosquitto 2.0.20（openEuler 24.03 SP4 EPOL）
- 验证：匿名 publish/subscribe 成功；retained 消息在容器重启后仍可订阅；
  健康检查 healthy。

## 构建

```bash
docker build -t mosquitto:loong64 .
docker tag mosquitto:loong64 yunixintel/mosquitto:loong64
docker tag mosquitto:loong64 yunixintel/mosquitto:24.10-la5
docker push yunixintel/mosquitto:loong64
docker push yunixintel/mosquitto:24.10-la5
```

openEuler 的 `mosquitto` 包已经包含 broker、`mosquitto_pub`/`mosquitto_sub`、
`mosquitto_passwd` 和 `mosquitto_ctrl`；没有单独的 `mosquitto-clients` 包，
Dockerfile 里不要写这个名字。

## 默认配置

`/mosquitto/config/mosquitto.conf`：

```text
persistence true
persistence_location /mosquitto/data/

log_dest stdout
log_type error
log_type warning
log_type notice
log_type information
connection_messages true

listener 1883
allow_anonymous true
```

- 数据持久化到 `/mosquitto/data/mosquitto.db`，日志走 stdout。
- 默认允许匿名，只适合可信内网；公网或多人环境必须关闭匿名并配置密码。
- 容器以 `mosquitto` 用户（UID/GID 998:996）运行，`/mosquitto/data` 和
  `/mosquitto/log` 已 chown；挂载宿主目录时需自行 `chown -R 998:996`。

## 启用密码认证

准备配置目录：

```bash
mkdir -p /srv/mosquitto/config /srv/mosquitto/data
docker run --rm -v /srv/mosquitto/config:/cfg --entrypoint mosquitto_passwd \
  yunixintel/mosquitto:loong64 -b -c /cfg/passwd mqtt 'change-me'
```

`/srv/mosquitto/config/mosquitto.conf` 在默认配置基础上改：

```text
allow_anonymous false
password_file /mosquitto/config/passwd
```

启动：

```bash
docker run -d --name mosquitto -p 1883:1883 \
  -v /srv/mosquitto/config:/mosquitto/config:ro \
  -v /srv/mosquitto/data:/mosquitto/data \
  yunixintel/mosquitto:loong64
```

挂载的配置文件需对 UID 998 可读（至少 0644）。

## 注意

- `persistence true` 只保证保留消息、订阅和会话元数据；普通 QoS 0 消息不落盘。
- 需要 WebSocket 时，在配置中追加 `listener 9001` + `protocol websockets`，
  并额外映射 9001。
- 健康检查用 bash 的 `/dev/tcp` 做端口连通性检查，不依赖客户端命令。
- 客户端工具已内置，可直接：
  `docker exec mosquitto mosquitto_sub -h 127.0.0.1 -t '#' -C 1 -W 5`。

## 验证命令

```bash
docker run --rm -it --network host --entrypoint mosquitto_sub \
  yunixintel/mosquitto:loong64 -h 127.0.0.1 -t 'test/#' -C 1 -W 10
docker run --rm --network host --entrypoint mosquitto_pub \
  yunixintel/mosquitto:loong64 -h 127.0.0.1 -t test/retain -m hello -r
```
