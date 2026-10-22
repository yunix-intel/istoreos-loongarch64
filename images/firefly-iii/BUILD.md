# firefly-iii (loong64) 构建记录

## 结论

- 镜像：`yunixintel/firefly-iii:loong64` / `:24.10-la5`
- 大小：821MB，架构 `linux/loong64`
- 验证：302→`/install` 200
- 说明：v6.7.9；PHP 8.5 自编（上游要求 ≥8.5）+ nginx；SQLite 自动迁移/种子；8080

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：v6.7.9
- 关键步骤：openEuler 只有 PHP 8.3，builder 阶段源码编 PHP 8.5；SQLite 迁移/种子

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v6.7.9；PHP 8.5 自编（上游要求 ≥8.5）+ nginx；SQLite 自动迁移/种子；8080

## 验证

```bash
docker inspect yunixintel/firefly-iii:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/firefly-iii:loong64 --help 2>/dev/null || true
```
