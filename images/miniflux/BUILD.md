# miniflux (loong64) 构建记录

## 结论

- 镜像：`yunixintel/miniflux:loong64` / `:24.10-la5`
- 大小：290MB，架构 `linux/loong64`
- 验证：200（**仅 PostgreSQL**）
- 说明：v2.3.3；上游已删 SQLite 支持，必须提供 PostgreSQL DSN；8080

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：2.3.3
- 关键步骤：上游删 SQLite，必须外接 PostgreSQL

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.3.3；上游已删 SQLite 支持，必须提供 PostgreSQL DSN；8080

## 验证

```bash
docker inspect yunixintel/miniflux:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/miniflux:loong64 --help 2>/dev/null || true
```
