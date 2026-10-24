# Headscale v0.29.5 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/headscale:loong64` / `:24.10-la5`
- 大小：约 137MB（Hub 压缩）
- digest：`sha256:603650be7d91772df3f00426ecbc79ed8b11b76122c630a5c6784a0e0662b3fb`
- 版本：Headscale v0.29.5（commit `0f7d1e53`）
- 验证：
  - `/health` 200、`/metrics` 9090 监听、健康检查 healthy
  - `headscale users create testuser` 成功
  - `headscale preauthkeys create --user 1` 生成 `hskey-auth-...`
  - 未用真实 Tailscale 客户端注册节点

## 构建链路

1. `juanfont/headscale` v0.29.5，`go.mod` 要求 Go 1.26.8。
2. Go 1.27.2，`CGO_ENABLED=0 go build -trimpath -ldflags "-s -w"`。
3. 运行阶段 openEuler + `ca-certificates tzdata curl shadow util-linux`。
4. 配置模板来自上游 `config-example.yaml`；entrypoint 首次启动复制为
   `/etc/headscale/config.yaml`，按环境变量改 `server_url`/`listen_addr`/metrics。
5. 运行用户 `headscale` UID/GID 1106；数据 `/var/lib/headscale`。

## 遇到的问题

- **`/var/run/headscale` 权限**：Headscale 启动时创建 unix socket，目录不存在或
  不可写会报 `creating directory failed with permission error`；
  entrypoint 必须先 `mkdir` 并 `chown`。
- **CLI 需要配置文件**：`headscale users create` 默认读 `/etc/headscale/config.yaml`；
  首次 `serve` 生成后 CLI 才能用。
- **gRPC 默认只监听 127.0.0.1:50443**：容器内 CLI 可用；远程 CLI 需要证书和
  `grpc_allow_insecure`，默认不放开。
- **DNS base_domain**：默认 `example.com`，生产需改成自己的域名，MagicDNS 才能用。

## 运行

```bash
docker run -d --name headscale -p 8080:8080 -p 9090:9090 \
  -e HEADSCALE_SERVER_URL=https://headscale.example.com \
  -v headscale-config:/etc/headscale \
  -v headscale-data:/var/lib/headscale \
  yunixintel/headscale:loong64
```

- HTTP/API：`8080`；metrics：`9090`。
- 创建用户：`docker exec headscale headscale users create <name>`。
- 创建 preauth key：`docker exec headscale headscale preauthkeys create --user <id>`。
- 客户端：`tailscale up --login-server https://<host> --authkey <key>`。
- `/etc/headscale` 与 `/var/lib/headscale` 必须持久化；私钥/DB 都在里面。
- 无 Web UI，纯 CLI/API；无 TLS 终止，公网需反代 HTTPS。
