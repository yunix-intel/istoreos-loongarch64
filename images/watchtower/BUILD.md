# watchtower (loong64) 构建记录

## 结论

- 镜像：`yunixintel/watchtower:loong64` / `:24.10-la5`
- 大小：14.7MB，架构 `linux/loong64`
- 验证：`--help`；`--run-once --label-enable` 扫描 0 容器
- 说明：v1.7.1；Go 静态二进制 + CA 证书；需挂 `/var/run/docker.sock`；`--label-enable` 只更新带标签容器

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t watchtower:loong64 .
docker tag watchtower:loong64 yunixintel/watchtower:loong64
docker tag watchtower:loong64 yunixintel/watchtower:24.10-la5
docker push yunixintel/watchtower:loong64
docker push yunixintel/watchtower:24.10-la5
```

- 基础镜像：`scratch`
- 暴露端口：未在 Dockerfile 声明
- 启动：`["/watchtower"]`

Dockerfile 的上下文依赖：

- `COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt`
- `COPY watchtower /watchtower`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`—`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v1.7.1；Go 静态二进制 + CA 证书；需挂 `/var/run/docker.sock`；`--label-enable` 只更新带标签容器

## 验证

```bash
docker inspect yunixintel/watchtower:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/watchtower:loong64 --help 2>/dev/null || true
```
