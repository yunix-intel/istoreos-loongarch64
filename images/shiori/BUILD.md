# shiori (loong64) 构建记录

## 结论

- 镜像：`yunixintel/shiori:loong64` / `:24.10-la5`
- 大小：290MB，架构 `linux/loong64`
- 验证：200
- 说明：v1.8.0；Go 静态编；8080 端口；生产建议设 `SHIORI_HTTP_SECRET_KEY`

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t shiori:loong64 .
docker tag shiori:loong64 yunixintel/shiori:loong64
docker tag shiori:loong64 yunixintel/shiori:24.10-la5
docker push yunixintel/shiori:loong64
docker push yunixintel/shiori:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 默认环境：`TZ=Asia/Shanghai \`
- 启动：`["/usr/local/bin/shiori"] ["server"]`

Dockerfile 的上下文依赖：

- `COPY shiori /usr/local/bin/shiori`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v1.8.0；Go 静态编；8080 端口；生产建议设 `SHIORI_HTTP_SECRET_KEY`

## 验证

```bash
docker inspect yunixintel/shiori:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/shiori:loong64 --help 2>/dev/null || true
```
