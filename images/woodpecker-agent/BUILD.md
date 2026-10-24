# Woodpecker agent (loong64) 构建记录

## 结论

- 镜像：`yunixintel/woodpecker-agent:loong64` / `:24.10-la5`
- 大小：约 117MB（Hub 压缩；本地 267MB）
- digest：`sha256:23689010ffd0f825d05943b48f9ad933e43adad5b254e5a248f5ec6a09d8efc2`
- 版本：Woodpecker `v3.19.0`（commit `9f5568c`）
- 验证：
  - 注册到 server（日志 `agent registered with ID 4`）
  - `/healthz` 200，Docker health `healthy`
  - 以 UID/GID 1114 运行，`--group-add` 宿主 docker.sock 的 GID 后可访问 Docker API

## 构建链路

1. 后端：openEuler 24.03 容器内，Go 1.27.2，`CGO_ENABLED=0`：
   ```bash
   CGO_ENABLED=0 go build -tags grpcnotrace \
     -ldflags "-s -w -X go.woodpecker-ci.org/woodpecker/v3/version.Version=3.19.0" \
     -o dist/woodpecker-agent go.woodpecker-ci.org/woodpecker/v3/cmd/agent
   ```
2. 与 server 使用同一份 x86 构建的 `web/dist`（agent 二进制本身不含 UI，但同 tag 构建保持一致）。
3. 运行阶段：openEuler + `ca-certificates tzdata curl bash shadow procps-ng`；
   用户 `woodpecker` UID/GID 1114；`/etc/woodpecker` 与 `/var/lib/woodpecker` 归该用户。

## 运行时契约

- 无对外业务端口；3000 只提供 `/healthz`、`/varz`、`/version`。
- 必须挂载 `/var/run/docker.sock`，并用 `--group-add <docker.sock 的 GID>` 把进程加入该组：
  ```bash
  --group-add $(stat -c %g /var/run/docker.sock)
  ```
- 环境变量：
  ```
  WOODPECKER_SERVER=woodpecker-server:9000
  WOODPECKER_AGENT_SECRET=<与 server 相同>
  WOODPECKER_BACKEND=docker
  WOODPECKER_MAX_WORKFLOWS=1
  ```
- 可选 `WOODPECKER_AGENT_CONFIG_FILE`、`WOODPECKER_LABELS`、`WOODPECKER_HOSTNAME`。

## 遇到的问题

- **无子命令**：`woodpecker-agent ping/agent` 都不存在，直接 `ENTRYPOINT` 运行二进制；
  健康检查走 HTTP `/healthz`，不是 CLI。
- **`/etc/woodpecker` 必须存在**：否则每轮都报
  `open /etc/woodpecker/agent.conf: no such file or directory`；镜像已预建并授权。
- **useradd/groupadd 不在基础包**：openEuler 最小镜像需额外装 `shadow`，否则 UID 1114 创建失败（exit 127）。
- **docker.sock 权限**：非 root 运行必须 `--group-add`；不加则是 `permission denied`。

## 运行

```bash
docker run -d --name woodpecker-agent --network woodpecker --restart unless-stopped \
  --group-add $(stat -c %g /var/run/docker.sock) \
  -e WOODPECKER_SERVER=woodpecker-server:9000 \
  -e WOODPECKER_AGENT_SECRET=<server 的 agent-secret> \
  -e WOODPECKER_BACKEND=docker \
  -e WOODPECKER_MAX_WORKFLOWS=1 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  yunixintel/woodpecker-agent:loong64
```

安全提示：能访问 `docker.sock` 等同宿主 root。agent 只应运行受信任仓库的流水线，
不要把公开注册的 Gitea 实例直接接到该 agent。
