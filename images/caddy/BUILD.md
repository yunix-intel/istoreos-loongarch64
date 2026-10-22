# caddy (loong64) 构建记录

## 结论

- 镜像：`yunixintel/caddy:loong64` / `:24.10-la5`
- 大小：57MB，架构 `linux/loong64`
- 验证：`caddy version` 2.11.7；默认页 HTTP 200
- 说明：纯 Go 静态编；scratch + CA；默认 Caddyfile 监听 8080；挂载自己的 Caddyfile 覆盖，80/443/8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t caddy:loong64 .
docker tag caddy:loong64 yunixintel/caddy:loong64
docker tag caddy:loong64 yunixintel/caddy:24.10-la5
docker push yunixintel/caddy:loong64
docker push yunixintel/caddy:24.10-la5
```

- 基础镜像：`scratch`
- 暴露端口：`80 443 8080`
- 默认环境：`XDG_DATA_HOME=/data \`
- 启动：`["/usr/bin/caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]`

Dockerfile 的上下文依赖：

- `COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt`
- `COPY caddy /usr/bin/caddy`
- `COPY Caddyfile /etc/caddy/Caddyfile`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80/443/8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

纯 Go 静态编；scratch + CA；默认 Caddyfile 监听 8080；挂载自己的 Caddyfile 覆盖，80/443/8080

## 验证

```bash
docker inspect yunixintel/caddy:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/caddy:loong64 --help 2>/dev/null || true
```
