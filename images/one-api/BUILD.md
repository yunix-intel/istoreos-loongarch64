# one-api (loong64) 构建记录

## 结论

- 镜像：`yunixintel/one-api:loong64` / `:24.10-la5`
- 大小：294MB，架构 `linux/loong64`
- 验证：`/` 200、`/api/status` 返回版本
- 说明：v0.6.10；三套前端主题本机编；go-sqlite3 需 CGO 静态链接（`-linkmode external -extldflags -static`）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t one-api:loong64 .
docker tag one-api:loong64 yunixintel/one-api:loong64
docker tag one-api:loong64 yunixintel/one-api:24.10-la5
docker push yunixintel/one-api:loong64
docker push yunixintel/one-api:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`3000`
- 卷：`["/data"]`
- 默认环境：`TZ=Asia/Shanghai`
- 启动：`["/one-api"] ["--port", "3000", "--log-dir", "/data/logs"]`

Dockerfile 的上下文依赖：

- `COPY one-api /one-api`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`3000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.6.10；三套前端主题本机编；go-sqlite3 需 CGO 静态链接（`-linkmode external -extldflags -static`）

## 验证

```bash
docker inspect yunixintel/one-api:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/one-api:loong64 --help 2>/dev/null || true
```
