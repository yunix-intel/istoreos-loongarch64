# gogs (loong64) 构建记录

## 结论

- 镜像：`yunixintel/gogs:loong64` / `:24.10-la5`
- 大小：613MB，架构 `linux/loong64`
- 验证：302→200，安装与 SQLite 验证通过
- 说明：v0.14.3 源码编；0.14 起 sqlite 已纯 Go（不需要 CGO）；镜像带 git

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t gogs:loong64 .
docker tag gogs:loong64 yunixintel/gogs:loong64
docker tag gogs:loong64 yunixintel/gogs:24.10-la5
docker push yunixintel/gogs:loong64
docker push yunixintel/gogs:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`3000 22`
- 卷：`["/data"]`
- 默认环境：`GOGS_CUSTOM=/data/gogs`
- 启动：`["/app/gogs/gogs", "web", "--config", "/data/gogs/conf/app.ini"]`

Dockerfile 的上下文依赖：

- `COPY gogs /app/gogs/gogs`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`3000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.14.3 源码编；0.14 起 sqlite 已纯 Go（不需要 CGO）；镜像带 git

## 验证

```bash
docker inspect yunixintel/gogs:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/gogs:loong64 --help 2>/dev/null || true
```
