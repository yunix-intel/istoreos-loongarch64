# uptimekuma (loong64) 构建记录

## 结论

- 镜像：`yunixintel/uptimekuma:loong64` / `:24.10-la5`
- 大小：664MB，架构 `linux/loong64`
- 验证：302→200
- 说明：Node 20 + 源码编 sqlite3

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t uptimekuma:loong64 .
docker tag uptimekuma:loong64 yunixintel/uptimekuma:loong64
docker tag uptimekuma:loong64 yunixintel/uptimekuma:24.10-la5
docker push yunixintel/uptimekuma:loong64
docker push yunixintel/uptimekuma:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS build`
- 暴露端口：`3001`
- 卷：`/app/data`
- 默认环境：`UPTIME_KUMA_IS_CONTAINER=1 NODE_ENV=production`
- 启动：`["node", "--experimental-require-module", "server/server.js"]`

Dockerfile 的上下文依赖：

- `COPY package.json package-lock.json .npmrc ./`
- `COPY . .`
- `COPY --from=build /app /app`（构建阶段内部）

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`3001`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

Node 20 + 源码编 sqlite3

## 验证

```bash
docker inspect yunixintel/uptimekuma:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/uptimekuma:loong64 --help 2>/dev/null || true
```
