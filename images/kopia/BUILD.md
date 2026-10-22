# kopia (loong64) 构建记录

## 结论

- 镜像：`yunixintel/kopia:loong64` / `:24.10-la5`
- 大小：317MB，架构 `linux/loong64`
- 验证：401（Basic 认证）→ 200
- 说明：v0.23.1 源码编；为 loong64 打了 Stat_t.Dev/Rdev 类型补丁；Web UI 强制 Basic 认证（默认 admin/kopia）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t kopia:loong64 .
docker tag kopia:loong64 yunixintel/kopia:loong64
docker tag kopia:loong64 yunixintel/kopia:24.10-la5
docker push yunixintel/kopia:loong64
docker push yunixintel/kopia:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`51515`
- 默认环境：`KOPIA_CONFIG_PATH=/app/config/repository.config \`
- 启动：`["/usr/bin/kopia"] ["server","start","--insecure","--address=0.0.0.0:51515","--server-username=admin","--server-password=kopia"]`

Dockerfile 的上下文依赖：

- `COPY kopia /usr/bin/kopia`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`51515`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v0.23.1 源码编；为 loong64 打了 Stat_t.Dev/Rdev 类型补丁；Web UI 强制 Basic 认证（默认 admin/kopia）

## 验证

```bash
docker inspect yunixintel/kopia:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/kopia:loong64 --help 2>/dev/null || true
```
