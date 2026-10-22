# tautulli (loong64) 构建记录

## 结论

- 镜像：`yunixintel/tautulli:loong64` / `:24.10-la5`
- 大小：390MB，架构 `linux/loong64`
- 验证：303→`/welcome` 200
- 说明：v2.18.2；纯 Python；8181

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t tautulli:loong64 .
docker tag tautulli:loong64 yunixintel/tautulli:loong64
docker tag tautulli:loong64 yunixintel/tautulli:24.10-la5
docker push yunixintel/tautulli:loong64
docker push yunixintel/tautulli:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8181`
- 卷：`/config`
- 默认环境：`TZ=UTC \`
- 启动：`["python3", "Tautulli.py", "--datadir", "/config", "--nolaunch"] ["--quiet"]`

Dockerfile 的上下文依赖：

- `COPY src/ /app/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8181`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.18.2；纯 Python；8181

## 验证

```bash
docker inspect yunixintel/tautulli:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/tautulli:loong64 --help 2>/dev/null || true
```
