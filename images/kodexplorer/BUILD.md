# kodexplorer (loong64) 构建记录

## 结论

- 镜像：`yunixintel/kodexplorer:loong64` / `:24.10-la5`
- 大小：507MB，架构 `linux/loong64`
- 验证：302→登录 200
- 说明：4.55；PHP 8.3 + nginx/php-fpm；首启为环境检查/设置管理员；默认 admin/admin

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t kodexplorer:loong64 .
docker tag kodexplorer:loong64 yunixintel/kodexplorer:loong64
docker tag kodexplorer:loong64 yunixintel/kodexplorer:24.10-la5
docker push yunixintel/kodexplorer:loong64
docker push yunixintel/kodexplorer:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/var/www/html/data"]`
- 默认环境：`TZ=UTC \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY kodexplorer-4.55.tar.gz /tmp/kodexplorer.tar.gz`
- `COPY deploy/nginx.conf        /etc/nginx/nginx.conf`
- `COPY deploy/kodexplorer.conf  /etc/nginx/conf.d/kodexplorer.conf`
- `COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf`
- `COPY deploy/99-kodexplorer.ini /etc/php.d/99-kodexplorer.ini`
- `COPY deploy/entrypoint.sh     /entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

4.55；PHP 8.3 + nginx/php-fpm；首启为环境检查/设置管理员；默认 admin/admin

## 验证

```bash
docker inspect yunixintel/kodexplorer:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/kodexplorer:loong64 --help 2>/dev/null || true
```
