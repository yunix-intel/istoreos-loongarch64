# prowlarr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/prowlarr:loong64` / `:24.10-la5`
- 大小：358MB，架构 `linux/loong64`
- 验证：200（API 401 正常）
- 说明：2.6.5；.NET 9 + 自编 Mono.Posix/e_sqlite3；9696

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t prowlarr:loong64 .
docker tag prowlarr:loong64 yunixintel/prowlarr:loong64
docker tag prowlarr:loong64 yunixintel/prowlarr:24.10-la5
docker push yunixintel/prowlarr:loong64
docker push yunixintel/prowlarr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`9696`
- 卷：`["/config"]`
- 默认环境：`DOTNET_ROOT=/usr/share/dotnet \`
- 启动：`["dotnet", "/app/Prowlarr.dll", "-nobrowser", "-data=/config"]`

Dockerfile 的上下文依赖：

- `COPY libstdc++.so.6.0.33 /usr/lib64/`
- `COPY dotnet-min/ /usr/share/dotnet/`
- `COPY out/ /app/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`9696`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

2.6.5；.NET 9 + 自编 Mono.Posix/e_sqlite3；9696

## 验证

```bash
docker inspect yunixintel/prowlarr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/prowlarr:loong64 --help 2>/dev/null || true
```
