# gatus (loong64) 构建记录

## 结论

- 镜像：`yunixintel/gatus:loong64` / `:24.10-la5`
- 大小：35MB，架构 `linux/loong64`
- 验证：`/` 200；`/api/v1/endpoints/statuses` 200
- 说明：5.37.0；Go 静态编；自带 `web/static`；scratch；默认配置监控 Prometheus；8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t gatus:loong64 .
docker tag gatus:loong64 yunixintel/gatus:loong64
docker tag gatus:loong64 yunixintel/gatus:24.10-la5
docker push yunixintel/gatus:loong64
docker push yunixintel/gatus:24.10-la5
```

- 基础镜像：`scratch`
- 暴露端口：`8080`
- 默认环境：`GATUS_CONFIG_PATH=/config/config.yaml \`
- 启动：`["/gatus"]`

Dockerfile 的上下文依赖：

- `COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt`
- `COPY gatus /gatus`
- `COPY config.yaml /config/config.yaml`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

5.37.0；Go 静态编；自带 `web/static`；scratch；默认配置监控 Prometheus；8080

## 验证

```bash
docker inspect yunixintel/gatus:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/gatus:loong64 --help 2>/dev/null || true
```
