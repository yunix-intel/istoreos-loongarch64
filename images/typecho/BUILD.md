# typecho (loong64) 构建记录

## 结论

- 镜像：`yunixintel/typecho:loong64` / `:24.10-la5`
- 大小：428MB，架构 `linux/loong64`
- 验证：`/install.php` 200，完整安装验证
- 说明：v1.3.0；PHP 8.3 + nginx/php-fpm；**config.inc.php 与 typecho.db 在站点根目录**（不在挂载卷内，重建容器前需一并备份）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t typecho:loong64 .
docker tag typecho:loong64 yunixintel/typecho:loong64
docker tag typecho:loong64 yunixintel/typecho:24.10-la5
docker push yunixintel/typecho:loong64
docker push yunixintel/typecho:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/var/www/html/usr"]`
- 默认环境：`TZ=UTC \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY typecho-1.3.0.zip /tmp/typecho.zip`
- `COPY deploy/nginx.conf        /etc/nginx/nginx.conf`
- `COPY deploy/typecho.conf      /etc/nginx/conf.d/typecho.conf`
- `COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf`
- `COPY deploy/99-typecho.ini    /etc/php.d/99-typecho.ini`
- `COPY deploy/entrypoint.sh     /entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v1.3.0；PHP 8.3 + nginx/php-fpm；**config.inc.php 与 typecho.db 在站点根目录**（不在挂载卷内，重建容器前需一并备份）

## 验证

```bash
docker inspect yunixintel/typecho:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/typecho:loong64 --help 2>/dev/null || true
```
