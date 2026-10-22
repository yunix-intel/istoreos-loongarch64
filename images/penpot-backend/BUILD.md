# Penpot backend 2.18.3 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/penpot-backend:loong64` / `:24.10-la5`
- Hub 压缩大小：约 710MB
- digest：`sha256:96eb7b46198807ec957e592e8fd2d4436c22f545e02c06e7a3cf26492e210bfe`
- 版本：Penpot 2.18.3（`bundle-backend` uberjar）
- 验证：连接 PostgreSQL 15 + Redis，全部迁移执行到 `0153`，
  backend 监听 6060，前端 `/api` 代理返回 200

## 构建链路

Penpot 官方后端镜像是 amd64/arm64 的 Debian + 自带 JRE 26，无法在龙芯运行。
但后端主体是 **JVM 字节码**，可以做“取 bundle、换 JRE”的移植：

1. 用 `crane export --platform linux/amd64 penpotapp/backend:latest`
   解包官方镜像，只取 `/opt/penpot/backend`（约 194MB）。
2. 检查 `penpot.jar` 内 AOT class 的 major version 为 **65（Java 21）**，
   说明虽然官方用 JDK 26/27 打包，产物仍兼容 Java 21。
3. 运行阶段基于 `openeuler/openeuler:24.03`，安装
   `java-21-openjdk-headless fontconfig fontforge ImageMagick librsvg2
   python3 python3-tabulate woff2`。
4. 自写 entrypoint，不再使用官方 `run.sh`（它写死了
   `--sun-misc-unsafe-memory-access` 等 JDK 24+ 参数），改为：

   ```bash
   java -Djava.util.logging.manager=org.apache.logging.log4j.jul.LogManager \
        -Dlog4j2.configurationFile=log4j2.xml \
        -XX:-OmitStackTraceInFastThrow -XX:+ExitOnOutOfMemoryError \
        -jar penpot.jar -m app.main
   ```

## 说明与限制

- 需要外部 PostgreSQL 与 Redis；镜像本身不包含数据库。
- 官方 `imagick` 目录是 x86 二进制，未复制；改用 openEuler 的
  ImageMagick 7。缩略图/导出基本可用，但字体渲染与官方镜像可能有细微差异。
- `PENPOT_SECRET_KEY` 必须设置，否则 entrypoint 直接报错退出。
- 导出 PDF/PNG 需要单独的 `penpot-exporter`（内含 Chromium）。
  本仓库暂未提供 loong64 exporter；前端会把 `/api/export` 代理到
  `PENPOT_EXPORTER_URI`，未部署时该功能 502。
- 官方 admin-console / MCP 未移植；用
  `PENPOT_FLAGS=disable-email-verification disable-secure-session-cookies`
  即可正常注册和绘图。

## 运行（与 frontend 一起）

```bash
docker network create penpot

docker run -d --name penpot-postgres --network penpot \
  -e POSTGRES_DB=penpot -e POSTGRES_USER=penpot -e POSTGRES_PASSWORD=penpot \
  -v penpot-pg:/var/lib/postgresql/data yunixintel/postgres:loong64

docker run -d --name penpot-redis --network penpot yunixintel/redis:loong64

docker run -d --name penpot-backend --network penpot \
  -e PENPOT_PUBLIC_URI=http://<host>:9001 \
  -e PENPOT_SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(64))')" \
  -e PENPOT_DATABASE_URI=postgresql://penpot-postgres/penpot \
  -e PENPOT_DATABASE_USERNAME=penpot \
  -e PENPOT_DATABASE_PASSWORD=penpot \
  -e PENPOT_REDIS_URI=redis://penpot-redis/0 \
  -e PENPOT_FLAGS="disable-email-verification disable-secure-session-cookies" \
  -v penpot-assets:/opt/data/assets yunixintel/penpot-backend:loong64

docker run -d --name penpot-frontend --network penpot -p 9001:8080 \
  -e PENPOT_PUBLIC_URI=http://<host>:9001 \
  -e PENPOT_BACKEND_URI=http://penpot-backend:6060 \
  -e PENPOT_FLAGS="disable-email-verification disable-secure-session-cookies" \
  yunixintel/penpot-frontend:loong64
```

- 数据库首次启动会自动迁移，日志出现 `app.util.migrations` 即正常。
- `PENPOT_PUBLIC_URI` 必须与浏览器实际访问地址一致，否则 WebSocket/邀请链接错误。
- PostgreSQL 建议单独卷持久化；Redis 只做通知，可不持久化。
- 前端说明见 [../penpot-frontend/BUILD.md](../penpot-frontend/BUILD.md)。
