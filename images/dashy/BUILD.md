# dashy (loong64) 构建记录

## 结论

- 镜像：`yunixintel/dashy:loong64` / `:24.10-la5`
- 大小：379MB，架构 `linux/loong64`
- 验证：HTTP 200，title/conf 正常
- 说明：4.8.0；官方预构建 `dist/` + nginx 1.24；配置挂载 `/usr/share/nginx/html/conf.yml`；8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t dashy:loong64 .
docker tag dashy:loong64 yunixintel/dashy:loong64
docker tag dashy:loong64 yunixintel/dashy:24.10-la5
docker push yunixintel/dashy:loong64
docker push yunixintel/dashy:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 启动：`["nginx", "-g", "daemon off;"]`

Dockerfile 的上下文依赖：

- `COPY dist/ /usr/share/nginx/html/`
- `COPY nginx.conf /etc/nginx/nginx.conf`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

4.8.0；官方预构建 `dist/` + nginx 1.24；配置挂载 `/usr/share/nginx/html/conf.yml`；8080

## 验证

```bash
docker inspect yunixintel/dashy:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/dashy:loong64 --help 2>/dev/null || true
```
