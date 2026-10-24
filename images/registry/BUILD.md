# Registry (distribution) (loong64) 构建记录

## 结论

- 镜像：`yunixintel/registry:loong64` / `:24.10-la5`
- 大小：约 124MB（Hub 压缩；本地 381MB）
- digest：`sha256:da519e590805895b3efc3f9b52b7e02d5fa3b5de3774723a4d1068a9c5b40229`
- 版本：distribution `v3.1.2`（commit `3220848`）
- 验证：
  - `/v2/` 匿名 401，admin 认证后可访问
  - `crane copy` 推送 `test/mediamtx:loong64` 成功，digest 与源一致
  - `/v2/_catalog` 返回 `{"repositories":["test/mediamtx"]}`
  - Docker health `healthy`

## 构建链路

1. Go 1.27.2，`CGO_ENABLED=0`，`go build ./cmd/registry`，单二进制约 53MB。
2. 运行阶段 openEuler + `ca-certificates tzdata curl bash shadow util-linux coreutils httpd-tools`；
   `htpasswd` 来自 `httpd-tools`。
3. 非 root 用户 `registry` UID/GID 1121。
4. 配置 `config.yml`：filesystem 存储 `/var/lib/registry`、删除开启、`:5000`、
   health storagedriver 检查。

## 运行时契约

- 端口 5000；卷 `/var/lib/registry`（镜像数据）与 `/auth`（htpasswd、随机密码、HTTP secret）。
- 默认安全策略：首次启动生成 `admin` 用户与 24 字符随机密码：
  - 密码在容器内 `/auth/password`；
  - 可用 `REGISTRY_USER` / `REGISTRY_PASSWORD` 在首次生成时指定；
  - 设置 `REGISTRY_ALLOW_ANONYMOUS=true` 可关闭认证（不建议暴露公网）。
- `REGISTRY_HTTP_SECRET` 首次生成并持久化到 `/auth/http-secret`，避免重启后随机变化。
- 无 TLS；公网必须由 Caddy/Nginx 反代并挂证书。
- 删除镜像需要 registry 配置已开启（本镜像已开），删除后用垃圾回收：
  `registry garbage-collect /etc/registry/config.yml`（容器内执行，先停写）。

## 遇到的问题

- **默认无认证等于开放写入**：distribution 默认匿名可推送；镜像改为首启生成 htpasswd。
- **HTTP secret 随机**：不设置时每次启动生成，日志有 warning；entrypoint 改为持久化。
- **构建输出路径**：仓库根目录已有 `registry/` 目录，`-o /src/registry` 会把二进制写进该目录，
  复制时要注意是 `registry/registry`。
- **Docker CLI 推送**：目标是 HTTP registry 时需在 daemon 配置 `insecure-registries`；
  测试用 `crane --insecure` 完成推送和校验。

## 运行

```bash
docker run -d --name registry -p 5000:5000 \
  -v registry-data:/var/lib/registry \
  -v registry-auth:/auth \
  yunixintel/registry:loong64
docker exec registry cat /auth/password
```

推送示例（crane）：

```bash
crane auth login <host>:5000 -u admin -p "$(docker exec registry cat /auth/password)" --insecure
crane copy yunixintel/mediamtx:loong64 <host>:5000/test/mediamtx:loong64 --insecure
```

如果使用 Docker CLI，先在 `/etc/docker/daemon.json` 添加
`{"insecure-registries":["<host>:5000"]}` 并重启 dockerd。
