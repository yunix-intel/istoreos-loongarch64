# memos (loong64) 构建记录

## 结论

- 镜像：`yunixintel/memos:loong64` / `:24.10-la5`
- 大小：352MB，架构 `linux/loong64`
- 验证：`/` 200、`/healthz` 200
- 说明：v0.31.0 源码编（官方无 loong64）；纯 Go sqlite；前端在 x64 上编（rolldown 无 loong64 binding），产物架构无关

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：v0.31.0
- 关键步骤：Go 源码编；前端在 x64 编（rolldown 无 loong64）

## 运行

端口/挂载：`5230`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.31.0 源码编（官方无 loong64）；纯 Go sqlite；前端在 x64 上编（rolldown 无 loong64 binding），产物架构无关

## 验证

```bash
docker inspect yunixintel/memos:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/memos:loong64 --help 2>/dev/null || true
```
