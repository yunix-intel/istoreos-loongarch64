# syncthing (loong64) 构建记录

## 结论

- 镜像：`yunixintel/syncthing:loong64` / `:24.10-la5`
- 大小：273MB，架构 `linux/loong64`
- 验证：HTTP 200
- 说明：v2.1.6 官方 loong64 包；注意 v2 CLI 用双横线 `--home=`

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t syncthing:loong64 .
docker tag syncthing:loong64 yunixintel/syncthing:loong64
docker tag syncthing:loong64 yunixintel/syncthing:24.10-la5
docker push yunixintel/syncthing:loong64
docker push yunixintel/syncthing:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8384 22000 21027/udp`
- 卷：`["/var/syncthing"]`
- 默认环境：`TZ=Asia/Shanghai`
- 启动：`["/usr/local/bin/syncthing", "--home=/var/syncthing", "--gui-address=0.0.0.0:8384"]`

Dockerfile 的上下文依赖：

- `COPY pkg/syncthing-linux-loong64-v2.1.6/syncthing /usr/local/bin/syncthing`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8384`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v2.1.6 官方 loong64 包；注意 v2 CLI 用双横线 `--home=`

## 验证

```bash
docker inspect yunixintel/syncthing:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/syncthing:loong64 --help 2>/dev/null || true
```
