# Komga 1.29.1 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/komga:loong64` / `:24.10-la5`
- 本地大小：687,927,754 B（约 656 MiB）；Hub 压缩后 333,721,998 B（约 318 MiB）
- 镜像 ID：`sha256:7a5f8283b4be6d1790c98d257f65d87cc3b0c1f3e40c3330371f7d7310876a1f`
- Registry digest（两 tag 相同）：
  `sha256:0cf05b7ec54e94d135e16e18f4e2c8ee5c9518167e09ea685a03a2f5b6cd9e7a`
- 架构：`linux/loong64`
- 验证：
  - 三个 SQLite 库共 94 + 2 + 1 个 Flyway 迁移完成
  - `/` = 200；`/actuator/health` = `{"status":"UP"}`；Docker health = `healthy`
  - 重启后书库/书籍仍在（`books` = 1，状态 `READY`）
  - 最小 CBZ 扫描成功：1 个系列、1 本书、1 页；阅读页 1 返回 200 `image/png`
  - Java 进程 UID/GID = 1110；`/data` 以只读方式挂载也能正常启动

## 版本与校验和

| 组件 | 版本 | SHA-256 |
|---|---|---|
| Komga 官方 jar | 1.29.1 | `e9cafae1ec6d0d117c2375fff9ecb737ed384eede2afea9716bcb555d96ea834` |
| sqlite-jdbc 源码 tar.gz | 3.53.4.0 | `9dded7305b4f3bab596d6a40eaab0cf0d3afad60006eb80073492103b06b081c` |
| SQLite amalgamation | 3.53.4 / `3530400` | `1e71ddf93849c6a6ecf58b827c0692073d2dd7ee40196158068f7b29f422e87d` |
| 编译出的 `libsqlitejdbc.so` | — | `8c850b6c26cdf8de44d83a5fbd9880db3b3a1afab2aea33768cfc355e479f697` |

运行阶段：openEuler 24.03 SP4 + `java-21-openjdk-headless 21.0.11`（BiSheng）。
Komga jar 为纯 JVM 字节码（`Build-Jdk-Spec: 21`），唯一需要重编的 native 是 sqlite-jdbc。

## 构建

```bash
cd images/komga
./build.sh                      # 默认 classic builder，避免 BuildKit 缓存占用
# 等价于：
DOCKER_BUILDKIT=0 docker build --network=host \
  -t yunixintel/komga:loong64 -t yunixintel/komga:24.10-la5 .
```

Dockerfile 分两阶段，所有上游文件都在构建期下载并用 `sha256sum -c` 校验：

1. `sqlite-native`：openEuler 24.03 + gcc/make/perl/zip/curl + `java-21-openjdk-devel`；
   下载 sqlite-jdbc 3.53.4.0 源码与 `sqlite-amalgamation-3530400.zip`；
   预置到 `target/` 后执行：

   ```bash
   JAVA_HOME=/usr/lib/jvm/java-21-openjdk \
     make OS_NAME=Linux OS_ARCH=loongarch64 native
   ```

   - 必须显式传 `OS_NAME=Linux`：自动探测在本机会得到空值，产物路径会变成
     `native//loongarch64`。
   - `Linux-loongarch64` 不在上游 `known_targets`，Makefile 回落到 `Default` 参数：
     `-Os -fPIC -fvisibility=hidden -shared -static-libgcc -pthread -lm`。
   - 沿用上游宏：FTS5、RTREE、JSON/数学函数、列元数据、`LOAD_EXTENSION`、
     `SQLITE_ENABLE_UPDATE_DELETE_LIMIT`、`SQLITE_MAX_VARIABLE_NUMBER=250000` 等。
   - 实测编译约 37 秒，产物 1,198,904 B，ELF64 LoongArch，61 个 `Java_org_sqlite_*` 符号。
2. 运行阶段：安装 `java-21-openjdk-headless curl tzdata util-linux ca-certificates`，
   创建 UID/GID 1110 的 `komga` 用户，复制官方 jar 与 `.so`。

## 运行时契约

- 端口：25600
- 卷：`/config`（SQLite、Lucene、日志）、`/data`（漫画库，可只读）
- 用户：UID/GID 1110；entrypoint 以 root 修正 `/config` 所有权（必要时递归），
  对 `/data` 仅尝试 chown（只读挂载失败可忽略），随后 `runuser -u komga` 降权
- 环境：
  - `KOMGA_CONFIGDIR=/config`
  - `JAVA_OPTS` 默认含
    `-Dorg.sqlite.lib.path=/opt/komga/native -Dorg.sqlite.lib.name=libsqlitejdbc.so`
  - entrypoint 会检查 `JAVA_OPTS`；即使调用方覆盖，也会补回上述 native 参数
  - 启动参数含 `-Dspring.profiles.include=docker`（启用持久化会话库）
- 健康检查：
  `curl -fsS http://127.0.0.1:25600/actuator/health | grep -q '"status":"UP"'`
  启动期 120 秒内失败不计入重试。

```bash
docker run -d --name komga -p 25600:25600 \
  -v /srv/komga/config:/config \
  -v /srv/comics:/data:ro \
  yunixintel/komga:loong64
```

首次打开 `http://<host>:25600/` 创建管理员；也可调用
`POST /api/v1/claim`（头 `X-Komga-Email` / `X-Komga-Password`）。

## 测试记录（2026-10-24/25，Host A）

1. 全新启动：日志出现 `Database: jdbc:sqlite:/config/database.sqlite (SQLite 3.53)`，
   主库 94、tasks 2、sessions 1 个迁移全部成功；`Started ApplicationKt` 用时 28–39 秒
   （构建机负载波动）。
2. HTTP：`/` = 200，`/actuator/health` = `{"status":"UP"}`，Docker health = `healthy`。
3. CBZ 扫描（最小 64×64 PNG 打包为 `Test Series/Test 001.cbz`，挂载到 `/data`）：
   `GET /api/v1/series` → 1；`GET /api/v1/books` → 1，`pagesCount=1`，`status=READY`；
   `GET /api/v1/books/<id>/pages/1` → 200 `image/png`。
4. 重启：同一 `/config` 卷重启后书籍仍为 1、状态 `READY`，迁移只做 validate，不重复执行。
5. 只读 `/data` 挂载：启动、健康检查、既有书籍读取均正常。
6. 进程：`docker top` 中 Java 进程 USER = 1110。

## 推送

```bash
docker save yunixintel/komga:loong64 -o /tmp/komga-loong64.tar
export HTTPS_PROXY=http://127.0.0.1:17890
/build/bin/crane push /tmp/komga-loong64.tar docker.io/yunixintel/komga:loong64
/build/bin/crane push /tmp/komga-loong64.tar docker.io/yunixintel/komga:24.10-la5
```

验证：两 tag digest 均为
`sha256:0cf05b7ec54e94d135e16e18f4e2c8ee5c9518167e09ea685a03a2f5b6cd9e7a`；
`crane config` 返回 `architecture=loong64`、`os=linux`。

## 限制与未验证

- **已补验（2026-10-25）**：CBZ/PDF/EPUB、RAR4（junrar）、只读 `/data`、首用户 `/api/v1/claim` 均通过；EPUB `/pages/1` 500 是设计行为，阅读走 `/manifest/epub`。
- **HEIF/JXL 不可用**：JDK 21 下 nightmonkeys 插件日志为
  `only supports Java 22, plugin will be disabled`。WebP 仍由 TwelveMonkeys 纯 Java 支持。
- **Kobo 转换不可用**：镜像没有 `kepubify`（无 loong64 官方二进制），启动时有 WARN；
  EPUB/普通阅读不受影响。
- **未验证**：PDF、EPUB、RAR/CBR、HEIF/JXL 封面、Kobo/KOReader 同步、大库扫描性能、
  多用户权限。CBZ 的扫描与单页读取已验证。
- 官方 jar 未修改；若改为把 `.so` 嵌入 jar，嵌套 jar 必须以 Stored（`zip -0`）写入，
  否则 Spring Boot 会报 `NoClassDefFoundError: org/sqlite/SQLiteConfig$JournalMode`。
- 升级 Komga 时需同步检查 `gradle/libs.versions.toml` 的 `sqliteJdbc` 版本，
  并重算本文件中的校验和。

## 文件

- `Dockerfile`：两阶段构建；构建期下载并校验所有上游文件
- `docker-entrypoint.sh`：目录/权限准备、native 参数兜底、`runuser` 降权
- `build.sh`：`docker build` 双 tag 入口
