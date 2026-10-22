# portainer (loong64) 构建记录

## 结论

- 镜像：`yunixintel/portainer:loong64` / `:24.10-la5`
- 大小：373MB，架构 `linux/loong64`
- 验证：200
- 说明：2.45.2 LTS；Go 自编 + 前端本机 pnpm/webpack；需挂 docker.sock；9000

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t portainer:loong64 .
docker tag portainer:loong64 yunixintel/portainer:loong64
docker tag portainer:loong64 yunixintel/portainer:24.10-la5
docker push yunixintel/portainer:loong64
docker push yunixintel/portainer:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`9000 ; 9443 ; 8000`
- 卷：`/data`
- 启动：`["/portainer"]`

Dockerfile 的上下文依赖：

- `COPY src/dist/portainer /portainer`
- `COPY src/dist/public /public`
- `COPY src/dist/mustache-templates /mustache-templates`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`9000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

2.45.2 LTS；Go 自编 + 前端本机 pnpm/webpack；需挂 docker.sock；9000

## 验证

```bash
docker inspect yunixintel/portainer:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/portainer:loong64 --help 2>/dev/null || true
```
