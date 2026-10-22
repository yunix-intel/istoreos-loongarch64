# 故障排查与启动注意

本页按“现象 → 原因 → 修复”记录本项目实际踩过的坑。构建日志的完整时间线见
[BUILDLOG.md](BUILDLOG.md)。

## 前端 / Node

### `Cannot find module './rolldown-binding.linux-loong64-gnu.node'`

- 原因：Vite 8 / Rolldown 没有 loong64 native binding。
- 修复：在 x86_64 WSL2 / x86 构建机用 Node 22 编前端，把架构无关的 `dist` 拷到龙芯：

```bash
export PATH=$HOME/node22/bin:$PATH
npm ci && npm run build
```

### `react-app-rewired: not found`（Prometheus UI）

- 原因：`web/ui/react-app` 是独立 pnpm 工作区，根 `pnpm install` 不会装它。
- 修复：`cd web/ui/react-app && pnpm install`，再回 `web/ui` 执行 `pnpm run build`。

## Go / CGO / glibc

### `Binary was compiled with 'CGO_ENABLED=0', go-sqlite3 requires cgo to work. This is a stub`

- 原因：ntfy/gotify/podman 等依赖 mattn/go-sqlite3，必须 CGO。
- 修复：`CGO_ENABLED=1` 编；并且要在**目标镜像的 glibc 版本**里编：

```bash
docker run --rm -v "$PWD":/src -w /src openeuler/openeuler:24.03 bash -c '
  dnf install -y gcc make
  CGO_ENABLED=1 GOOS=linux GOARCH=loong64 go build -o app .
'
```

### `GLIBC_2.39 not found`（geckodriver 在 openEuler 2.38 镜像里）

- 原因：在 Loongnix 宿主（glibc 2.41）编的 Rust 二进制引用了 2.39 符号。
- 修复：在目标基础镜像内装 Rust 并重编；geckodriver 用 openEuler 容器 + rustup 1.99。
  脚本见 `scripts/build-geckodriver.sh`。

### `numpy.core.multiarray failed to import`（cv2）

- 原因：openEuler 的 cv2 4.5.2 是 numpy 1.x ABI，numpy 2.x 不兼容。
- 修复：venv 里锁 `numpy==1.26.4`，并把系统 `cv2` 复制进 venv；见
  [OPENCV-SSIM.md](OPENCV-SSIM.md)。

## Python / 应用依赖

### pikepdf 编译报 `qpdf/Constants.h: No such file` 或 qpdf API 私有成员

- 原因：openEuler 24.03 只有 qpdf 11.1；pikepdf 10.17 需要 qpdf 12。
- 修复：多阶段源码编 qpdf 12.4.2 到 `/usr/local/lib`，`ldconfig` 后再 pip。
  Paperless 的 Dockerfile 是完整示例。

### jq 编译报 `config.sub loongarch64-unknown-linux-gnu failed`

- 原因：jq 1.13 内置 oniguruma 的旧 autotools 脚本不认识 loongarch64。
- 修复：用 automake 1.16 的 `config.guess/config.sub` 替换嵌套 tarball，并加
  `--build=loongarch64-unknown-linux-gnu`；脚本见 `scripts/build-jq-wheel.sh`。

### tesseract 找不到 `eng` / `hocr` / `osd`

- 原因：openEuler 语言包装在 `/usr/share/tesseract/tessdata`，tesseract 5.3 默认找
  `/usr/share/tessdata`；`hocr` 配置在默认目录。
- 修复：把 `eng/chi_sim/osd.traineddata` 逐个链接到 `/usr/share/tessdata`，
  补 `tesseract-osd` 包，设 `TESSDATA_PREFIX=/usr/share/tessdata`。
- 不要整目录替换 `/usr/share/tessdata`，否则 `configs/hocr` 丢失。

### Redis 启动后立刻退出：`Failed to configure LOCALE for invalid locale name`

- 原因：镜像里 `LANG=en_US.UTF-8` 但 locale 未生成。
- 修复：用 `C.UTF-8` 启动 Redis/镜像；`LC_ALL=C.UTF-8 LANG=C.UTF-8 redis-server ...`。

### Paperless 消费目录不处理

- 原因：自定义 entrypoint 只起了 daphne + celery worker，没有 `document_consumer` 和 beat。
- 修复：entrypoint 增加 `python manage.py document_consumer &` 与 `celery -A paperless beat &`。

## 浏览器 / Selenium

### changedetection 的 `html_webdriver` 没有截图 / 浏览器步骤

- 原因：原 fetcher 只实现 Chrome 远程；且上游在有 browser_steps 时强制切 Playwright。
- 修复：镜像内置 Firefox + geckodriver；fetcher 声明 `supports_browser_steps=True`；
  修改 `resolve_content_fetcher()`，已支持步骤时不再切 Playwright。
- 运行加 `--shm-size=1g`；Firefox 在 64MB `/dev/shm` 下容易崩。
- 实时 Browser Steps 预览 UI 仍依赖 Playwright live page；保存后的步骤执行走 Selenium。

### 远程 Chrome / Edge

- Edge 只有 x86_64/ARM64，无 loong64；不要尝试。
- 需要 Chrome 时设 `WEBDRIVER_BROWSER=chrome` + `WEBDRIVER_URL=http://<x86-host>:4444/wd/hub`。

## Prometheus / 监控

### 健康检查正常但 UI 500、`/static/...` 404

- 原因：`web/ui/embed.go` 带 `//go:build builtinassets`，未加 tag 编出的是无 UI 版本。
- 修复：先跑 `scripts/compress_assets.sh`，再
  `go build -tags builtinassets ./cmd/prometheus`。

### Node Exporter 只有容器指标

- 原因：默认读容器命名空间的 `/proc`、`/sys`。
- 修复：挂宿主 `/proc:/host/proc:ro`、`/sys:/host/sys:ro`、`/:/rootfs:ro`，
  并加 `--path.procfs=/host/proc --path.sysfs=/host/sys --path.rootfs=/rootfs`。

## Pi-hole FTL

### dnf 卡在 `404 metalink ... EPOL/main` / `debuginfo`

- 原因：openEuler 24.03 的 EPOL/debuginfo metalink 在部分镜像返回 404，dnf 会长时间重试。
- 修复：构建时加
  `--disablerepo=debuginfo --disablerepo=EPOL --setopt=retries=1 --setopt=timeout=15`。

### `RESOURCE_COMPILER-NOTFOUND` / `docs.h: 'index_html' undeclared`

- 原因：FTL 用 `xxd` 把 web/spec 资源转成 C 数组；openEuler 的 `xxd` 在 `vim-common` 包里。
- 修复：安装 `vim-common`，确认 `xxd` 在 PATH，清空 `build/` 重新 configure。

### `nettle/balloon.h: No such file or directory`

- 原因：openEuler 只有 nettle 3.8.1，FTL v6.8 需要 3.9+ 的 balloon API。
- 修复：源码编 nettle 3.10.x 到 `/usr/local`，FTL configure 加
  `-DCMAKE_PREFIX_PATH=/usr/local -DCMAKE_C_FLAGS=-I/usr/local/include`，
  链接加 `-L/usr/local/lib64 -Wl,-rpath,/usr/local/lib64`；运行时镜像复制
  `libnettle.so*`/`libhogweed.so*` 并 `ldconfig`。

### `-Werror` 把 dnsmasq/生成的 docs 警告变成错误

- 修复：龙芯构建把 `src/CMakeLists.txt` 的 `-Werror` 改为 `-Wno-error`；
  这是编译策略补丁，不改变运行逻辑。

## 容器 / 固件

### podman 静态版启动报 `go-sqlite3 requires cgo`

- 原因：podman 5.5+ 删了 boltdb，SQLite 是唯一后端且需 CGO。
- 修复：CGO 重编 podman 5.8.8（musl-gcc，SQLite 静态编入）；不要用静态版。
- 嵌套运行：`--cgroups=disabled --security-opt seccomp=unconfined --runtime crun`。

### podman bridge 网络不可用

- 原因：宿主内核缺 `nft_conntrack`（Loongnix 6.6.52 默认没有）。
- 修复：用 `--network=host` / `none`；或在宿主内核补 nft conntrack 模块后重测。

### OpenWrt ABI 检查拒绝 musl 二进制

- 原因：静态 musl 文件直接放 `package/files` 会触发 `libc.musl-*` 依赖。
- 修复：打成 tar.gz，首启脚本解压到目标目录。

### CasaOS 挂载/格式化报 `exit 127 do_mount: 未找到命令`

- 原因：P3 安装包漏了 `share/shell/local-storage-helper.sh`。
- 修复：从上游
  `build/sysroot/usr/share/casaos/shell/local-storage-helper.sh` 补入并重打 tarball
  （sha256 `6efcbb60…7bea`）。

### CasaOS 只列出部分磁盘

- 原因：`lsblk` 默认排除 RAM 盘；`IsDiskSupported` 只接受
  `sata/nvme/sas/spi/virtio/mmc`，loop/dm/nbd 被过滤。
- 修复：用真实 SATA/USB 盘验证；NBD 只能通过 `POST /v1/storage` 直接挂载。

### CasaOS 格式化后数据库多一条旧 UUID

- 原因：`DeleteMountPointFromDB` 按 UUID + mount_point 过滤，旧 UUID 记录不会删。
- 修复：上游建议按 mount_point 删除或 upsert；当前重启仍可挂载，但记录会累积。

### Alertmanager 日志 `gossip not settled`

- 原因：默认启用 9094 gossip 集群，单节点启动时要等收敛轮询。
- 修复：属正常现象，十余秒后恢复；单机不需要 HA 时加
  `--cluster.listen-address=` 关闭 9094。

### Alertmanager 数据卷写入失败

- 原因：容器以 `65534:65534`（nobody）运行，宿主挂载目录属主是 root。
- 修复：`chown -R 65534:65534 /srv/alertmanager/data`，或改用命名卷。

### PostgreSQL 首启报 `directory is not empty`

- 原因：挂载目录里有 `lost+found` 之外的文件，`initdb` 拒绝初始化。
- 修复：换空目录，或挂载 ext4 分区的子目录；已有数据目录不要清空。

### PostgreSQL 重启慢或权限报错

- 原因：entrypoint 只对顶层目录做非递归 chown，卷内文件属主不对时 postgres 无法读取。
- 修复：一次性 `chown -R 26:26 /path/to/pgdata`，之后正常重启不会再遍历全部文件。

### Redis 日志 `Memory overcommit must be enabled`

- 原因：宿主 `vm.overcommit_memory` 不是 1，低内存时后台保存可能失败。
- 修复：宿主执行 `sysctl -w vm.overcommit_memory=1` 并写入 `/etc/sysctl.d/`；
  家用低负载可忽略。

### Node 应用报 `Cannot find module '/usr/local/lib/cli'`

- 原因：npm 全局 bin 是符号链接，Docker `COPY` 会解引用，`fs.realpathSync` 解析到错误目录。
- 修复：运行阶段重新创建指向 `/opt/node24/lib/node_modules/...` 的符号链接；Homebridge 2 的入口是 `bin/homebridge.js`。

### Homebridge UI 5 的 8581 不监听

- 原因：Config UI 5 不再由插件自身启动，必须由 `hb-service` supervisor 运行。
- 修复：默认命令改为 `hb-service run -U /homebridge --docker`，不要只运行 `homebridge`。

### Homebridge UI 安装 node-pty 失败

- 原因：`@homebridge/node-pty-prebuilt-multiarch` 没有 loong64 预编译，npm 包又不含 `src/unix`。
- 修复：从 GitHub v0.14.1 源码 `node-gyp rebuild`，把 `build/Release/pty.node` 放回包内；不要试图在 npm 包目录里直接编译。

### Actual Budget 启动报缺少 better_sqlite3.node

- 原因：`better-sqlite3` 没有 install script，npm 包只带 x64/arm 预编译。
- 修复：构建阶段进入包目录执行 `npx node-gyp rebuild`，再复制 `build/Release/better_sqlite3.node`。

### Actual Budget 反代后登录/cookie 异常

- 原因：未正确传递可信代理头或 host。
- 修复：设置 `ACTUAL_TRUSTED_PROXIES`、`ACTUAL_HOSTNAME`，并确保反向代理传递 `X-Forwarded-*`。

### MinIO 启动立即退出

- 原因：没有设置 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`。
- 修复：两者都提供；密码不要使用示例值，且不要在公网明文暴露。

### MinIO 日志出现 host failure 警告

- 原因：单目录/单盘模式没有纠删码冗余，属于预期警告。
- 修复：生产使用多盘或分布式部署，并做独立备份；不要把它当成高可用存储。

### Homebox 构建报 workbox-window 无法解析

- 原因：pnpm 严格 node_modules 布局下 PWA 依赖没有提升到顶层。
- 修复：前端安装必须加 `--shamefully-hoist`，并使用与 lockfile v6 匹配的 pnpm 8。

### Homebox 构建报 `undefined: sqlite3_index_constraint`

- 原因：v0.10.3 自带 `modernc.org/sqlite v1.27` 没有 loong64 生成文件。
- 修复：构建前 `go get modernc.org/sqlite@v1.61.0`，再 `CGO_ENABLED=0` 编译。

### NocoDB 启动报 `Meta database configuration missing SQLite file name`

- 原因：`NC_DB` 的 SQLite 文件名没有放在查询参数里。
- 修复：使用 `NC_DB=sqlite3://?d=/data/noco.db`；不要用 `sqlite3:///data/noco.db`。

### NocoDB npm 安装报 `only-allow pnpm`

- 原因：包内 preinstall 脚本强制 pnpm。
- 修复：`npm install -g --ignore-scripts nocodb@...`，再手动进入 `node_modules/sqlite3` 执行 `node-gyp rebuild`。

### Apprise nginx 报缺 `server-override.conf`

- 原因：openEuler 的 nginx 包不会预建上游 Debian 镜像里的 override 文件。
- 修复：构建时 `touch /etc/nginx/server-override.conf /etc/nginx/location-override.conf`。

### Apprise nginx 报 error.log 权限拒绝

- 原因：supervisor 把 nginx 降权到 apprise 用户，`/var/log/nginx` 不可写。
- 修复：构建时创建 `/var/log/nginx` 并设为 0777，或改 error_log 到 stdout。

### Apprise `pycares` 构建报 CMake 缺失

- 原因：pycares 需要 CMake 编译。
- 修复：构建阶段安装 `cmake`，并加系统 cryptography/gevent 的 constraints 避免重编。

### Mealie 构建 Pillow 时报 libheif 头文件缺失

- 原因：`pillow-heif` 需要 `libheif`，openEuler 24.03（含 EPOL）没有 `libheif-devel`。
- 修复：当前 loong64 使用 `pillow_heif` stub 禁用 HEIF/HEIC；JPEG/PNG/WebP 正常。需要 HEIF 时必须先移植 libheif。

### Mealie 构建 numpy 时报 `autoreconf: command not found`

- 原因：numpy 构建后端依赖 patchelf，patchelf 又需要 autotools。
- 修复：构建阶段安装 `autoconf automake libtool patch`。

### Mealie 启动报 `PRODUCTION Field required`

- 原因：Mealie 的 pydantic 设置在运行时不带默认 `PRODUCTION`。
- 修复：设置 `PRODUCTION=true`（本镜像已内置）。

## 2026-10 新镜像的坑

### ChineseSubFinder：`#error Please add support for your architecture`

- 原因：`go-webrtcvad` 的 `arch.h` 没有 LoongArch 分支。
- 修复：在 `arch.h` 增加：

```c
#elif defined(__loongarch__) || defined(__loongarch64__)
#define WEBRTC_ARCH_64_BITS
#define WEBRTC_ARCH_LITTLE_ENDIAN
```

- 运行期若报 `mkdir Logs: permission denied`，把 `WORKDIR` 设为 `/config`，
  entrypoint `cd /config` 后再降权。

### LANraragi：`Can't locate LANraragi/Utils/Config.pm`

- 原因：CPAN 模块在 `local::lib` 下，Perl 默认不搜索。
- 修复：`PERL5LIB` 同时包含通用与架构目录：

```text
/home/koyomi/perl5/lib/perl5:/home/koyomi/perl5/lib/perl5/loongarch64-linux-thread-multi
```

- `install.pl` 的 libarchive 检查会报 `Unsupported compile language "C"`；
  该检查不影响链接，可直接跳过（第 137–138 行）。
- 镜像必须含 `perl-local-lib`，否则运行时缺 `local/lib.pm`。

### OwnTone：`mDNS init failed`

- 原因：即使关闭 mDNS 公告，OwnTone 初始化仍要求 D-Bus/Avahi。
- 修复：镜像内安装 `dbus avahi avahi-tools`，entrypoint 先启动
  `dbus-daemon --system --fork` 与 `avahi-daemon --daemonize --no-chroot`。
- 日志文件需在降权前 `touch` 并 `chown`。

### WebVirtCloud：`bcrypt` 无 loong64 wheel

- 原因：pip 回退源码编译，需要 Rust。
- 修复：构建容器安装 `rust cargo`；或预装系统 `python3-bcrypt`。
- `cryptography/cffi` 源码编译失败时，先装系统
  `python3-cryptography python3-cffi libffi-devel`。
- `numpy` 被 websockify 拉起会触发 CMake 源码构建，装系统 `python3-numpy` 跳过。
- openEuler 的 GID 33 已被 `tape` 占用，创建 `www-data` 用
  `groupadd -o -g 33 www-data`。

### Penpot：官方 JRE 26 无法在 loong64 运行

- 原因：官方 backend 镜像自带 x86 JRE 26；龙芯只有 OpenJDK 21。
- 修复：只取官方 `penpot.jar`，确认 class major version 为 65（Java 21），
  在 openEuler 上装 `java-21-openjdk-headless` 运行。
- 不要直接用官方 `run.sh`：它包含 JDK 24+ 才认识的
  `--sun-misc-unsafe-memory-access`，在 Java 21 会启动失败。
- 前端 nginx 必须用变量 `proxy_pass` + Docker DNS `127.0.0.11`，
  否则 backend 未启动时 nginx 直接退出。

### Hermes：pip 解析 `browser-harness` 与 `Pillow` 冲突

- 原因：Hermes 直接依赖 `Pillow==13.0.0`，`browser-harness` 又精确要求
  `pillow==12.3.0`；pip 没有 uv 的 override 机制，报 `ResolutionImpossible`。
- 修复：`browser-harness` 用 `--no-deps` 预装，再从
  `importlib.metadata.requires("hermes-agent")` 生成顶层依赖列表，
  跳过 `browser-harness`/`cryptography`/`pynacl`/`pillow-heif` 后安装。
- `pillow-heif` 需要 `libheif-devel`，openEuler 无此包；Hermes 对它是软依赖，
  跳过即可（HEIC/HEIF 图片不可用，JPEG/PNG/WebP 正常）。
- Hermes 的 wheel 构建有保护：必须 `HERMES_NIX_BUILD=1 pip install --no-deps`
  才能生成 wheel，否则报 “Building wheels or sdists for hermes-agent is not supported”。

## Docker Hub

### `denied: requested access to the resource is denied`

- 原因：构建机没有登录，或 Docker Desktop 的 `credsStore` 凭据没有迁到 Linux。
- 修复：`docker login`，或从 `docker-credential-desktop get` 导出后写入
  `/root/.docker/config.json`（0600）；不要打印 token。

## 启动前检查清单

```bash
docker inspect <image> --format '{{.Architecture}} {{.Os}}'
docker run --rm <image> <version-or-help>
docker logs -f <container>     # 先看日志，不只看 docker ps
curl -fsS http://127.0.0.1:<port>/<health>
```
