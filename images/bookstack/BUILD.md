# BookStack v26.09.2 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/bookstack:loong64` / `:24.10-la5`
- 大小：约 600MB（Hub 压缩 214MB）
- digest：`sha256:20304871bd43fbb3aa2f453795f8e096232b3fb669d5d617e1530112e580efba`
- 版本：BookStack v26.09.2
- 验证：
  - MariaDB 10.11 下全部迁移执行完成
  - `/login` 200，健康检查 healthy
  - `bookstack:create-admin --initial` 创建管理员成功
  - 未做浏览器内“建书/写页/搜索”完整手工流程

## 构建链路

1. 源码 `BookStackApp/BookStack` v26.09.2；`public/dist` 已随仓库提供，无需 npm 构建。
2. 在 openEuler 容器内用 Composer 装生产依赖：
   `composer install --no-dev --prefer-dist --optimize-autoloader`。
3. 运行阶段 openEuler + `nginx php-fpm php-cli php-pdo php-mysqlnd php-mbstring
   php-xml php-gd php-curl php-intl php-pecl-zip php-opcache`。
4. nginx + php-fpm 由 entrypoint 启动；php-fpm `listen=127.0.0.1:9000`。
5. 运行用户 `nginx`；应用目录 `/var/www/bookstack`。

## 遇到的问题

- **`php-pecl-zip` 不能和整组 PHP 包一起装**：dnf 在混合版本里报
  `No match for argument: php-pecl-zip`；分两步安装即可。
- **metalink 导致 update 仓库超时**：openEuler 的 metalink 可能指向不可达镜像；
  构建时注释 `metalink=`，只用 aliyun `baseurl`。
- **Composer post-install 需要 PDO**：只装 `php-cli` 会报 `Class "PDO" not found`；
  必须加 `php-pdo`（以及运行期 `php-mysqlnd`）。
- **`.env` 不能当卷**：entrypoint 每次从环境变量生成 `.env`；
  `APP_KEY` 持久化到 `storage/app.key`（0600），否则重建容器后会话/加密失效。
- **数据库等待**：entrypoint 用 PDO 重试 60 次，避免 MariaDB 未就绪时迁移失败。

## 运行

```bash
docker network create bookstack

docker run -d --name bookstack-db --network bookstack \
  -e MYSQL_ROOT_PASSWORD='change-me' \
  -e MYSQL_DATABASE=bookstack \
  -e MYSQL_USER=bookstack -e MYSQL_PASSWORD='bookpass' \
  -v bookstack-db:/var/lib/mysql yunixintel/mariadb:loong64

docker run -d --name bookstack --network bookstack -p 8080:80 \
  -e APP_URL=http://<host>:8080 \
  -e DB_HOST=bookstack-db -e DB_DATABASE=bookstack \
  -e DB_USERNAME=bookstack -e DB_PASSWORD='bookpass' \
  -v bookstack-storage:/var/www/bookstack/storage \
  -v bookstack-uploads:/var/www/bookstack/public/uploads \
  yunixintel/bookstack:loong64
```

- Web：`http://<host>:8080/`。
- 首次创建管理员：

```bash
docker exec -u nginx -w /var/www/bookstack bookstack \
  php artisan bookstack:create-admin --email=admin@example.com \
  --name=Admin --password='change-me' --initial
```

- `/var/www/bookstack/storage` 存缓存/日志/`app.key`；`public/uploads` 存上传图片，
  两者必须持久化。
- 必须外接 MariaDB/MySQL；不支持 SQLite。
- 默认无 TLS；公网必须放在反代之后。
