# paperless-ngx (loong64) 构建记录

## 结论

- 镜像：`yunixintel/paperless-ngx:loong64` / `:24.10-la5`
- 大小：2.53GB，架构 `linux/loong64`
- 验证：302→登录 200；OCR、消费入库、重启持久化通过
- 说明：3.3.2；qpdf 12.4.2 自编（pikepdf 10.17 要求）；tesseract eng/chi_sim/osd；AI 关闭、unpaper 无；单容器含 redis/celery worker/beat/consumer；8000

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t paperless-ngx:loong64 .
docker tag paperless-ngx:loong64 yunixintel/paperless-ngx:loong64
docker tag paperless-ngx:loong64 yunixintel/paperless-ngx:24.10-la5
docker push yunixintel/paperless-ngx:loong64
docker push yunixintel/paperless-ngx:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS qpdf`
- 暴露端口：`8000`
- 卷：`["/data"]`
- 默认环境：`TZ=UTC \`
- 启动：`["/entrypoint.sh"]`

Dockerfile 的上下文依赖：

- `COPY --from=qpdf /usr/local /usr/local`（构建阶段内部）
- `COPY requirements.txt /tmp/requirements.txt`
- `COPY entrypoint.sh /entrypoint.sh`
- `COPY paperless-ngx-3.3.2/src/ ./src/`
- `COPY frontend/ ./src/documents/static/frontend/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

3.3.2；qpdf 12.4.2 自编（pikepdf 10.17 要求）；tesseract eng/chi_sim/osd；AI 关闭、unpaper 无；单容器含 redis/celery worker/beat/consumer；8000

## 验证

```bash
docker inspect yunixintel/paperless-ngx:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/paperless-ngx:loong64 --help 2>/dev/null || true
```
