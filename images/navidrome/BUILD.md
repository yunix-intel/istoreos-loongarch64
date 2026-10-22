# navidrome (loong64) 构建记录

## 结论

- 镜像：`yunixintel/navidrome:loong64` / `:24.10-la5`
- 大小：1.18GB，架构 `linux/loong64`
- 验证：302 向导 + scanner
- 说明：Go + 系统 taglib 2.0.2，**DSD 完整**

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t navidrome:loong64 .
docker tag navidrome:loong64 yunixintel/navidrome:loong64
docker tag navidrome:loong64 yunixintel/navidrome:24.10-la5
docker push yunixintel/navidrome:loong64
docker push yunixintel/navidrome:24.10-la5
```

- 基础镜像：`--platform=$BUILDPLATFORM ghcr.io/crazy-max/osxcross:14.5-debian AS osxcross`
- 暴露端口：`${ND_PORT}`
- 卷：`["/data", "/music"]`
- 默认环境：`XX_VERSION=b4e4c451c778822e6742bfc9d9a91d7c7d885c8a ; CROSS_TAGLIB_RELEASES_URL=https://github.com/navidrome/cross-taglib/releases/download/v${CROSS_TAGLIB_VERSION}/ ; ND_MUSICFOLDER=/music ; ND_DATAFOLDER=/data ; ND_CONFIGFILE=/data/navidrome.toml ; ND_PORT=4533 ; GODEBUG="asyncpreemptoff=1"`
- 启动：`["/app/navidrome"]`

Dockerfile 的上下文依赖：

- `COPY --from=xx-build /out/ /usr/bin/`（构建阶段内部）
- `COPY ui/package.json ui/package-lock.json ./`
- `COPY ui/bin/ ./bin/`
- `COPY ui/ ./`
- `COPY --from=ui /build /build`（构建阶段内部）
- `COPY --from=xx / /`（构建阶段内部）
- `COPY --from=build /out /`（构建阶段内部）
- `COPY --from=build /out/navidrome /app/`（构建阶段内部）

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`4533`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

Go + 系统 taglib 2.0.2，**DSD 完整**

## 验证

```bash
docker inspect yunixintel/navidrome:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/navidrome:loong64 --help 2>/dev/null || true
```
