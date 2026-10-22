# linkding (loong64) 构建记录

## 结论

- 镜像：`yunixintel/linkding:loong64` / `:24.10-la5`
- 大小：1.21GB，架构 `linux/loong64`
- 验证：`/login/` 200、`/health` 200
- 说明：v1.47.0；Python 3.13 源码编 + uwsgi；cryptography 需 Rust 源码编；`UWSGI_MAX_FD=4096` 必设（否则 uwsgi 路由进程吃 8GB）

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t linkding:loong64 .
docker tag linkding:loong64 yunixintel/linkding:loong64
docker tag linkding:loong64 yunixintel/linkding:24.10-la5
docker push yunixintel/linkding:loong64
docker push yunixintel/linkding:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS nodebuild`
- 暴露端口：`9090`
- 卷：`["/etc/linkding/data"]`
- 默认环境：`OPENSSL_NO_VENDOR=1 ; PATH=/usr/local/bin:$PATH ; LD_SERVER_HOST=0.0.0.0 ; UWSGI_MAX_FD=4096`
- 启动：`["./bootstrap.sh"]`

Dockerfile 的上下文依赖：

- `COPY src/linkding-1.47.0/package.json src/linkding-1.47.0/package-lock.json ./`
- `COPY src/linkding-1.47.0/bookmarks/frontend ./bookmarks/frontend`
- `COPY src/linkding-1.47.0/bookmarks/styles ./bookmarks/styles`
- `COPY src/Python-${PYTHON_VERSION}.tgz /tmp/Python.tgz`
- `COPY src/icu.c /src/icu.c`
- `COPY --from=pybuild /usr/local /usr/local`（构建阶段内部）
- `COPY src/linkding-1.47.0/ ./`
- `COPY --from=nodebuild /build/bookmarks/static/bundle.js /build/bookmarks/static/bundle.js.map bookmarks/static/`（构建阶段内部）
- `COPY --from=nodebuild /build/bookmarks/static/theme-light.css /build/bookmarks/static/theme-dark.css bookmarks/static/`（构建阶段内部）
- `COPY --from=icubuild /libicu.so ./libicu.so`（构建阶段内部）

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`9090`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v1.47.0；Python 3.13 源码编 + uwsgi；cryptography 需 Rust 源码编；`UWSGI_MAX_FD=4096` 必设（否则 uwsgi 路由进程吃 8GB）

## 验证

```bash
docker inspect yunixintel/linkding:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/linkding:loong64 --help 2>/dev/null || true
```
