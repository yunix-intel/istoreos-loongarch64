# drawio (loong64) 构建记录

## 结论

- 镜像：`yunixintel/drawio:loong64` / `:24.10-la5`
- 大小：498MB，架构 `linux/loong64`
- 验证：200（app.min.js 10MB）
- 说明：v32.5.5；直接取源码仓库预构建 `src/main/webapp`，无需 npm/maven；hash 路由

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t drawio:loong64 .
docker tag drawio:loong64 yunixintel/drawio:loong64
docker tag drawio:loong64 yunixintel/drawio:24.10-la5
docker push yunixintel/drawio:loong64
docker push yunixintel/drawio:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 启动：`["nginx", "-g", "daemon off;"]`

Dockerfile 的上下文依赖：

- `COPY nginx.conf /etc/nginx/nginx.conf`
- `COPY webroot/ /usr/share/nginx/html/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v32.5.5；直接取源码仓库预构建 `src/main/webapp`，无需 npm/maven；hash 路由

## 验证

```bash
docker inspect yunixintel/drawio:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/drawio:loong64 --help 2>/dev/null || true
```
