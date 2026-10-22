# vaultwarden (loong64) 构建记录

## 结论

- 镜像：`yunixintel/vaultwarden:loong64` / `:24.10-la5`
- 大小：357MB，架构 `linux/loong64`
- 验证：Rocket launched + Web 200
- 说明：Rust；镜像内置宿主 glibc 2.41 闭包（显式 loader 启动）

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：1.35.x
- 关键步骤：Rust 编后带 GLIBC_2.39 引用；镜像内置宿主 glibc 2.41 闭包并显式 loader

## 运行

端口/挂载：`8443`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

Rust；镜像内置宿主 glibc 2.41 闭包（显式 loader 启动）

## 验证

```bash
docker inspect yunixintel/vaultwarden:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/vaultwarden:loong64 --help 2>/dev/null || true
```
