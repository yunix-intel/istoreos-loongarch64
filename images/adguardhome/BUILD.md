# adguardhome (loong64) 构建记录

## 结论

- 镜像：`yunixintel/adguardhome:loong64` / `:24.10-la5`
- 大小：290MB，架构 `linux/loong64`
- 验证：302→200
- 说明：官方无 loong64 资产，源码自编 + 官方前端；53 端口需映射避让宿主 dnsmasq

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：AdGuardHome 源码 + 官方前端
- 关键步骤：Go 编；官方无 loong64 资产；53 端口需避让宿主 dnsmasq

## 运行

端口/挂载：`53/tcp+udp, 3000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

官方无 loong64 资产，源码自编 + 官方前端；53 端口需映射避让宿主 dnsmasq

## 验证

```bash
docker inspect yunixintel/adguardhome:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/adguardhome:loong64 --help 2>/dev/null || true
```
