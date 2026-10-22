# dozzle (loong64) 构建记录

## 结论

- 镜像：`yunixintel/dozzle:loong64` / `:24.10-la5`
- 大小：68MB，架构 `linux/loong64`
- 验证：v11.3.3；HTTP 200；日志 `Connected to Docker`
- 说明：前端 Bun 1.4.3/Vite 在 x86 WSL2 构建（产物架构无关），Go 1.27.2 在 A 编 loong64；scratch；需挂 docker.sock；8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t dozzle:loong64 .
docker tag dozzle:loong64 yunixintel/dozzle:loong64
docker tag dozzle:loong64 yunixintel/dozzle:24.10-la5
docker push yunixintel/dozzle:loong64
docker push yunixintel/dozzle:24.10-la5
```

- 基础镜像：`scratch`
- 暴露端口：`8080`
- 启动：`["/dozzle"]`

Dockerfile 的上下文依赖：

- `COPY data /data`
- `COPY tmp /tmp`
- `COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt`
- `COPY dozzle /dozzle`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

前端 Bun 1.4.3/Vite 在 x86 WSL2 构建（产物架构无关），Go 1.27.2 在 A 编 loong64；scratch；需挂 docker.sock；8080

## 验证

```bash
docker inspect yunixintel/dozzle:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/dozzle:loong64 --help 2>/dev/null || true
```
