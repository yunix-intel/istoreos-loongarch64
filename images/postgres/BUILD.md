# PostgreSQL 15.18 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/postgres:loong64` / `:24.10-la5`
- 大小：378MB，`linux/loong64`
- digest：`sha256:c94527eee9603beccbbbe7acacca0fca1e6f2faffa5cf22d575df9af49dc825b`
- 版本：PostgreSQL 15.18（openEuler 24.03 SP4 包）
- 验证：`initdb` + SCRAM 认证、TCP 远程登录、重启持久化、健康检查；
  miniflux 用该库执行 132 个迁移后首页 200。

## 为什么用 openEuler 包

官方 `postgres` 镜像没有 loong64 资产。openEuler 24.03 SP4 自带
`postgresql-server 15.18`，与镜像的 glibc 2.38 完全匹配；源码重编不会带来
15.x 内的功能收益，反而增加维护面。需要 16/17 时再按同样 entrypoint 换源码。

## 构建

```bash
docker build -t postgres:loong64 .
docker tag postgres:loong64 yunixintel/postgres:loong64
docker tag postgres:loong64 yunixintel/postgres:24.10-la5
docker push yunixintel/postgres:loong64
docker push yunixintel/postgres:24.10-la5
```

镜像内包含 `postgresql-server`、`postgresql-contrib`、`util-linux`（提供
`runuser`）、CA 与时区数据。

## entrypoint 行为

- 数据目录 `PGDATA` 默认 `/var/lib/postgresql/data`，与官方镜像路径一致。
- 首次启动自动 `initdb`：
  - `POSTGRES_USER`（默认 `postgres`）作为超级用户；
  - `POSTGRES_PASSWORD` 写入临时 `--pwfile`，initdb 后立即删除；
  - `POSTGRES_DB`（默认等于 `POSTGRES_USER`）自动创建；
  - `POSTGRES_HOST_AUTH_METHOD` 默认 `scram-sha-256`，可选 `trust`。
- `pg_hba.conf` 追加 `host all all all <method>`，允许容器网络访问；
  仅本机 socket 保持 `trust`，方便初始化。
- `listen_addresses='*'`、socket 固定在 `/var/run/postgresql`，并关闭
  `logging_collector`，让日志继续走 stdout/stderr（`docker logs` 可看）。
- 启动时用 `runuser -u postgres -- postgres ...` 降权，PID 1 仍是 postgres。

## 启动

```bash
docker run -d --name postgres \
  -e POSTGRES_USER=app -e POSTGRES_PASSWORD='change-me' -e POSTGRES_DB=appdb \
  -p 5432:5432 -v pgdata:/var/lib/postgresql/data \
  yunixintel/postgres:loong64
```

连接串：

```text
postgres://app:change-me@<host>:5432/appdb?sslmode=disable
```

## 注意

- 挂载宿主目录时必须 `chown -R postgres:postgres <dir>`（镜像内是 UID 26）。
  用命名卷时 Docker 会复制镜像目录属主，无需手工处理。
- 数据目录不能有除 `lost+found` 以外的文件，否则 initdb 拒绝初始化；
  挂载 ext4 分区时建议用子目录。
- 未设置 `POSTGRES_PASSWORD` 且认证方式不是 `trust` 时，容器会明确报错退出。
- 备份用 `pg_dump`/`pg_dumpall`，不要直接拷运行中的数据目录。
- 该镜像没有 `gosu`，用 util-linux 的 `runuser`；不要删掉 `util-linux`。

## 验证命令

```bash
docker exec postgres pg_isready -U app -d appdb
docker exec -e PGPASSWORD=change-me postgres \
  psql -h 127.0.0.1 -U app -d appdb -c 'select version()'
docker restart postgres && docker exec postgres \
  psql -U app -d appdb -c 'select 1'
```
