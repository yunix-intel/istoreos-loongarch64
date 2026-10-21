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
