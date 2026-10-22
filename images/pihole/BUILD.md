# pihole (loong64) 构建记录

## 结论

- 镜像：`yunixintel/pihole:loong64` / `:24.10-la5`
- 大小：287MB，架构 `linux/loong64`
- 验证：`/admin/` 200；`pihole -g` 拉取 1 条 adlist；`dig` 被拦截域名返回 NXDOMAIN
- 说明：FTL 6.8 + web 6.6.1；C/C++，静态 nettle 3.10；上游 `pihole` CLI + `gravity.sh` + `pihole-adlist`（add/list/remove）；DNS 53 / Web 80；`/etc/pihole`

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t pihole:loong64 .
docker tag pihole:loong64 yunixintel/pihole:loong64
docker tag pihole:loong64 yunixintel/pihole:24.10-la5
docker push yunixintel/pihole:loong64
docker push yunixintel/pihole:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`53/udp 53/tcp 80`
- 卷：`["/etc/pihole"]`
- 启动：`["/docker-entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY pihole-FTL /usr/bin/pihole-FTL`
- `COPY gravity.db.sql /usr/share/pihole/gravity.db.sql`
- `COPY docker-entrypoint.sh /docker-entrypoint.sh`
- `COPY web/ /var/www/html/admin/`
- `COPY cli/pihole /usr/local/bin/pihole`
- `COPY cli/gravity.sh /opt/pihole/gravity.sh`
- `COPY cli/scripts/ /opt/pihole/`
- `COPY cli/advanced /etc/.pihole/advanced`
- `COPY pihole-adlist.sh /usr/local/bin/pihole-adlist`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`53/tcp+udp, 80`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

FTL 6.8 + web 6.6.1；C/C++，静态 nettle 3.10；上游 `pihole` CLI + `gravity.sh` + `pihole-adlist`（add/list/remove）；DNS 53 / Web 80；`/etc/pihole`

## 验证

```bash
docker inspect yunixintel/pihole:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/pihole:loong64 --help 2>/dev/null || true
```
