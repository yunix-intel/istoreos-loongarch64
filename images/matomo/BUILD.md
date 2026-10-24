# Matomo 5.14.2 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/matomo:loong64` / `:24.10-la5`
- 大小：约 193MB（Hub 压缩）
- digest：`sha256:b1e7baec9556f5c04f73f9d6c13d1839f0951eceb4113650627d934ca5881bc2`
- 版本：Matomo 5.14.2（官方完整包，含 vendor）
- 验证：
  - `/index.php` 200、安装向导可打开、健康检查 healthy
  - `php -m` 确认 pdo_mysql/gd/mbstring/zip/intl/bcmath 存在
  - 未完成 Web 安装向导的数据库/管理员/站点配置

## 构建链路

1. 下载官方完整包 `https://builds.matomo.org/matomo.zip`（含 vendor）。
2. 运行阶段 openEuler + `nginx php-fpm php-cli php-pdo php-mysqlnd
   php-mbstring php-xml php-gd php-curl php-intl php-bcmath php-opcache`；
   `php-pecl-zip` 单独安装。
3. 应用目录 `/var/www/matomo`；nginx + php-fpm 由 entrypoint 启动。
4. 运行用户 `nginx`；可写 `config/`、`tmp/`。

## 安装

Matomo 没有 CLI 安装器，首次打开 `/index.php` 走 Web 向导：

1. 系统检查；
2. 填 MariaDB/MySQL 地址、库、用户、密码；
3. 建超级用户；
4. 建第一个站点。

`config/config.ini.php` 由向导生成，必须持久化。

## 遇到的问题

- **`php-pecl-zip` 不能和整组 PHP 包一起装**：dnf 会报 no match；分两步安装。
- **没有 CLI install**：`console` 只有 `core:update`，没有 `core:install`；
  自动化安装需要模拟多步 Web 表单，本镜像保留向导。
- **`config/`/`tmp/` 必须可写**：否则向导无法保存配置/缓存。
- **必须 MariaDB/MySQL**；不要用 SQLite 替代。

## 运行

```bash
docker network create matomo
docker run -d --name matomo-db --network matomo \
  -e MYSQL_ROOT_PASSWORD='change-me' -e MYSQL_DATABASE=matomo \
  -e MYSQL_USER=matomo -e MYSQL_PASSWORD='matomo-pass' \
  -v matomo-db:/var/lib/mysql yunixintel/mariadb:loong64

docker run -d --name matomo --network matomo -p 8080:80 \
  -v matomo-config:/var/www/matomo/config \
  -v matomo-tmp:/var/www/matomo/tmp \
  yunixintel/matomo:loong64
```

- Web：`http://<host>:8080/index.php`；首次打开安装向导。
- DB 主机填 `matomo-db`，库/用户/密码与上面一致。
- `config`、`tmp` 必须持久化；`config/config.ini.php` 丢失会要求重装。
- 归档任务建议宿主 cron 执行：
  `docker exec matomo php /var/www/matomo/console core:archive --url=http://<host>:8080/`
- 默认无 TLS；公网放在反代之后。
