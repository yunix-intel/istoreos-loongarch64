# homarr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/homarr:loong64` / `:24.10-la5`
- 大小：819MB，架构 `linux/loong64`
- 验证：307→`/init` 200
- 说明：v2.6.0；Next 16 WASM SWC + Node 24 + redis；Bun/Turbo 无 loong64 改用 pnpm；7575 端口

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t homarr:loong64 .
docker tag homarr:loong64 yunixintel/homarr:loong64
docker tag homarr:loong64 yunixintel/homarr:24.10-la5
docker push yunixintel/homarr:loong64
docker push yunixintel/homarr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`7575`
- 卷：`["/appdata"]`
- 默认环境：`DB_URL=/appdata/db/db.sqlite \`
- 启动：`["/app/entrypoint.sh"] ["sh", "run.sh"]`

Dockerfile 的上下文依赖：

- `COPY src/node24/bin/node /usr/local/bin/node`
- `COPY build/artifacts/standalone/ /app/`
- `COPY build/artifacts/cli.cjs /app/apps/cli/cli.cjs`
- `COPY build/artifacts/migrations/ /app/db/migrations/`
- `COPY build/artifacts/better_sqlite3.node /app/build/better_sqlite3.node`
- `COPY src/homarr-2.6.0/scripts/run.sh /app/run.sh`
- `COPY src/homarr-2.6.0/scripts/trusted-proxies.mjs /app/scripts/trusted-proxies.mjs`
- `COPY src/homarr-2.6.0/scripts/entrypoint.sh /app/entrypoint.sh`
- `COPY src/homarr-2.6.0/packages/redis/redis.conf /app/redis.conf`
- `COPY src/homarr-2.6.0/nginx.conf /etc/nginx/templates/nginx.conf`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`7575`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.6.0；Next 16 WASM SWC + Node 24 + redis；Bun/Turbo 无 loong64 改用 pnpm；7575 端口

## 验证

```bash
docker inspect yunixintel/homarr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/homarr:loong64 --help 2>/dev/null || true
```
