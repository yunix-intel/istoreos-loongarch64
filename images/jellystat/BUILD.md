# jellystat (loong64) 构建记录

## 结论

- 镜像：`yunixintel/jellystat:loong64` / `:24.10-la5`
- 大小：833MB，架构 `linux/loong64`
- 验证：200，`/auth/isConfigured` 200
- 说明：1.1.12；Node 20 + 降级 Vite 6；**需要外部 PostgreSQL**；3000

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t jellystat:loong64 .
docker tag jellystat:loong64 yunixintel/jellystat:loong64
docker tag jellystat:loong64 yunixintel/jellystat:24.10-la5
docker push yunixintel/jellystat:loong64
docker push yunixintel/jellystat:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS builder`
- 暴露端口：`3000`
- 卷：`/app/data`
- 默认环境：`NODE_ENV=production \`
- 启动：`["/entry.sh"]`

Dockerfile 的上下文依赖：

- `COPY package.json package-lock.json ./`
- `COPY . .`
- `COPY --from=builder /app/package.json /app/package-lock.json ./`（构建阶段内部）
- `COPY --from=builder /app/dist ./dist`（构建阶段内部）
- `COPY --from=builder /app/backend ./backend`（构建阶段内部）
- `COPY entry.sh /entry.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`3000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

1.1.12；Node 20 + 降级 Vite 6；**需要外部 PostgreSQL**；3000

## 验证

```bash
docker inspect yunixintel/jellystat:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/jellystat:loong64 --help 2>/dev/null || true
```
