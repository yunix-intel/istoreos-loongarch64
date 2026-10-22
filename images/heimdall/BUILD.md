# heimdall (loong64) 构建记录

## 结论

- 镜像：`yunixintel/heimdall:loong64` / `:24.10-la5`
- 大小：691MB，架构 `linux/loong64`
- 验证：200
- 说明：2.8.3；PHP 8.4.26 自编（源里只有 8.3）+ nginx/php-fpm；数据在 /config（.env/sqlite/storage）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t heimdall:loong64 .
docker tag heimdall:loong64 yunixintel/heimdall:loong64
docker tag heimdall:loong64 yunixintel/heimdall:24.10-la5
docker push yunixintel/heimdall:loong64
docker push yunixintel/heimdall:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS php-build`
- 暴露端口：`8080`
- 卷：`["/config"]`
- 默认环境：`PATH=/usr/local/php/bin:/usr/local/php/sbin:$PATH \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY --from=php-build /usr/local/php /usr/local/php`（构建阶段内部）
- `COPY --from=php-build /usr/local/bin/composer /usr/local/bin/composer`（构建阶段内部）
- `COPY src /var/www/html`
- `COPY deploy/nginx.conf /etc/nginx/nginx.conf`
- `COPY deploy/heimdall.conf /etc/nginx/conf.d/heimdall.conf`
- `COPY deploy/php-fpm.conf /usr/local/php/etc/php-fpm.conf`
- `COPY deploy/php.ini /usr/local/php/etc/php.ini`
- `COPY deploy/entrypoint.sh /entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

2.8.3；PHP 8.4.26 自编（源里只有 8.3）+ nginx/php-fpm；数据在 /config（.env/sqlite/storage）

## 验证

```bash
docker inspect yunixintel/heimdall:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/heimdall:loong64 --help 2>/dev/null || true
```
