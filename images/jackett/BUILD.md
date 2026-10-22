# jackett (loong64) 构建记录

## 结论

- 镜像：`yunixintel/jackett:loong64` / `:24.10-la5`
- 大小：335MB，架构 `linux/loong64`
- 验证：301→302（登录）
- 说明：v0.24.2867；.NET 9 源码编，自带运行时；需宿主 libstdc++ 6.0.33（已内置）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t jackett:loong64 .
docker tag jackett:loong64 yunixintel/jackett:loong64
docker tag jackett:loong64 yunixintel/jackett:24.10-la5
docker push yunixintel/jackett:loong64
docker push yunixintel/jackett:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`9117`
- 卷：`["/config"]`
- 默认环境：`DOTNET_ROOT=/usr/share/dotnet     PATH=/usr/share/dotnet:$PATH     DOTNET_CLI_TELEMETRY_OPTOUT=1     DOTNET_NOLOGO=1     XDG_CONFIG_HOME=/config     HOME=/config     TZ=UTC`
- 启动：`["dotnet", "/app/jackett.dll", "--NoRestart", "--NoUpdates"]`

Dockerfile 的上下文依赖：

- `COPY libstdc++.so.6.0.33 /usr/lib64/`
- `COPY dotnet-min/ /usr/share/dotnet/`
- `COPY out/ /app/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`9117`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.24.2867；.NET 9 源码编，自带运行时；需宿主 libstdc++ 6.0.33（已内置）

## 验证

```bash
docker inspect yunixintel/jackett:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/jackett:loong64 --help 2>/dev/null || true
```
