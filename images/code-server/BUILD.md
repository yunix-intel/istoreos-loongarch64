# code-server (loong64) 构建记录

## 结论

- 镜像：`yunixintel/code-server:loong64` / `:24.10-la5`
- 大小：1.11GB，架构 `linux/loong64`
- 验证：200（或 302 登录）
- 说明：4.141.0 + VS Code 1.141；**必须 Node 24**（Node 20 缺 `module.registerHooks`）；自编静态 ripgrep 15.2

## 构建

> 该早期镜像未保留 Dockerfile，以下为归档配方，完整步骤见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 第 3 节。

- 上游/版本：4.141.0 + VS Code 1.141
- 关键步骤：必须 Node 24；自编静态 ripgrep 15.2

## 运行

端口/挂载：`8443`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

4.141.0 + VS Code 1.141；**必须 Node 24**（Node 20 缺 `module.registerHooks`）；自编静态 ripgrep 15.2

## 验证

```bash
docker inspect yunixintel/code-server:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/code-server:loong64 --help 2>/dev/null || true
```
