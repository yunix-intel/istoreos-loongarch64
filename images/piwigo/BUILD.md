# Piwigo 16.4.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/piwigo:loong64` / `:24.10-la5`
- 大小：约 550MB（Hub 压缩 179MB）
- digest：`sha256:289fca6c1f21c72c7b17a8e7964a2094058b00e5190c95b8de7d1922c4d8f8b9`
- 版本：Piwigo 16.4.0
- 验证：
  - 首次启动自动执行 `install.php`，生成 `local/config/database.inc.php`
  - MariaDB 中 `piwigo_users` 2 行（admin + guest），`/` 200、`/identification.php` 200
  - 健康检查 healthy
  - 未做实际照片上传/缩略图生成

## 构建链路

1. 源码 `Piwigo/Piwigo` 16.4.0（git tag）。
2. 运行阶段 openEuler + `nginx php-fpm php-cli php-pdo php-mysqlnd
   php-mbstring php-xml php-gd php-curl php-intl php-opcache php-pecl-zip`。
3. 应用目录 `/var/www/piwigo`；nginx + php-fpm 由 entrypoint 启动。
4. 运行用户 `nginx`；可写目录 `local`、`_data`、`galleries`、`upload`。

## 自动安装

entrypoint 等待 MariaDB 后，向 `http://127.0.0.1/install.php` POST：

- `dbhost/dbuser/dbpasswd/dbname`
- `admin_name/admin_pass1/admin_pass2/admin_mail`
- `prefix=piwigo_`

安装成功后生成 `local/config/database.inc.php`；失败则保留 Web 安装向导。

## 遇到的问题

- **PHP 扩展**：Piwigo 需要 mysqli/PDO MySQL、gd、mbstring、xml、zip；
  `php-pecl-zip` 需单独安装（和整组 PHP 包一起装会 no match）。
- **首次安装是 Web 流程**：没有官方 CLI 安装器；用 curl POST `install.php`
  可以自动化，但必须等 php-fpm/nginx 起来。
- **可写目录**：`local/config`、`_data`、`galleries`、`upload` 必须由 nginx 用户可写，
  否则安装/缩略图失败。
- **数据库必须 MariaDB/MySQL**；不要用 SQLite。

## 运行

```bash
docker network create piwigo
docker run -d --name piwigo-db --network piwigo \
  -e MYSQL_ROOT_PASSWORD='change-me' -e MYSQL_DATABASE=piwigo \
  -e MYSQL_USER=piwigo -e MYSQL_PASSWORD='piwigo-pass' \
  -v piwigo-db:/var/lib/mysql yunixintel/mariadb:loong64

docker run -d --name piwigo --network piwigo -p 8080:80 \
  -e PIWIGO_DB_HOST=piwigo-db -e PIWIGO_DB_NAME=piwigo \
  -e PIWIGO_DB_USER=piwigo -e PIWIGO_DB_PASSWORD='piwigo-pass' \
  -e PIWIGO_ADMIN_USER=admin -e PIWIGO_ADMIN_PASSWORD='change-me' \
  -e PIWIGO_ADMIN_EMAIL=admin@example.com \
  -v piwigo-local:/var/www/piwigo/local \
  -v piwigo-data:/var/www/piwigo/_data \
  -v piwigo-galleries:/var/www/piwigo/galleries \
  -v piwigo-upload:/var/www/piwigo/upload \
  yunixintel/piwigo:loong64
```

- Web：`http://<host>:8080/`，管理员 `/identification.php`。
- 首次启动自动安装；若安装失败，打开 `/install.php` 手动完成。
- `galleries` 是原图目录，`_data` 是缓存/编译模板，`local` 存数据库配置，
  三者必须持久化。
- 默认无 TLS；公网放在反代之后。
