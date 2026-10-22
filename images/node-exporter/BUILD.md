# node-exporter (loong64) 构建记录

## 结论

- 镜像：`yunixintel/node-exporter:loong64` / `:24.10-la5`
- 大小：17MB，架构 `linux/loong64`
- 验证：`/metrics` 200，含 `node_cpu_seconds_total`
- 说明：1.12.1；纯 Go 静态编；scratch + CA；9100；采集宿主指标需挂 `/proc`、`/sys`、`/`

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t node-exporter:loong64 .
docker tag node-exporter:loong64 yunixintel/node-exporter:loong64
docker tag node-exporter:loong64 yunixintel/node-exporter:24.10-la5
docker push yunixintel/node-exporter:loong64
docker push yunixintel/node-exporter:24.10-la5
```

- 基础镜像：`scratch`
- 暴露端口：`9100`
- 启动：`["/bin/node_exporter"]`

Dockerfile 的上下文依赖：

- `COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt`
- `COPY node_exporter /bin/node_exporter`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`9100`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

1.12.1；纯 Go 静态编；scratch + CA；9100；采集宿主指标需挂 `/proc`、`/sys`、`/`

## 验证

```bash
docker inspect yunixintel/node-exporter:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/node-exporter:loong64 --help 2>/dev/null || true
```
