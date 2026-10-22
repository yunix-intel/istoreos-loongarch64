# radarr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/radarr:loong64` / `:24.10-la5`
- 大小：367MB，架构 `linux/loong64`
- 验证：200
- 说明：v6.4.4；同上；自编译 e_sqlite3；7878

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t radarr:loong64 .
docker tag radarr:loong64 yunixintel/radarr:loong64
docker tag radarr:loong64 yunixintel/radarr:24.10-la5
docker push yunixintel/radarr:loong64
docker push yunixintel/radarr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`7878`
- 卷：`["/config"]`
- 默认环境：`DOTNET_ROOT=/usr/share/dotnet \`
- 启动：`["dotnet", "/app/Radarr.dll", "-nobrowser", "-data=/config"]`

Dockerfile 的上下文依赖：

- `COPY libstdc++.so.6.0.33 /usr/lib64/`
- `COPY dotnet-min/ /usr/share/dotnet/`
- `COPY out/ /app/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`7878`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v6.4.4；同上；自编译 e_sqlite3；7878

## 验证

```bash
docker inspect yunixintel/radarr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/radarr:loong64 --help 2>/dev/null || true
```
