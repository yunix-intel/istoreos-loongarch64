# sonarr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/sonarr:loong64` / `:24.10-la5`
- 大小：368MB，架构 `linux/loong64`
- 验证：200（API 401 未认证正常）
- 说明：v4.0.20；.NET 9 运行时 + 自写 Mono.Posix loong64 兼容层；8989

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t sonarr:loong64 .
docker tag sonarr:loong64 yunixintel/sonarr:loong64
docker tag sonarr:loong64 yunixintel/sonarr:24.10-la5
docker push yunixintel/sonarr:loong64
docker push yunixintel/sonarr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8989`
- 卷：`["/config"]`
- 默认环境：`DOTNET_ROOT=/usr/share/dotnet \`
- 启动：`["dotnet", "/app/Sonarr.dll", "-nobrowser", "-data=/config"]`

Dockerfile 的上下文依赖：

- `COPY libstdc++.so.6.0.33 /usr/lib64/`
- `COPY dotnet-min/ /usr/share/dotnet/`
- `COPY out/ /app/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8989`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v4.0.20；.NET 9 运行时 + 自写 Mono.Posix loong64 兼容层；8989

## 验证

```bash
docker inspect yunixintel/sonarr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/sonarr:loong64 --help 2>/dev/null || true
```
