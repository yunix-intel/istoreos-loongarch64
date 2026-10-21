# restic REST server 0.14.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/rest-server:loong64` / `:24.10-la5`
- 大小：250MB，`linux/loong64`
- digest：`sha256:536244337de0bd0925559d4623716c9f18b3d31491f0346d52d59f985de1a19a`
- 版本：rest-server 0.14.0（Go 1.27.2 静态编）
- 验证：`POST /repo/?create=true` 200、config 写入/读取、Basic 认证 401/200、
  `rest-server --version` 正常。

## 构建

```bash
# 龙芯上编静态二进制
export GOROOT=/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64
export PATH=$GOROOT/bin:$PATH GOTOOLCHAIN=local GOPROXY=https://goproxy.cn,direct
export GOCACHE=/build/gocache GOTMPDIR=/build/gotmp
unset GOFLAGS
CGO_ENABLED=0 GOOS=linux GOARCH=loong64 \
  go build -trimpath -ldflags '-s -w' -o rest-server ./cmd/rest-server

# 镜像
docker build -t rest-server:loong64 .
docker tag rest-server:loong64 yunixintel/rest-server:loong64
docker tag rest-server:loong64 yunixintel/rest-server:24.10-la5
docker push yunixintel/rest-server:loong64
docker push yunixintel/rest-server:24.10-la5
```

openEuler 没有 Alpine 的 `apache2-utils`，`htpasswd` 由 `httpd-tools` 提供。
`rest-server` 本体是 12MB 静态二进制；镜像其余体积来自 openEuler 基础和
`httpd-tools`。

## 运行

```bash
docker run -d --name rest-server -p 8000:8000 \
  -v restic-data:/data yunixintel/rest-server:loong64
```

首次启动日志会提示没有用户：

```bash
docker exec rest-server create_user backup 'change-me'
docker restart rest-server
```

- 认证默认开启，密码文件 `/data/.htpasswd`（bcrypt）。
- 完全内网可关闭认证：`-e DISABLE_AUTHENTICATION=1`。
- 数据目录 `/data`，端口 8000；容器以 root 运行以简化卷权限。
- 可追加 rest-server 参数，例如只增不删：

```bash
docker run ... yunixintel/rest-server:loong64 --append-only
```

- `create_user` 修改 htpasswd 后需重启容器才会生效（服务启动时加载文件）。

## restic 客户端用法

```bash
export RESTIC_REPOSITORY=rest:http://backup:change-me@<host>:8000/myrepo/
restic init
restic backup /path/to/data
restic snapshots
```

注意 URL 末尾的 `/`；仓库名会成为 `/data` 下的子目录。

## 注意

- 本镜像只提供 HTTP，不含 TLS；公网使用必须放在 Caddy/Nginx 反向代理后，
  并确保代理传递 `Authorization` 头。
- 无内置用户配额；多租户场景需要额外限额或分实例。
- `--append-only` 可防止客户端删除快照，但不会限制磁盘占用。
- 没有内置健康检查命令；用 `curl -f http://127.0.0.1:8000/` 从宿主检查
  （无认证时 200，有认证时 401 也说明服务在监听）。
- 备份数据目录本身不要放在会被 restic 再次备份的路径里，避免递归。

## 验证命令

```bash
curl -sS -u backup:change-me -o /dev/null -w '%{http_code}\n' \
  -X POST 'http://127.0.0.1:8000/testrepo/?create=true'
printf '{"version":2,"id":"0123456789abcdef","chunker_polynomial":"3da3358b4dc173"}' >/tmp/cfg
curl -sS -u backup:change-me -H 'Content-Type: application/octet-stream' \
  -X POST --data-binary @/tmp/cfg http://127.0.0.1:8000/testrepo/config
curl -sS -u backup:change-me http://127.0.0.1:8000/testrepo/config
docker exec rest-server /usr/bin/rest-server --version
```
