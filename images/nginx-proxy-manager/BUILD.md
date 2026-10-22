# nginx-proxy-manager (loong64) 构建记录

## 结论

- 镜像：`yunixintel/nginx-proxy-manager:loong64` / `:24.10-la5`
- 大小：774MB，架构 `linux/loong64`
- 验证：200，`/api/` OK
- 说明：v2.16.0；Node 22 + nginx；前端在 x64 编 dist；自写 entrypoint 替代 s6-overlay；81/443

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t nginx-proxy-manager:loong64 .
docker tag nginx-proxy-manager:loong64 yunixintel/nginx-proxy-manager:loong64
docker tag nginx-proxy-manager:loong64 yunixintel/nginx-proxy-manager:24.10-la5
docker push yunixintel/nginx-proxy-manager:loong64
docker push yunixintel/nginx-proxy-manager:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03 AS builder`
- 暴露端口：`80 81 443`
- 卷：`[ "/data" ]`
- 默认环境：`PATH=/opt/node22/bin:$PATH ; npm_config_build_from_source=true \ ; PATH=/opt/node22/bin:$PATH \`
- 启动：`[ "/usr/local/bin/entrypoint.sh" ]`

Dockerfile 的上下文依赖：

- `COPY node22/ /opt/node22/`
- `COPY backend/package.json backend/yarn.lock ./`
- `COPY backend/ /app/`
- `COPY node22/ /opt/node22/`
- `COPY --from=builder /app /app`（构建阶段内部）
- `COPY frontend-dist/ /app/frontend/`
- `COPY rootfs/ /`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`81/443`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.16.0；Node 22 + nginx；前端在 x64 编 dist；自写 entrypoint 替代 s6-overlay；81/443

## 验证

```bash
docker inspect yunixintel/nginx-proxy-manager:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/nginx-proxy-manager:loong64 --help 2>/dev/null || true
```
