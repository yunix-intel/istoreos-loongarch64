# homeassistant (loong64) 构建记录

## 结论

- 镜像：`yunixintel/homeassistant:loong64` / `:24.10-la5`
- 大小：2.53GB，架构 `linux/loong64`
- 验证：302→`/onboarding.html` 200
- 说明：Core 2026.10.2；Python 3.14 自编；cryptography/grpcio/Pillow/aiohttp 等全源码编；cloud/camera 集成需运行期编译器，未预装

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t homeassistant:loong64 .
docker tag homeassistant:loong64 yunixintel/homeassistant:loong64
docker tag homeassistant:loong64 yunixintel/homeassistant:24.10-la5
docker push yunixintel/homeassistant:loong64
docker push yunixintel/homeassistant:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8123`
- 卷：`["/config"]`
- 默认环境：`PATH=/usr/local/ha-venv/bin:/usr/local/bin:$PATH \`
- 启动：`["python3", "-m", "homeassistant", "--config", "/config"]`

Dockerfile 的上下文依赖：

- `COPY usrlocal/ /usr/local/`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8123`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

Core 2026.10.2；Python 3.14 自编；cryptography/grpcio/Pillow/aiohttp 等全源码编；cloud/camera 集成需运行期编译器，未预装

## 验证

```bash
docker inspect yunixintel/homeassistant:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/homeassistant:loong64 --help 2>/dev/null || true
```
