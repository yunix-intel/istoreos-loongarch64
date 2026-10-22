# it-tools (loong64) 构建记录

## 结论

- 镜像：`yunixintel/it-tools:loong64` / `:24.10-la5`
- 大小：408MB，架构 `linux/loong64`
- 验证：200
- 说明：纯静态站点 + nginx；Vite 4/rollup 3 可在龙芯本机直接编

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t it-tools:loong64 .
docker tag it-tools:loong64 yunixintel/it-tools:loong64
docker tag it-tools:loong64 yunixintel/it-tools:24.10-la5
docker push yunixintel/it-tools:loong64
docker push yunixintel/it-tools:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 启动：`["nginx", "-g", "daemon off;"]`

Dockerfile 的上下文依赖：

- `COPY nginx.conf /etc/nginx/nginx.conf`
- `COPY dist /usr/share/nginx/html`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

纯静态站点 + nginx；Vite 4/rollup 3 可在龙芯本机直接编

## 验证

```bash
docker inspect yunixintel/it-tools:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/it-tools:loong64 --help 2>/dev/null || true
```
