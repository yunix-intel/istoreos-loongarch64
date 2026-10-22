# prometheus (loong64) 构建记录

## 结论

- 镜像：`yunixintel/prometheus:loong64` / `:24.10-la5`
- 大小：407MB，架构 `linux/loong64`
- 验证：`/-/healthy` 200；UI 200；`/api/v1/status/buildinfo` 3.15.0
- 说明：3.15.0；UI 用 Vite 8 在 x86 WSL2 构建，Go `-tags builtinassets` 嵌入；TSDB `/prometheus`；9090

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t prometheus:loong64 .
docker tag prometheus:loong64 yunixintel/prometheus:loong64
docker tag prometheus:loong64 yunixintel/prometheus:24.10-la5
docker push yunixintel/prometheus:loong64
docker push yunixintel/prometheus:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`9090`
- 卷：`["/prometheus"]`
- 启动：`["/bin/prometheus"] ["--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus"]`

Dockerfile 的上下文依赖：

- `COPY prometheus /bin/prometheus`
- `COPY promtool /bin/promtool`
- `COPY prometheus.yml /etc/prometheus/prometheus.yml`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`9090`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

3.15.0；UI 用 Vite 8 在 x86 WSL2 构建，Go `-tags builtinassets` 嵌入；TSDB `/prometheus`；9090

## 验证

```bash
docker inspect yunixintel/prometheus:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/prometheus:loong64 --help 2>/dev/null || true
```
