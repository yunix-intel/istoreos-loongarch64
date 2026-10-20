# MariaDB 10.11.18 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/mariadb:loong64` / `:24.10-la5`
- 大小：549MB，`linux/loong64`
- digest：`sha256:bf37b65e30b60bf323c981ebeea49c6b495e68582ee37c29f935ceb2da435e00`
- 版本：MariaDB 10.11.18（openEuler 24.03 SP4）
- 验证：首次初始化、root/app 用户 TCP 登录、建表、重启持久化、健康检查；
  密码含单引号、反斜杠、空格时仍可登录。

## 构建

```bash
docker build -t mariadb:loong64 .
docker tag mariadb:loong64 yunixintel/mariadb:loong64
docker tag mariadb:loong64 yunixintel/mariadb:24.10-la5
docker push yunixintel/mariadb:loong64
docker push yunixintel/mariadb:24.10-la5
```

openEuler 提供 MariaDB 10.11 LTS，官方 `mariadb` 镜像没有 loong64 资产，因此基于
`mariadb-server` + `mariadb` 客户端构建。镜像内还包含 `util-linux`（`runuser`）、
CA 和时区数据。

## entrypoint 行为

首次启动（`/var/lib/mysql/mysql` 不存在）：

1. 检查 `MYSQL_ROOT_PASSWORD`；除非 `MYSQL_ALLOW_EMPTY_PASSWORD=yes`，否则缺失即退出。
2. `mariadb-install-db --user=mysql --auth-root-authentication-method=normal`。
3. 启动一个 `--skip-networking` 的临时实例，通过 socket 执行：
   - `ALTER USER 'root'@'localhost' IDENTIFIED BY ...`
   - `CREATE DATABASE IF NOT EXISTS ...`（`MYSQL_DATABASE`）
   - `CREATE USER ...@'%' IDENTIFIED BY ...`（`MYSQL_USER`/`MYSQL_PASSWORD`）
   - `GRANT ALL PRIVILEGES ON <db>.* TO ...`
4. 关闭临时实例，降权到 `mysql`（UID/GID 27）启动 `mariadbd`。

密码/用户名通过 `SET SESSION sql_mode=...,NO_BACKSLASH_ESCAPES` 加单引号加倍来转义，
因此 `'`、`\`、空格都不会破坏初始化 SQL。

## 启动

```bash
docker run -d --name mariadb \
  -e MYSQL_ROOT_PASSWORD='change-me' \
  -e MYSQL_DATABASE=appdb \
  -e MYSQL_USER=app -e MYSQL_PASSWORD='app-pass' \
  -p 3306:3306 -v mariadb-data:/var/lib/mysql \
  yunixintel/mariadb:loong64
```

- 应用连接：`app` / `app-pass`，数据库 `appdb`，主机 `<host>`，端口 `3306`。
- root 只允许从容器内 `localhost` 登录；需要远程 root 请自行创建管理用户。
- 字符集固定 `utf8mb4` / `utf8mb4_unicode_ci`。
- 数据目录 `/var/lib/mysql`，socket `/run/mysqld/mysqld.sock`；镜像内的
  `/etc/my.cnf.d/container-client.cnf` 已让客户端默认使用该 socket。

## 注意

- 挂载宿主目录时需 `chown -R 27:27 <dir>`；命名卷无需手工处理。
- `MYSQL_USER` 存在但 `MYSQL_DATABASE` 为空时不会授予库权限；两者应成对设置。
- 日志通过 `/var/log/mariadb/mariadb.log -> /dev/stderr` 输出，
  `docker logs mariadb` 可直接查看启动和错误日志。
- 容器只初始化一次；修改 `MYSQL_*` 环境变量不会改变已有数据目录中的账号。
- 备份用 `mariadb-dump`，不要直接复制运行中的数据目录。
- 该镜像面向单实例；主从/集群需要另行配置 server-id、binlog 和复制账号。

## 验证命令

```bash
docker exec -e MYSQL_PWD=change-me mariadb mariadb -u root -e 'select version()'
docker exec -e MYSQL_PWD=app-pass mariadb mariadb -u app appdb -e 'select 1'
docker restart mariadb
docker exec -e MYSQL_PWD=app-pass mariadb mariadb -u app appdb -e 'show tables'
```
