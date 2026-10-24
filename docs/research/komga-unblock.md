# Komga on LoongArch64：sqlite-jdbc 解锁报告

日期：2026-10-24。基于 Komga 1.29.1 源码/官方 jar 与 xerial sqlite-jdbc 3.53.4.0 的实际检查，
并在 Host A（3A6000 / Loongnix 25 / 内核 6.6.52-loong64 / 16 KiB 页）的 openEuler 24.03
容器中完成编译、JNI 冒烟测试与 Komga 端到端启动验证。

## 1. 结论（Go / No-Go）

**GO。** 不需要 Gradle/Node 也能出镜像：使用官方 `komga-1.29.1.jar`（纯 JVM 字节码），
另编 loongarch64 的 `libsqlitejdbc.so`，用 `-Dorg.sqlite.lib.path` 外挂即可。
已验证 Komga 完成 94 个主库迁移、2 个任务库迁移、1 个会话库迁移，HTTP 200、健康检查 UP，
重启后数据保留。预计 2–3 人日（native 0.5 天已由本次验证覆盖，镜像 1 天，扫描/阅读/文档 1 天）。
前置条件：**固定 Komga 1.29.1 + JDK 21**；HEIF/JXL 封面不可用，Kobo 转换需另编 kepubify。

## 2. 版本与构建要求（2026-10-24 核实）

| 项 | 值 |
|---|---|
| 最新稳定版 | **1.29.1**，2026-10-14；`komga-1.29.1.jar` 126,827,620 B，sha256 `e9cafae1…96ea834` |
| 构建 | Gradle **9.8.1**、Kotlin 2.4.10、JDK **21**（jar 内 `Build-Jdk-Spec: 21`） |
| 框架 | Spring Boot 3.5.16、jOOQ 3.19.35、Flyway 13.1.0、Lucene 9.9.1 |
| 数据库 | **sqlite-jdbc 3.53.4.0**（SQLite 3.53.4），无 PostgreSQL/MySQL 支持 |
| 前端 | `next-ui`：Node **24**、Vite 8.3.4；`komga-webui`：Node **22**、Vue CLI |
| 产物路径 | `next-ui/dist/`、`komga-webui/dist/` → Gradle 复制到 `komga/src/main/resources/public/`，`index-next.html` 单独生成 |
| 构建命令 | `npm ci && npm run build:with-i18n`；`npm ci && npm run build`；`./gradlew :komga:bootJar` |
| 运行 | 官方镜像用 JDK 25；jar 清单已含 `Enable-Native-Access: ALL-UNNAMED` |

**外部数据库：不支持。** 源码硬编码 `SQLiteDataSource`、`org.sqlite.JDBC`、`jdbc:sqlite:`，
直接用 `SQLiteConfig`/`SQLiteConnection`/`Function`/`Collation`；Flyway 只有 `db/migration/sqlite`，
全仓库无 postgres/mysql 引用。改 PostgreSQL 是重写，不是配置项。
**前端不能在 loong64 直接构建**：Vite 8 的 Rolldown 无 `@rolldown/binding-linux-loong64-gnu`
（npm registry 404），源码构建需在 x86 产出 `dist`/jar；镜像可直接用官方 jar。

## 3. 阻塞点复核

`sqlite-jdbc-3.53.4.0.jar` 的 `org/sqlite/native/Linux/` 只有 `x86`、`x86_64`、`aarch64`、
`arm`、`armv6`、`armv7`、`ppc64`、`riscv64`，**没有 loongarch64**。未注入 native 时实测：

```text
os.arch=loongarch64
SEVERE: Failed to load native library through System.loadLibrary
java.lang.UnsatisfiedLinkError: no sqlitejdbc in java.library.path
```

`SQLiteJDBCLoader` 加载顺序（3.53.4.0 源码）：① `org.sqlite.lib.path` + `org.sqlite.lib.name`
（path 为目录、name 为文件名）；② jar 内 `org/sqlite/native/<OS>/<arch>/libsqlitejdbc.so`，
解压到临时目录后 `System.load`；③ `java.library.path`；④ `System.loadLibrary`。
另有 `org.sqlite.osinfo.architecture` 可覆盖架构名，本方案不需要。

## 4. 方案排序

### A. 自编 loongarch64 `libsqlitejdbc.so`（推荐，已验证）

JNI 源文件只有 `src/main/java/org/sqlite/core/NativeDB.java`（`javac -h` 生成 `NativeDB.h`）
与 `NativeDB.c`；SQLite 侧为 3.53.4 的 `sqlite3.c`，并把 `src/main/ext/extension-functions.c`
追加进去。必须沿用上游 Makefile 的宏（FTS5、RTREE、JSON/数学函数、列元数据、LOAD_EXTENSION、
`SQLITE_ENABLE_UPDATE_DELETE_LIMIT`、`SQLITE_MAX_VARIABLE_NUMBER=250000` 等），不要手写精简版。

```bash
# openEuler 24.03 内执行（glibc 2.38，与运行镜像一致）
dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source \
  --disablerepo=update-source --setopt=retries=1 --setopt=timeout=20 \
  --setopt=install_weak_deps=False gcc make perl zip unzip curl java-21-openjdk-devel
curl -fsSL -o src.tgz https://github.com/xerial/sqlite-jdbc/archive/refs/tags/3.53.4.0.tar.gz
tar xzf src.tgz
curl -fsSL -o sqlite-amalgamation-3530400.zip \
  https://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip
cd sqlite-jdbc-3.53.4.0 && mkdir -p target && cp ../sqlite-amalgamation-3530400.zip target/
JAVA_HOME=/usr/lib/jvm/java-21-openjdk make OS_NAME=Linux OS_ARCH=loongarch64 native
# 产物 src/main/resources/org/sqlite/native/Linux/loongarch64/libsqlitejdbc.so
```

实测：37 秒；1,198,904 B，ELF64 LoongArch，61 个 `Java_org_sqlite_*` 导出符号，
sha256 `8c850b6c…79f697`。`OS_NAME` 必须显式传——自动探测在本机得到空值，会生成
`native//loongarch64`；`Linux-loongarch64` 不在上游 `known_targets` 中，会回落 `Default`
编译参数（`-Os -fPIC -fvisibility=hidden -shared -static-libgcc -pthread -lm`），实测可用。

### B. 换 JDBC 驱动 / 外部数据库（不可行）

- 无带 loongarch64 的 sqlite-jdbc 分支或发行版；natives-all 也只是同一组平台。
- 纯 Java SQLite JDBC（如 SQLJet）不兼容 Komga 直接使用的 `org.sqlite.*` API，
  且方言/迁移覆盖不足；替换等于 fork Komga。
- PostgreSQL/MySQL：代码与迁移写死 SQLite，无配置入口。
- 系统 `libsqlite3.so` 的 JNI 包装：xerial 驱动没有“链接系统 sqlite”的开关，
  `org.sqlite.lib.path` 只加载 xerial 自己的 `libsqlitejdbc.so`。

### C. QEMU 用户态（仅兜底，不推荐）
**不能只把 x86_64/riscv64 的 `.so` 塞给原生 loong64 JVM**：JNI 库必须与 JVM 进程同架构，
`qemu-user` 无法只接管一次 `dlopen`。可行的是整个 x86_64 JVM + jar 跑在 `qemu-x86_64` 下
（Host A 已有 `/usr/bin/qemu-x86_64-static` 与 binfmt）。代价：x86 根文件系统、无硬件加速、
SQLite 扫描/缩略图明显变慢；只适合功能验证。

## 5. 最小验证（已在 16 KiB 页内核实测）
```java
import java.sql.*;
public class Smoke {
  public static void main(String[] a) throws Exception {
    System.out.println("os.arch=" + System.getProperty("os.arch"));
    try (Connection c = DriverManager.getConnection("jdbc:sqlite:/work/smoke.sqlite");
         Statement s = c.createStatement()) {
      s.execute("create table if not exists t(id integer primary key, name text)");
      s.execute("insert into t(name) values ('komga-loong64')");
      try (ResultSet r = s.executeQuery("select sqlite_version(), count(*) from t")) {
        r.next(); System.out.println("sqlite_version=" + r.getString(1) + " rows=" + r.getInt(2));
      }
      s.execute("create virtual table ft using fts5(x)");
      s.execute("insert into ft(x) values ('hello komga')");
      try (ResultSet r = s.executeQuery("select count(*) from ft where ft match 'komga'")) {
        r.next(); System.out.println("fts5_hits=" + r.getInt(1));
      }
    }
  }
}
```

```bash
mkdir -p native && cp .../libsqlitejdbc.so native/
java -Dorg.sqlite.lib.path=$PWD/native -Dorg.sqlite.lib.name=libsqlitejdbc.so \
     -cp sqlite-jdbc-3.53.4.0.jar Smoke.java
# os.arch=loongarch64 / sqlite_version=3.53.4 rows=1 / fts5_hits=1
```

不传 `org.sqlite.lib.path` 时同一程序报 `UnsatisfiedLinkError`，可作反证。
**Komga 端到端**：官方 jar + 上述 `.so` + openEuler JDK 21.0.11：
```bash
java -Dorg.sqlite.lib.path=/work/native -Dorg.sqlite.lib.name=libsqlitejdbc.so \
     -Dspring.profiles.include=docker --enable-native-access=ALL-UNNAMED \
     -jar /work/komga-1.29.1.jar --spring.config.additional-location=file:/config/
```
实测：`Database: jdbc:sqlite:/config/database.sqlite (SQLite 3.53)`；主库 94、tasks 2、
sessions 1 个迁移全部成功；`Started ApplicationKt in 13.172 seconds`；`GET /`=200，
`/actuator/health`=`{"status":"UP"}`；重启后 15.365 秒启动，无重复迁移、数据保留。
宿主 `getconf PAGESIZE`=**16384**，SQLite 默认 4096 B 页正常。

## 6. 让 Komga 使用自定义 .so

**方式一（推荐）：外挂，不改官方 jar。**

```bash
mkdir -p /opt/komga/native && cp libsqlitejdbc.so /opt/komga/native/
export JAVA_OPTS="-Dorg.sqlite.lib.path=/opt/komga/native -Dorg.sqlite.lib.name=libsqlitejdbc.so"
```
entrypoint 把 `$JAVA_OPTS` 传给 `java` 即可；保留官方 jar 的 sha256，升级只换 jar 与版本号。
**方式二：替换 jar 内嵌 sqlite-jdbc（已验证，但改动官方产物）。** 把
`org/sqlite/native/Linux/loongarch64/libsqlitejdbc.so` 打进
`BOOT-INF/lib/sqlite-jdbc-3.53.4.0.jar`，再替换 Komga fat jar 内同名嵌套 jar。
嵌套 jar 必须 **Stored（`zip -0`）** 写入；压缩写入会导致
`NoClassDefFoundError: org/sqlite/SQLiteConfig$JournalMode`（已踩）。发布建议方式一，
避免 digest 变化与供应链疑问。
## 7. 镜像构建建议
多阶段，构建阶段只编 `.so`，不引入 Node/Gradle：
```dockerfile
FROM openeuler/openeuler:24.03 AS jni
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source \
      --disablerepo=update-source --setopt=retries=1 --setopt=timeout=20 \
      --setopt=install_weak_deps=False gcc make perl zip unzip curl java-21-openjdk-devel
# 下载 sqlite-jdbc 3.53.4.0 源码与 sqlite-amalgamation-3530400.zip，按第 4 节 make

FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source \
      --disablerepo=update-source --setopt=retries=1 --setopt=timeout=20 \
      --setopt=install_weak_deps=False java-21-openjdk-headless curl tzdata util-linux && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1110 komga && useradd -u 1110 -g 1110 -M -d /config -s /bin/false komga
COPY --from=jni /sqlite-jdbc-3.53.4.0/src/main/resources/org/sqlite/native/Linux/loongarch64/libsqlitejdbc.so /opt/komga/native/
COPY komga-1.29.1.jar /opt/komga/komga.jar
COPY docker-entrypoint.sh /usr/local/bin/
ENV KOMGA_CONFIGDIR=/config \
    JAVA_OPTS="-Xms256m -Xmx1g -Dorg.sqlite.lib.path=/opt/komga/native -Dorg.sqlite.lib.name=libsqlitejdbc.so"
EXPOSE 25600
VOLUME ["/config", "/data"]
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
```
entrypoint：root 启动 → `mkdir -p /config /data && chown -R 1110:1110` →
`exec runuser -u komga -- java $JAVA_OPTS -jar /opt/komga/komga.jar --spring.config.additional-location=file:/config/`。
无需覆盖 `--enable-native-access`（清单已声明）。健康检查用
`curl -fsS http://127.0.0.1:25600/actuator/health | grep -q UP`，比 `/` 更真实。
若坚持 `USER komga`，文档须要求宿主卷 `chown 1110:1110`。镜像预计 400–550 MB。
## 8. 剩余风险与待办
1. **版本漂移**：升级时重查 `gradle/libs.versions.toml` 的 `sqliteJdbc` 与 `nightmonkeys`，
   SQLite 版本/amalgamation 编号随之变化；1.29.1 先固定。
2. **HEIF/JXL**：JDK 21 下 nightmonkeys 明确 `only supports Java 22, plugin will be disabled`；
   TwelveMonkeys 的 WebP 仍在支持列表（纯 Java），但 HEIC/JXL 封面不可用。恢复需 JDK 22+
   与 loong64 的 libheif/libjxl，属额外工程。
3. **Kobo**：`kepubify` 无 loong64 二进制，docker profile 告警但只影响 Kobo 转换；
   如需可参考仓库内 Go 应用从源码编。
4. **源码构建未端到端验证**：Gradle 9.8.1 能在 loong64 启动（已测 `gradle --version`），
   但 Vite 8/Rolldown 无 loong64 binding，jOOQ 生成还需给 Gradle JVM 注入
   `-Dorg.sqlite.lib.path`。建议继续“官方 jar + 外挂 .so”，源码构建只在 x86 做。
5. **16 KiB 页**：所有测试在 16384 B 页内核完成，SQLite 用 4096 B 库页，无异常；
   换目标机仍需 `getconf PAGESIZE` 复核。
6. **未测**：首次建管理员、建库、扫描 CBZ/PDF、阅读页、缩略图生成。启动/迁移/重启已过，
   下一步按 APP-DESIGNS 的测试项补 UI 流程。
## 9. 证据入口
- Komga：`gotson/komga@1.29.1` → `komga/build.gradle.kts`、`gradle/libs.versions.toml`、
  `komga/src/main/kotlin/org/gotson/komga/infrastructure/datasource/`、`komga/docs/openapi.json`
- sqlite-jdbc：`xerial/sqlite-jdbc@3.53.4.0` → `Makefile`、`Makefile.common`、
  `src/main/java/org/sqlite/{SQLiteJDBCLoader.java,util/OSInfo.java,core/NativeDB.c}`
- Host A 临时验证目录：`/tmp/komga-spike/`（源码、jar、`.so`、Smoke.java、Komga 日志）
- 仓库设计：[../APP-DESIGNS.md](../APP-DESIGNS.md) P3-01、[../IMAGE-BUILD.md](../IMAGE-BUILD.md)
