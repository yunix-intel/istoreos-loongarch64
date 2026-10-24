# SFTPGo v2.7.6 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/sftpgo:loong64` / `:24.10-la5`
- 大小：422MB（Hub 压缩约 149MB）
- digest：`sha256:6e35b029a766266fccfe91e30d5ad27dd60d05f3104c5febf9d0ac6c59ca8919`
- 版本：SFTPGo v2.7.6
- 验证：
  - Web `/` 302 → 登录/首次安装页；首次安装 POST 302，管理员登录后 `/web/admin/users` 200
  - SQLite `sftpgo.db` 在 `/var/lib/sftpgo` 生成
  - SFTP 端口 2022 监听，自动生成 RSA/ECDSA/ED25519 host key
  - 健康检查 healthy
  - 未做真实 SFTP 上传测试（需要创建用户并配置目录）

## 构建链路

1. 源码 `drakkan/sftpgo` v2.7.6。
2. 在 openEuler 24.03 容器内用 Go 1.27.2 + `gcc sqlite-devel`，
   `CGO_ENABLED=1 go build -trimpath -ldflags "-s -w ..."`，SQLite 静态链入。
3. 运行阶段 openEuler + `sqlite-libs curl tzdata shadow util-linux`；
   复制 `/usr/share/sftpgo/{templates,static,openapi}` 和 `sftpgo.json`。
4. 配置默认：
   - `users_base_dir=/srv/sftpgo/data`
   - `backups_path=/srv/sftpgo/backups`
   - Web 8080、SFTP 2022、FTP/WebDAV 默认关闭
5. 运行用户 `sftpgo` UID/GID 1103，工作目录 `/var/lib/sftpgo`。

## 遇到的问题

- **SQLite 相对路径**：默认数据库名是 `sftpgo.db`，相对于进程工作目录。
  entrypoint 不 `cd /var/lib/sftpgo` 时会报
  `unable to open database file: no such file or directory`。
- **默认不创建管理员**：`create_default_admin=false`，首次访问进入
  `/web/admin/setup` 安装页；创建管理员后才会跳转登录。
- **运行资产不能漏**：`templates/`、`static/`、`openapi/`、`sftpgo.json`
  必须在运行镜像里，否则 Web UI 空白或 500。
- **CGO 构建**：SQLite 驱动需要 CGO；在宿主编译会引入 Loongnix 2.41 glibc
  依赖，必须在 openEuler 24.03 容器内编。

## 运行

```bash
docker run -d --name sftpgo \
  -p 8080:8080 -p 2022:2022 \
  -v sftpgo-data:/srv/sftpgo/data \
  -v sftpgo-db:/var/lib/sftpgo \
  -v sftpgo-backups:/srv/sftpgo/backups \
  yunixintel/sftpgo:loong64
```

- Web 管理/客户端：`http://<host>:8080/`。
- SFTP：`sftp -P 2022 <user>@<host>`。
- 首次访问 Web 进入 `/web/admin/setup` 创建管理员（**没有默认密码**）。
- `/srv/sftpgo/data` 是用户文件根目录；`/var/lib/sftpgo` 存 SQLite 与 host key，
  必须持久化，否则重启后 host key/用户丢失。
- FTP/WebDAV 默认端口为 0（关闭）；需要时改 `sftpgo.json` 或环境变量。
- 公网使用必须配 TLS 或放在反代之后；默认 Web 无 HTTPS。
