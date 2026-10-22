# homer (loong64) 构建记录

## 结论

- 镜像：`yunixintel/homer:loong64` / `:24.10-la5`
- 大小：371MB，架构 `linux/loong64`
- 验证：HTTP 200，title/config 正常
- 说明：v26.08.3；openEuler nginx 1.24 + 官方静态包；8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t homer:loong64 .
docker tag homer:loong64 yunixintel/homer:loong64
docker tag homer:loong64 yunixintel/homer:24.10-la5
docker push yunixintel/homer:loong64
docker push yunixintel/homer:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 启动：`["nginx", "-g", "daemon off;"]`

Dockerfile 的上下文依赖：

- `COPY nginx.conf /etc/nginx/nginx.conf`
- `COPY config.yml /usr/share/nginx/html/assets/config.yml`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v26.08.3；openEuler nginx 1.24 + 官方静态包；8080

## 验证

```bash
docker inspect yunixintel/homer:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/homer:loong64 --help 2>/dev/null || true
```
