# nextcloud (loong64) 构建记录

## 结论

- 镜像：`yunixintel/nextcloud:loong64` / `:24.10-la5`
- 大小：1.48GB，架构 `linux/loong64`
- 验证：`status.php` 200（installed=false，安装向导）
- 说明：33.0.10；PHP 8.3 + nginx/php-fpm；SQLite（测试用，生产建议 MySQL/MariaDB）；首次启动生成 config.php

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t nextcloud:loong64 .
docker tag nextcloud:loong64 yunixintel/nextcloud:loong64
docker tag nextcloud:loong64 yunixintel/nextcloud:24.10-la5
docker push yunixintel/nextcloud:loong64
docker push yunixintel/nextcloud:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/var/www/html/data", "/var/www/html/config"]`
- 默认环境：`TZ=UTC \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY nextcloud-33.0.10.tar.bz2 /tmp/nextcloud.tar.bz2`
- `COPY deploy/nginx.conf        /etc/nginx/nginx.conf`
- `COPY deploy/nextcloud.conf    /etc/nginx/conf.d/nextcloud.conf`
- `COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf`
- `COPY deploy/99-nextcloud.ini  /etc/php.d/99-nextcloud.ini`
- `COPY deploy/entrypoint.sh     /entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

33.0.10；PHP 8.3 + nginx/php-fpm；SQLite（测试用，生产建议 MySQL/MariaDB）；首次启动生成 config.php

## 验证

```bash
docker inspect yunixintel/nextcloud:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/nextcloud:loong64 --help 2>/dev/null || true
```
