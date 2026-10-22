# wizarr (loong64) 构建记录

## 结论

- 镜像：`yunixintel/wizarr:loong64` / `:24.10-la5`
- 大小：1.22GB，架构 `linux/loong64`
- 验证：302→`/setup/` 200
- 说明：v2026.10.1；Python 3.13 自编；前端静态资源取自官方 amd64 镜像（架构无关）；5690

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t wizarr:loong64 .
docker tag wizarr:loong64 yunixintel/wizarr:loong64
docker tag wizarr:loong64 yunixintel/wizarr:24.10-la5
docker push yunixintel/wizarr:loong64
docker push yunixintel/wizarr:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS builder`
- 暴露端口：`5690`
- 卷：`["/data"]`
- 默认环境：`PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin ; FLASK_ENV=production     FLASK_APP=run:app     HOST=0.0.0.0     PORT=5690     APP_VERSION=2026.10.1`
- 启动：`["/usr/local/bin/docker-entrypoint.sh"] ["gunicorn","--config","gunicorn.conf.py","--umask","007","run:app"]`

Dockerfile 的上下文依赖：

- `COPY Python-3.13.9.tgz /tmp/`
- `COPY vendor/ /tmp/vendor/`
- `COPY vendor-src/brotli-1.2.0.tar.gz /tmp/`
- `COPY requirements.txt /tmp/requirements.txt`
- `COPY --from=builder /usr/local /usr/local`（构建阶段内部）
- `COPY --from=builder /opt/venv /opt/venv`（构建阶段内部）
- `COPY --chown=wizarr:wizarr wizarr-2026.10.1/ /app/`
- `COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`5690`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2026.10.1；Python 3.13 自编；前端静态资源取自官方 amd64 镜像（架构无关）；5690

## 验证

```bash
docker inspect yunixintel/wizarr:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/wizarr:loong64 --help 2>/dev/null || true
```
