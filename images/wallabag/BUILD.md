# wallabag (loong64) 构建记录

## 结论

- 镜像：`yunixintel/wallabag:loong64` / `:24.10-la5`
- 大小：688MB，架构 `linux/loong64`
- 验证：`/login` 200，登录与 quickstart 验证
- 说明：2.6.14；PHP 8.3 + nginx/php-fpm；2.6 起无网页安装向导，entrypoint 首次启动 CLI 安装（默认 wallabag/wallabag）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t wallabag:loong64 .
docker tag wallabag:loong64 yunixintel/wallabag:loong64
docker tag wallabag:loong64 yunixintel/wallabag:24.10-la5
docker push yunixintel/wallabag:loong64
docker push yunixintel/wallabag:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/var/www/wallabag/data"]`
- 默认环境：`TZ=UTC \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY wallabag-2.6.14.tar.gz /tmp/wallabag.tar.gz`
- `COPY deploy/nginx.conf        /etc/nginx/nginx.conf`
- `COPY deploy/wallabag.conf     /etc/nginx/conf.d/wallabag.conf`
- `COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf`
- `COPY deploy/99-wallabag.ini   /etc/php.d/99-wallabag.ini`
- `COPY deploy/entrypoint.sh     /entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

2.6.14；PHP 8.3 + nginx/php-fpm；2.6 起无网页安装向导，entrypoint 首次启动 CLI 安装（默认 wallabag/wallabag）

## 验证

```bash
docker inspect yunixintel/wallabag:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/wallabag:loong64 --help 2>/dev/null || true
```
