# gotify (loong64) 构建记录

## 结论

- 镜像：`yunixintel/gotify:loong64` / `:24.10-la5`
- 大小：261MB，架构 `linux/loong64`
- 验证：`/health` green；UI 200；`/version` v3.1.1
- 说明：3.1.1；Go CGO（go-sqlite3）在 openEuler 容器编；UI Vite 8 在 x86 WSL2 构建；8080；数据卷 `/data`

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t gotify:loong64 .
docker tag gotify:loong64 yunixintel/gotify:loong64
docker tag gotify:loong64 yunixintel/gotify:24.10-la5
docker push yunixintel/gotify:loong64
docker push yunixintel/gotify:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/data"]`
- 默认环境：`GOTIFY_SERVER_PORT=8080 \`
- 启动：`["/app/gotify-app"] ["serve"]`

Dockerfile 的上下文依赖：

- `COPY gotify-app /app/gotify-app`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

3.1.1；Go CGO（go-sqlite3）在 openEuler 容器编；UI Vite 8 在 x86 WSL2 构建；8080；数据卷 `/data`

## 验证

```bash
docker inspect yunixintel/gotify:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/gotify:loong64 --help 2>/dev/null || true
```
