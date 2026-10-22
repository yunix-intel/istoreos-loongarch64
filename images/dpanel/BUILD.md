# dpanel (loong64) 构建记录

## 结论

- 镜像：`yunixintel/dpanel:loong64` / `:24.10-la5`
- 大小：566MB，架构 `linux/loong64`
- 验证：200
- 说明：v1.11.1；Go + CGO sqlite（CGO=0 会 panic）；需 docker.sock；8807 端口

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t dpanel:loong64 .
docker tag dpanel:loong64 yunixintel/dpanel:loong64
docker tag dpanel:loong64 yunixintel/dpanel:24.10-la5
docker push yunixintel/dpanel:loong64
docker push yunixintel/dpanel:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8807`
- 卷：`["/dpanel"]`
- 默认环境：`TZ=Asia/Shanghai \`
- 启动：`["/app/server/dpanel", "server:start", "-f", "/app/server/config.yaml"]`

Dockerfile 的上下文依赖：

- `COPY dpanel /app/server/dpanel`
- `COPY config.yaml /app/server/config.yaml`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8807`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v1.11.1；Go + CGO sqlite（CGO=0 会 panic）；需 docker.sock；8807 端口

## 验证

```bash
docker inspect yunixintel/dpanel:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/dpanel:loong64 --help 2>/dev/null || true
```
