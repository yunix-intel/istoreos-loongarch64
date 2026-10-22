# bazarr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/bazarr:loong64` / `:24.10-la5`
- 大小：2.28GB，架构 `linux/loong64`
- 验证：200，API 版本 1.6.2
- 说明：1.6.2；Python 3.11 + lxml/Pillow 源码编；webrtcvad 补 loongarch 分支；含 ffmpeg/7za；6767

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t bazarr:loong64 .
docker tag bazarr:loong64 yunixintel/bazarr:loong64
docker tag bazarr:loong64 yunixintel/bazarr:24.10-la5
docker push yunixintel/bazarr:loong64
docker push yunixintel/bazarr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS builder`
- 暴露端口：`6767`
- 卷：`["/config"]`
- 默认环境：`PATH=/opt/venv/bin:$PATH ; PATH=/opt/venv/bin:$PATH \`
- 启动：`["python3", "/app/bazarr.py", "--config", "/config", "--no-update"]`

Dockerfile 的上下文依赖：

- `COPY requirements-docker.txt /tmp/requirements.txt`
- `COPY webrtcvad-2.0.10/ /tmp/webrtcvad-2.0.10/`
- `COPY bazarr-1.6.2/ /app/`
- `COPY --from=builder /opt/venv /opt/venv`（构建阶段内部）
- `COPY --from=builder /app /app`（构建阶段内部）

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`6767`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

1.6.2；Python 3.11 + lxml/Pillow 源码编；webrtcvad 补 loongarch 分支；含 ffmpeg/7za；6767

## 验证

```bash
docker inspect yunixintel/bazarr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/bazarr:loong64 --help 2>/dev/null || true
```
