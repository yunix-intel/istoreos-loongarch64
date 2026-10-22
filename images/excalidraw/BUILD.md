# excalidraw (loong64) 构建记录

## 结论

- 镜像：`yunixintel/excalidraw:loong64` / `:24.10-la5`
- 大小：439MB，架构 `linux/loong64`
- 验证：200（SPA 深路径 200）
- 说明：v0.18.1；Vite 5 + rollup 4（自带 loongarch64 binding）；需 Node 22（用 /opt/node22-abi2）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t excalidraw:loong64 .
docker tag excalidraw:loong64 yunixintel/excalidraw:loong64
docker tag excalidraw:loong64 yunixintel/excalidraw:24.10-la5
docker push yunixintel/excalidraw:loong64
docker push yunixintel/excalidraw:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 启动：`["nginx", "-g", "daemon off;"]`

Dockerfile 的上下文依赖：

- `COPY nginx.conf /etc/nginx/nginx.conf`
- `COPY build/ /usr/share/nginx/html/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.18.1；Vite 5 + rollup 4（自带 loongarch64 binding）；需 Node 22（用 /opt/node22-abi2）

## 验证

```bash
docker inspect yunixintel/excalidraw:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/excalidraw:loong64 --help 2>/dev/null || true
```
