# jellyfin (loong64) 构建记录

## 结论

- 镜像：`yunixintel/jellyfin:loong64` / `:24.10-la5`
- 大小：1.46GB，架构 `linux/loong64`
- 验证：API 10.11.0 + Web 200
- 说明：.NET 9 自编；**自 2026-10-19 起内置 ImageSharp 编码器**（缩略图/Trickplay/拼图/BlurHash 全可用，含 Noto CJK 字体）；代价：纯托管性能较 Skia 慢、无 ICC 色彩管理

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t jellyfin:loong64 .
docker tag jellyfin:loong64 yunixintel/jellyfin:loong64
docker tag jellyfin:loong64 yunixintel/jellyfin:24.10-la5
docker push yunixintel/jellyfin:loong64
docker push yunixintel/jellyfin:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8096`
- 卷：`["/config", "/media"]`
- 默认环境：`DOTNET_ROOT=/usr/share/dotnet ; PATH="/usr/share/dotnet:${PATH}" ; DOTNET_CLI_TELEMETRY_OPTOUT=1 ; DOTNET_NOLOGO=1`
- 启动：`["dotnet", "/jellyfin/jellyfin.dll", "--webdir", "/jellyfin/jellyfin-web", "--ffmpeg", "/usr/bin/ffmpeg", "--datadir", "/config"]`

Dockerfile 的上下文依赖：

- `COPY libstdc++.so.6.0.33 /usr/lib64/`
- `COPY dotnet-min/ /usr/share/dotnet/`
- `COPY app/ /jellyfin/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8096`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

.NET 9 自编；**自 2026-10-19 起内置 ImageSharp 编码器**（缩略图/Trickplay/拼图/BlurHash 全可用，含 Noto CJK 字体）；代价：纯托管性能较 Skia 慢、无 ICC 色彩管理

## 验证

```bash
docker inspect yunixintel/jellyfin:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/jellyfin:loong64 --help 2>/dev/null || true
```
