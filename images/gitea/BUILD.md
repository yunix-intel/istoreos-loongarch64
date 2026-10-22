# gitea (loong64) 构建记录

## 结论

- 镜像：`yunixintel/gitea:loong64` / `:24.10-la5`
- 大小：666MB，架构 `linux/loong64`
- 验证：200（安装页/SQLite 已验）
- 说明：v28.2.0；Go 1.27 自编；modernc SQLite；入口脚本生成 app.ini；3000

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：v28.2.0
- 关键步骤：Go 1.27 编；modernc SQLite；入口生成 app.ini

## 运行

端口/挂载：`3000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v28.2.0；Go 1.27 自编；modernc SQLite；入口脚本生成 app.ini；3000

## 验证

```bash
docker inspect yunixintel/gitea:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/gitea:loong64 --help 2>/dev/null || true
```
