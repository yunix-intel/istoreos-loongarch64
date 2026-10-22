# mihomo (loong64) 构建记录

## 结论

- 镜像：`yunixintel/mihomo:loong64` / `:24.10-la5`
- 大小：59MB，架构 `linux/loong64`
- 验证：204 / 152ms
- 说明：scratch 单二进制，配置需挂载

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：上游 loong64 release
- 关键步骤：scratch + 单二进制；配置挂载 `/etc/mihomo`

## 运行

端口/挂载：`—`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

scratch 单二进制，配置需挂载

## 验证

```bash
docker inspect yunixintel/mihomo:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/mihomo:loong64 --help 2>/dev/null || true
```
