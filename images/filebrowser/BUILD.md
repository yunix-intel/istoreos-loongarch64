# filebrowser (loong64) 构建记录

## 结论

- 镜像：`yunixintel/filebrowser:loong64` / `:24.10-la5`
- 大小：290MB，架构 `linux/loong64`
- 验证：`/` 200、`/login` 200
- 说明：v2.63.23 源码编；**上游 2026-09-01 已归档**，无后续安全修复；默认监听改 0.0.0.0（v2.63 默认 127.0.0.1）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t filebrowser:loong64 .
docker tag filebrowser:loong64 yunixintel/filebrowser:loong64
docker tag filebrowser:loong64 yunixintel/filebrowser:24.10-la5
docker push yunixintel/filebrowser:loong64
docker push yunixintel/filebrowser:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 启动：`["/usr/local/bin/filebrowser","-a","0.0.0.0","-d","/database/filebrowser.db","-r","/srv"]`

Dockerfile 的上下文依赖：

- `COPY out/filebrowser /usr/local/bin/filebrowser`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.63.23 源码编；**上游 2026-09-01 已归档**，无后续安全修复；默认监听改 0.0.0.0（v2.63 默认 127.0.0.1）

## 验证

```bash
docker inspect yunixintel/filebrowser:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/filebrowser:loong64 --help 2>/dev/null || true
```
