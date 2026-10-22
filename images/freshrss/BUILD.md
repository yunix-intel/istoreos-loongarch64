# freshrss (loong64) 构建记录

## 结论

- 镜像：`yunixintel/freshrss:loong64` / `:24.10-la5`
- 大小：—（Hub 154MB 压缩），架构 `linux/loong64`
- 验证：302→登录页
- 说明：1.30.1；PHP 8.3 + nginx/php-fpm；SQLite 自动安装（admin/adminadmin）；8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t freshrss:loong64 .
docker tag freshrss:loong64 yunixintel/freshrss:loong64
docker tag freshrss:loong64 yunixintel/freshrss:24.10-la5
docker push yunixintel/freshrss:loong64
docker push yunixintel/freshrss:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/var/www/FreshRSS/data"]`
- 默认环境：`TZ=UTC \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY freshrss-1.30.1.tar.gz /tmp/freshrss.tar.gz`
- `COPY deploy/nginx.conf        /etc/nginx/nginx.conf`
- `COPY deploy/freshrss.conf     /etc/nginx/conf.d/freshrss.conf`
- `COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf`
- `COPY deploy/99-freshrss.ini   /etc/php.d/99-freshrss.ini`
- `COPY deploy/entrypoint.sh     /entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

1.30.1；PHP 8.3 + nginx/php-fpm；SQLite 自动安装（admin/adminadmin）；8080

## 验证

```bash
docker inspect yunixintel/freshrss:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/freshrss:loong64 --help 2>/dev/null || true
```
