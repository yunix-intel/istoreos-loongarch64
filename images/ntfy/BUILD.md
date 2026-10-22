# ntfy (loong64) 构建记录

## 结论

- 镜像：`yunixintel/ntfy:loong64` / `:24.10-la5`
- 大小：274MB，架构 `linux/loong64`
- 验证：`/v1/health` healthy；UI 200；publish 成功
- 说明：2.32.0；Go CGO（go-sqlite3）在 openEuler 容器编；前端 Vite 在 x86 WSL2 构建；8080；挂 `/var/cache/ntfy`、`/etc/ntfy`

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t ntfy:loong64 .
docker tag ntfy:loong64 yunixintel/ntfy:loong64
docker tag ntfy:loong64 yunixintel/ntfy:24.10-la5
docker push yunixintel/ntfy:loong64
docker push yunixintel/ntfy:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`80`
- 卷：`["/var/cache/ntfy", "/etc/ntfy"]`
- 启动：`["/usr/bin/ntfy"] ["serve"]`

Dockerfile 的上下文依赖：

- `COPY ntfy /usr/bin/ntfy`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

2.32.0；Go CGO（go-sqlite3）在 openEuler 容器编；前端 Vite 在 x86 WSL2 构建；8080；挂 `/var/cache/ntfy`、`/etc/ntfy`

## 验证

```bash
docker inspect yunixintel/ntfy:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/ntfy:loong64 --help 2>/dev/null || true
```
