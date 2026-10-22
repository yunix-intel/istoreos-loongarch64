# jellyseerr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/jellyseerr:loong64` / `:24.10-la5`
- 大小：1.56GB，架构 `linux/loong64`
- 验证：307→`/setup` 200
- 说明：v3.5.0；Next 16 用 WASM SWC（无 loong64 binding）；sharp 不可用 → `images.unoptimized`；5055 端口

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t jellyseerr:loong64 .
docker tag jellyseerr:loong64 yunixintel/jellyseerr:loong64
docker tag jellyseerr:loong64 yunixintel/jellyseerr:24.10-la5
docker push yunixintel/jellyseerr:loong64
docker push yunixintel/jellyseerr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS nodebase`
- 暴露端口：`5055`
- 默认环境：`PATH=/usr/local/bin:$PATH     CI=true     COREPACK_ENABLE_DOWNLOAD_PROMPT=0     CYPRESS_INSTALL_BINARY=0     NEXT_TELEMETRY_DISABLED=1     npm_config_nodedir=/usr/local ; PATH=/usr/local/bin:$PATH     NODE_ENV=production     NEXT_TELEMETRY_DISABLED=1     PORT=5055`
- 启动：`["node", "dist/index.js"]`

Dockerfile 的上下文依赖：

- `COPY node22/ /usr/local/`
- `COPY src/ /app/`
- `COPY patch/next.config.ts /app/next.config.ts`
- `COPY src/ /app/`
- `COPY node22/ /usr/local/`
- `COPY src/ /app/`
- `COPY --from=prod-deps /app/node_modules /app/node_modules`（构建阶段内部）
- `COPY --from=build /app/.next /app/.next`（构建阶段内部）
- `COPY --from=build /app/dist /app/dist`（构建阶段内部）
- `COPY patch/next.config.js /app/next.config.js`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`5055`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v3.5.0；Next 16 用 WASM SWC（无 loong64 binding）；sharp 不可用 → `images.unoptimized`；5055 端口

## 验证

```bash
docker inspect yunixintel/jellyseerr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/jellyseerr:loong64 --help 2>/dev/null || true
```
