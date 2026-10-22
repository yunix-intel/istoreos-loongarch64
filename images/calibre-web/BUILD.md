# calibre-web (loong64) 构建记录

## 结论

- 镜像：`yunixintel/calibre-web:loong64` / `:24.10-la5`
- 大小：657MB，架构 `linux/loong64`
- 验证：302→`/login` 200
- 说明：0.6.27；Python 3.11 + Rust 源码编 lxml/nh3/cryptography；8083 端口；书库挂 /books

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t calibre-web:loong64 .
docker tag calibre-web:loong64 yunixintel/calibre-web:loong64
docker tag calibre-web:loong64 yunixintel/calibre-web:24.10-la5
docker push yunixintel/calibre-web:loong64
docker push yunixintel/calibre-web:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS pybuild`
- 暴露端口：`8083`
- 卷：`["/config", "/books"]`
- 默认环境：`OPENSSL_NO_VENDOR=1 ; PATH=/opt/venv/bin:$PATH \`
- 启动：`["python3", "/app/cps.py"]`

Dockerfile 的上下文依赖：

- `COPY src/calibre-web-0.6.27/requirements.txt /tmp/requirements.txt`
- `COPY --from=pybuild /opt/venv /opt/venv`（构建阶段内部）
- `COPY src/calibre-web-0.6.27 /app`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8083`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

0.6.27；Python 3.11 + Rust 源码编 lxml/nh3/cryptography；8083 端口；书库挂 /books

## 验证

```bash
docker inspect yunixintel/calibre-web:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/calibre-web:loong64 --help 2>/dev/null || true
```
