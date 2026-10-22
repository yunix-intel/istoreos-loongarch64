# audiobookshelf (loong64) 构建记录

## 结论

- 镜像：`yunixintel/audiobookshelf:loong64` / `:24.10-la5`
- 大小：1.50GB，架构 `linux/loong64`
- 验证：200
- 说明：v2.37.1；Node 22 + sqlite3/nusqlite3 源码编；前端在 x64 构建（Tailwind oxide 无 loong64）；13378 端口

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t audiobookshelf:loong64 .
docker tag audiobookshelf:loong64 yunixintel/audiobookshelf:loong64
docker tag audiobookshelf:loong64 yunixintel/audiobookshelf:24.10-la5
docker push yunixintel/audiobookshelf:loong64
docker push yunixintel/audiobookshelf:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS nodebase`
- 暴露端口：`13378`
- 默认环境：`PATH=/usr/local/bin:$PATH     CI=true     npm_config_nodedir=/usr/local ; NODE_ENV=production     npm_config_build_from_source=true ; PATH=/usr/local/bin:$PATH     NODE_ENV=production     PORT=13378     CONFIG_PATH=/config     METADATA_PATH=/metadata     SOURCE=docker     FFMPEG_PATH=/usr/bin/ffmpeg     FFPROBE_PATH=/usr/bin/ffprobe     NUSQLITE3_PATH=/usr/local/lib/nusqlite3/libnusqlite3.so     SKIP_BINARIES_CHECK=1`
- 启动：`["node", "dist-server/index.js"]`

Dockerfile 的上下文依赖：

- `COPY node22/ /usr/local/`
- `COPY src/package.json src/package-lock.json src/index.js src/tsconfig.server.json ./`
- `COPY src/server/ ./server/`
- `COPY src/package.json src/package-lock.json src/index.js ./`
- `COPY src/server/ ./server/`
- `COPY --from=compile-server /server/dist-server ./dist-server`（构建阶段内部）
- `COPY node22/ /usr/local/`
- `COPY client-dist/ /app/client/dist/`
- `COPY --from=build-server /server /app`（构建阶段内部）
- `COPY nusqlite/ /usr/local/lib/nusqlite3/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`13378`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.37.1；Node 22 + sqlite3/nusqlite3 源码编；前端在 x64 构建（Tailwind oxide 无 loong64）；13378 端口

## 验证

```bash
docker inspect yunixintel/audiobookshelf:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/audiobookshelf:loong64 --help 2>/dev/null || true
```
