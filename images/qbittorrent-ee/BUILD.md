# qbittorrent-ee (loong64) 构建记录

## 结论

- 镜像：`yunixintel/qbittorrent-ee:loong64` / `:24.10-la5`
- 大小：289MB，架构 `linux/loong64`
- 验证：200（Host 需匹配端口）
- 说明：v5.2.4.10 官方 loong64 静态包；Host header 校验会拒绝端口映射不一致的访问，建议 `--webui-port` 与映射端口一致

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t qbittorrent-ee:loong64 .
docker tag qbittorrent-ee:loong64 yunixintel/qbittorrent-ee:loong64
docker tag qbittorrent-ee:loong64 yunixintel/qbittorrent-ee:24.10-la5
docker push yunixintel/qbittorrent-ee:loong64
docker push yunixintel/qbittorrent-ee:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080 6881 6881/udp`
- 卷：`["/config", "/downloads"]`
- 启动：`["/usr/bin/qbittorrent-nox", "--profile=/config", "--webui-port=8080"]`

Dockerfile 的上下文依赖：

- `COPY extract/qbittorrent-nox /usr/bin/qbittorrent-nox`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v5.2.4.10 官方 loong64 静态包；Host header 校验会拒绝端口映射不一致的访问，建议 `--webui-port` 与映射端口一致

## 验证

```bash
docker inspect yunixintel/qbittorrent-ee:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/qbittorrent-ee:loong64 --help 2>/dev/null || true
```
