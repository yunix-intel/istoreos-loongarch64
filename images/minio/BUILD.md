# MinIO RELEASE.2025-10-15T17-29-55Z (loong64) 构建记录

## 结论

- 镜像：`yunixintel/minio:loong64` / `:24.10-la5`
- 大小：483MB，`linux/loong64`
- digest：`sha256:df0708edf3da360ee3db36c8f626be15792c40e94abf7ff3286690a5c6389348`
- 版本：MinIO RELEASE.2025-10-15T17-29-55Z，Go 1.27.2
- 验证：`/minio/health/live` 200、Console `:9001` 200、数据目录初始化、
  `minio --version` 显示 RELEASE、健康检查 healthy、缺少凭据时明确报错。

## 构建

MinIO 官方没有 loong64 二进制，从源码构建：

```bash
export GOROOT=/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64
export PATH=$GOROOT/bin:$PATH GOTOOLCHAIN=local GOPROXY=https://goproxy.cn,direct
export GOCACHE=/build/gocache GOTMPDIR=/build/gotmp
unset GOFLAGS

commit=$(git rev-parse HEAD)
short=$(git rev-parse --short HEAD)
ldflags="-s -w \
  -X github.com/minio/minio/cmd.Version=2025-10-15T17:29:55Z \
  -X github.com/minio/minio/cmd.CopyrightYear=2025 \
  -X github.com/minio/minio/cmd.ReleaseTag=RELEASE.2025-10-15T17-29-55Z \
  -X github.com/minio/minio/cmd.CommitID=$commit \
  -X github.com/minio/minio/cmd.ShortCommitID=$short"

CGO_ENABLED=0 GOOS=linux GOARCH=loong64 \
  go build -tags kqueue -trimpath --ldflags "$ldflags" -o minio .
```

`buildscripts/gen-ldflags.go` 会从 git 描述生成版本；直接用它时 ReleaseTag 可能是
`DEVELOPMENT.*`。本镜像显式覆盖为 `RELEASE.2025-10-15T17-29-55Z`，版本串才是正式发布格式。

镜像基于 openEuler 24.03，二进制放 `/usr/bin/minio`，以 UID 1000（`minio`）运行。

```bash
docker build -t minio:loong64 .
docker tag minio:loong64 yunixintel/minio:loong64
docker tag minio:loong64 yunixintel/minio:24.10-la5
docker push yunixintel/minio:loong64
docker push yunixintel/minio:24.10-la5
```

## 运行

必须提供 root 凭据，镜像不会生成默认密码：

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD='change-me-123' \
  -v minio-data:/data \
  yunixintel/minio:loong64
```

- S3 API：`http://<host>:9000`
- Console：`http://<host>:9001`
- 数据目录：`/data`；挂宿主目录需 `chown -R 1000:1000 <dir>`。
- 可选 `MINIO_ADDRESS`、`MINIO_CONSOLE_ADDRESS` 覆盖监听地址；默认 `:9000`/`:9001`。
- `MINIO_UPDATE=off` 已设为默认，避免容器内自动更新尝试。

## 注意

- 单目录/单盘模式只会给出 “host failure” 警告，不具备纠删码冗余；生产 NAS 建议
  用多盘路径或分布式部署，并做好备份。
- 镜像只提供 HTTP；公网必须放在 Caddy/Nginx 反向代理后并启用 TLS。
- MinIO 使用 GNU AGPLv3，分发/修改需遵守其许可证。
- Console 和 S3 API 都应限制来源；不要使用示例密码。
- 健康检查只检查 `9000` 的 live 端点；如果改了 `MINIO_ADDRESS` 端口，需要同步改动
  HEALTHCHECK。
- 备份不能只拷 `/data` 中正在写入的对象；生产应使用 `mc mirror`/版本控制或快照。

## 验证命令

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9000/minio/health/live
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9001/
docker exec minio /usr/bin/minio --version
docker exec minio ls -la /data
docker restart minio
```
