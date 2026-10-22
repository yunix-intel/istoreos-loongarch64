# xteve (loong64) 构建记录

## 结论

- 镜像：`yunixintel/xteve:loong64` / `:24.10-la5`
- 大小：1.13GB，架构 `linux/loong64`
- 验证：200
- 说明：2.2.0.200；Go 静态编（升级 x/sys 支持 loong64）；自带 ffmpeg（占大头，可瘦身）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t xteve:loong64 .
docker tag xteve:loong64 yunixintel/xteve:loong64
docker tag xteve:loong64 yunixintel/xteve:24.10-la5
docker push yunixintel/xteve:loong64
docker push yunixintel/xteve:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`34400`
- 卷：`["/config"]`
- 默认环境：`TZ=UTC`
- 启动：`["/usr/local/bin/xteve", "-config", "/config", "-port", "34400"]`

Dockerfile 的上下文依赖：

- `COPY xteve /usr/local/bin/xteve`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`34400`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

2.2.0.200；Go 静态编（升级 x/sys 支持 loong64）；自带 ffmpeg（占大头，可瘦身）

## 验证

```bash
docker inspect yunixintel/xteve:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/xteve:loong64 --help 2>/dev/null || true
```
