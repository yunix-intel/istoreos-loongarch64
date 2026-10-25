# CasaOS P3 三个发布 BLOCKER 修复与复验

日期：2026-10-25
环境：Host A（SSH `loongson-lab`，`yunix-pc`，LoongArch64/3A6000，Loongnix 25）；
前缀 `/opt/casaos-p3`，gateway `:8081`；真实盘 `/dev/sda1` ext4 → `/mnt/Data`。
约束：未格式化真实盘、未重启 A 机；临时改测试用户密码前均备份 `user.db`，测后恢复原 hash。

源码/构建目录：`/build/casaos-fix/`
补丁：`docs/research/casaos-patches/*.patch`
修复包：`/build/archive/casaos-p3/casaos-p3-loong64-0.1.2-appmgr410.tar.gz`
（sha256 `688fed00656f9ff8a25299989d4ddf28bb6e35b2b10a1964f7acce6efeaa9b14`；
旧 `0.1.1-blockerfix` 已被本包取代）

## 0. 结论

| # | BLOCKER | 状态 | 关键证据 |
|---|---|---|---|
| 1 | 设备白名单未下沉 | **PASS** | `/dev/loop0`、`/dev/dm-0`、`/dev/mapper/test`、`/dev/nbd0` 的 POST/PUT 均 403；`blkid` 无 ext4；`findmnt` 无 `/tmp/loopverify`；真实盘 UUID 未变 |
| 2 | 首管理员 LAN 抢先 | **PASS** | 空库隔离实例 LAN status/register 403；loopback status 200 并注册成功；初始化后 LAN status 200、register 4xx |
| 3 | 运行时 socket/前缀路径 | **PASS** | app-management（v0.4.10-alpha2）二进制/source 无 `/tmp/message-bus.sock`；安装 9/9、卸载 6/6 事件 HTTP 200；新日志 0 次发布失败；危险脚本已移出前缀与包 |
| — | 6 服务健康 | **PASS** | `healthcheck.sh` 200；soak 15/15 六进程存活（local-storage 401 为需 JWT 的预期） |
| — | soak（最终 v0.4.10-alpha2 10min + 切换前 v0.4.5 15min） | **PASS**（详见 §7） | 六服务全部存活；HTTP 200/401；PID 稳定；RSS 无泄漏趋势 |
| — | 24h 稳定性 | **BLOCKED** | 未连续运行 24h，**需后续** |

**C-04 判定：三个 BLOCKER 已关闭，可以重开 C-04 复核；最终发布仍需补 24h soak/重启自启。**

### 0.1 对协调者反馈的说明（socket-first）

协调者指出 `PublishEventWrapper` 仍先调 `external.PublishEventInSocket`。
该问题存在于**旧二进制**：`go version -m` 显示旧 app-management 的模块元数据为
`v0.4.10-alpha2+dirty`，其 `PublishEventWrapper` 先走 unix socket、失败后才走 HTTP。

**最终版本**：按要求恢复为 **AppManagement v0.4.10-alpha2**
（tag `v0.4.10-alpha2`，commit `cc80b3313113d946f7216ff4b95c3c4b83381149`），
并直接修改其 `service/service.go`：删除 `external.PublishEventInSocket` 首调，
`PublishEventWrapper` 只调用
`MyService.MessageBus().PublishEventWithResponse`，使用 `run/message-bus.url`
解析出的 `http://127.0.0.1:40157`。

说明：v0.4.10-alpha2 的 `-v` 仍硬编码打印 `v0.4.5`（上游常量），版本以 tag/commit
和构建元数据为准。v0.4.5 曾作为中间修复版本验证通过，但**已被 v0.4.10-alpha2 取代**；
`casaos-appmanagement-v0.4.5-blockers.patch` 作废，仅保留作历史对照。

复核证据：

```bash
grep -rn "PublishEventInSocket\|message-bus.sock\|http://unix" \
  /build/casaos-fix/CasaOS-AppManagement-v0410 --include="*.go"
# -> none
strings /opt/casaos-p3/bin/casaos-app-management | grep -c "/tmp/message-bus.sock"
# -> 0
strings /opt/casaos-p3/bin/casaos-app-management | grep -c "PublishEventInSocket"
# -> 0
awk '/2026-10-25T20:5[4-9]/' /opt/casaos-p3/log/app-management.stdout.log | grep -c "message-bus.sock"
# -> 0
awk '/2026-10-25T20:5[4-9]/' /opt/casaos-p3/log/app-management.stdout.log | grep -c "failed to publish event"
# -> 0
```

最终二进制 sha256：`6ed86c879d11b9ea30e46f63ff536119446d9a9c4279a520c4272a6f62406c78`。
中间 v0.4.5 二进制（已备份）：`899d540ae0b7ae5d70e7a5e0f7f6cfc9e9706701c5486d6852ee348646d5f879`。

## 1. 根因

### 1.1 设备白名单未下沉（LocalStorage v0.4.4）

- `route/v1/storage.go` 的 `PostAddStorage` 在 `format=true` 时先执行
  `UmountPointAndRemoveDir → DeletePartition → AddPartition`，之后才用
  `IsDiskSupported` 决定“是否把整盘当子项”，从不拒绝请求。
- `PutFormatStorage` 只把 body 解成 `map[string]string`，完全不读 `format`，
  无条件 `FormatDisk(path)`；密码二次确认整段被注释。
- `share/shell/local-storage-helper.sh` 的 `FormatDisk/AddPartition/do_mount`
  也没有任何传输层校验。
- `IsDiskSupported` 本身只接受 `sata/nvme/spi/sas/virtio/mmc/ata`，loop/nbd/dm 返回 false。

### 1.2 首管理员可被局域网抢先（UserService v0.4.8）

- `GET /v1/users/status` 未初始化时对任何来源生成并返回注册 key；
- `POST /v1/users/register` 只校验 key，不校验来源 IP；
- 首次启动窗口内 LAN 任意主机可注册 admin（等价宿主 root + docker.sock）。

### 1.3 运行时 socket/前缀路径（AppManagement）

- 旧二进制（v0.4.10-alpha2+dirty）的 `PublishEventWrapper` 先调用
  `external.PublishEventInSocket`，固定 dial `/tmp/message-bus.sock`；
  该文件不存在，每次安装/卸载产生事件发布失败日志（旧证据 15 次）。
- 同时 AppManagement 上游把 `/etc/casaos/env`、`/var/lib/casaos/docker_root`
  写死；本次一并改为前缀内路径。v0.4.10-alpha2 本身已写
  `run/app-management.url`（中间版本 v0.4.5 缺失，已回退，不再是最终版本）。
- 随包 `delete-old-service.sh` 写 `/etc`、`/usr`、`/var/lib/casaos`，
  `helper.sh` 含 `systemctl stop docker`、`cp -r /var/lib/docker/*`，
  `update.sh` 直接 `curl | bash`；三者均未被 unit 引用。

## 2. 改动文件

### 2.1 LocalStorage v0.4.4（`casaos-localstorage-v0.4.4-blockers.patch`）

| 文件 | 改动 |
|---|---|
| `route/v1/storage.go` | 新增 `allowedStoragePaths()`/`isStoragePathAllowed()`：从服务端 `LSBLK(false)` 派生“白名单磁盘 + 其 `Type=part` 分区”的精确路径集合（嵌套 dm/lvm/crypt 不纳入），并对 `/dev/loop`、`/dev/nbd`、`/dev/dm-`、`/dev/mapper/` 前缀显式拒绝；`PostAddStorage` 在任何 `DeletePartition/AddPartition` 之前拒绝非白名单；`PutFormatStorage` 在 `UmountPointAndRemoveDir/FormatDisk` 之前拒绝；严格解析 `format`（bool 或 `"true"/"false"`，其他类型 400）；显式 `format=false` 只挂载不格式化；`format=true` 需密码二次确认（JWT claims 的 username + UserService `/v1/users/login` 校验，失败 fail-closed）；`FormatDisk` 失败立即返回；UUID 变化等待加 30s 上限 |
| `build/sysroot/usr/share/casaos/shell/local-storage-helper.sh` | 新增 `IsDiskAllowed()`/`RequireSupportedDisk()`，镜像 Go 侧白名单（sata/nvme/spi/sas/ata/virtio/Hyper-V/mmc；分区查 PKNAME 父盘）；`FormatDisk`、`AddPartition`、`do_mount` 入口全部校验 |
| `service/usb.go` | gopsutil v3 → v4 import |
| `go.mod` / `go.sum` | `gopsutil/v4 v4.26.9`、`modernc.org/sqlite v1.30.0`、`modernc.org/libc v1.50.9` |

白名单设计说明：不是只查 `IsDiskSupported(path)`，而是构造**服务端实际枚举出的**
允许路径集合。这样 `/dev/loop0`（LSBLK 直接跳过 loop）、`/dev/nbd0`、`/dev/dm-*`、
`/dev/mapper/*`、任意不存在的路径、符号链接路径都会在写操作前被拒绝。
分区（如 `/dev/sda1`）通过父盘的 `Children` 进入集合，因此真实盘分区仍可用。

密码二次确认说明：CasaOS JWT 的 claims 只有 `Username/ID`，没有密码哈希，无法像
上游注释那样比较 `claims.Password`。实现改为：解析已登录 JWT 得到用户名，再调用
UserService 的 `/v1/users/login` 校验请求体中的 `password`；UserService 不可达或
校验失败一律 401，不执行任何磁盘操作。`format` 省略时保持历史行为（格式化）但同样
需要密码；显式 `format=false` 不需要密码。

### 2.2 UserService v0.4.8（`casaos-userservice-v0.4.8-blockers.patch`）

| 文件 | 改动 |
|---|---|
| `route/v1/user.go` | 新增 `isLoopbackHost`/`requestIsLoopback`：先查 `RemoteAddr` 必须 loopback，再查 `X-Forwarded-For`/`X-Real-IP` 首个地址也必须 loopback（防 gateway 代理把 LAN 请求伪装成 127.0.0.1）；`GET /v1/users/status` 与 `POST /v1/users/register` 仅在**未初始化**时强制 loopback，LAN 返回 403；初始化后行为不变 |
| `go.mod` / `go.sum` | `modernc.org/sqlite v1.30.0`、`modernc.org/libc v1.50.9` |

### 2.3 AppManagement v0.4.10-alpha2（`casaos-appmanagement-v0.4.10-alpha2-blockers.patch`）

最终版本：tag `v0.4.10-alpha2`，commit `cc80b3313113d946f7216ff4b95c3c4b83381149`。

| 文件 | 改动 |
|---|---|
| `service/service.go` | 删除 `external.PublishEventInSocket` 首调及其 `else` 分支；`PublishEventWrapper` 直接调用 `MyService.MessageBus().PublishEventWithResponse`（URL 来自 `run/message-bus.url`），socket 路径彻底移除 |
| `pkg/config/init.go` | 全局 env 文件从写死 `/etc/casaos/env` 改为 `ConfigFilePath` 同目录的 `env`（前缀内 `/opt/casaos-p3/conf/env`） |
| `route/v1/docker.go` | docker-root 标记文件从 `/var/lib/casaos/docker_root` 改为 `$PREFIX/apps/docker_root` |
| `main.go` | 无需改动：v0.4.10-alpha2 上游已写 `run/app-management.url = http://127.0.0.1:<port>`，本次验证该文件随监听端口更新 |

v0.4.5 中间版本补丁 `casaos-appmanagement-v0.4.5-blockers.patch` **作废**，仅保留作
历史对照；最终安装包与验收均使用 v0.4.10-alpha2。

随包脚本处理：

- 从 `/opt/casaos-p3/share/shell/` 移除 `delete-old-service.sh`、`helper.sh`、`update.sh`，
  备份到 `/opt/casaos-p3/.removed-20261025-192413/`（不随包、不被 unit 引用）。
- 同步从 `/build/archive/casaos-p3/authored/share/shell/` 和 stage 移除；
  新包 `casaos-p3-loong64-0.1.2-appmgr410.tar.gz` 中已无这三个脚本。
- 保留 `local-storage-helper.sh`（已加白名单）、`usb-mount.sh`/`usb-mount@.service`
  （USB 自动挂载，本次策略仍不纳入 local-storage 管理）。

## 3. 构建

Go：`/home/yunix/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.27.2.linux-loong64/bin/go`（go1.27.2）
环境：`GOTOOLCHAIN=local CGO_ENABLED=0 GOOS=linux GOARCH=loong64`

源码 tag/commit：

| 组件 | tag | commit |
|---|---|---|
| LocalStorage | v0.4.4 | `c78fcce41c1cbb1ec37fa14d71d39521ba3db3ca` |
| UserService | v0.4.8 | `5cf4ed5424be4c62b97d67b51f6338c47285f47b` |
| AppManagement | v0.4.10-alpha2 | `cc80b3313113d946f7216ff4b95c3c4b83381149` |

oapi codegen（生成的 `codegen/` 不在 git 中，必须先生成；MessageBus spec 固定到运行中的
v0.4.4-3-alpha2，避免 main 分支漂移）：

```bash
GEN="go run github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.12.4"
MB=https://raw.githubusercontent.com/IceWhaleTech/CasaOS-MessageBus/v0.4.4-3-alpha2/api/message_bus/openapi.yaml

# LocalStorage
$GEN -generate types,server,spec -package codegen api/local_storage/openapi.yaml > codegen/local_storage_api.go
$GEN -generate types,client -package message_bus "$MB" > codegen/message_bus/api.go

# UserService
$GEN -generate types,server,spec -package codegen api/user-service/openapi.yaml > codegen/user_service/user_service_api.go
$GEN -generate types,client -package message_bus "$MB" > codegen/message_bus/api.go

# AppManagement
$GEN -generate types,server,spec -package codegen api/app_management/openapi.yaml > codegen/app_management_api.go
$GEN -generate types,client -package message_bus "$MB" > codegen/message_bus/api.go
```

依赖与编译：

```bash
cd /build/casaos-fix/CasaOS-LocalStorage
go get github.com/shirou/gopsutil/v4@v4.26.9 modernc.org/sqlite@v1.30.0
go mod tidy
go build -trimpath -buildvcs=false -ldflags="-s -w" -o /build/casaos-fix/out/casaos-local-storage .

cd /build/casaos-fix/CasaOS-UserService
go get modernc.org/sqlite@v1.30.0
go mod tidy
go build -trimpath -buildvcs=false -ldflags="-s -w" -o /build/casaos-fix/out/casaos-user-service .

cd /build/casaos-fix/CasaOS-AppManagement-v0410
go mod tidy
go build -trimpath -buildvcs=false -ldflags="-s -w" -o /build/casaos-fix/out/casaos-app-management-v0410 .
# 安装时重命名为 /opt/casaos-p3/bin/casaos-app-management
```

产物均为 `ELF 64-bit LSB executable, LoongArch, statically linked, stripped`；
`-v` 分别为 `v0.4.4` / `v0.4.8` / `v0.4.5`（AppManagement 的 `0.4.5` 是上游硬编码常量，
实际源码为 tag `v0.4.10-alpha2`，以 commit `cc80b33…` 为准）。

构建中遇到 `/home` 满（150G，100%）：清理了可再生 `~/.cache/go-build`，并把 `GOCACHE`
指向 `/build/casaos-fix/.gocache`；未删除模块缓存/源码。

## 4. 替换与重启

```bash
# 第一轮（19:24）：LocalStorage / UserService / AppManagement
TS=20261025-192413
mkdir -p /opt/casaos-p3/bin/.bak-$TS
cp -a /opt/casaos-p3/bin/{casaos-local-storage,casaos-user-service,casaos-app-management} /opt/casaos-p3/bin/.bak-$TS/
install -m 0755 /build/casaos-fix/out/casaos-local-storage /opt/casaos-p3/bin/
install -m 0755 /build/casaos-fix/out/casaos-user-service /opt/casaos-p3/bin/
install -m 0755 .../local-storage-helper.sh /opt/casaos-p3/share/shell/

# 第二轮（20:52）：AppManagement 回到 v0.4.10-alpha2（仅备份/替换 app-management）
TS2=20261025-205258
mkdir -p /opt/casaos-p3/bin/.bak-$TS2-v045
cp -a /opt/casaos-p3/bin/casaos-app-management /opt/casaos-p3/bin/.bak-$TS2-v045/
install -m 0755 /build/casaos-fix/out/casaos-app-management-v0410 /opt/casaos-p3/bin/casaos-app-management

# 只停/起 app-management + casaos；gateway/message-bus/user-service/local-storage/Docker 未重启
CASAOS_CONFIG_PATH=/opt/casaos-p3/conf /opt/casaos-p3/scripts/start.sh
```

备份与最终哈希：

| 文件 | 旧 sha256 | 新 sha256 |
|---|---|---|
| casaos-local-storage | `6af97e290c2d9bc87085cfbd3f1e7ce4bd3f2443990882ab6ca6314a34e6cfe7`（`.bak-20261025-192413`） | `c11c596d246c1bc1eb8e984ad29194d85a955696aae53cbbe64eba4595b38008` |
| casaos-user-service | `72b70ee483b34b05faff0cbfa158e4f05b4d1d9cf792f4d9d0ef1a85800d3dbb`（`.bak-20261025-192413`） | `cafebdac273df450ab780b7671bf154dcefee0bc26e556318ca221323db77572` |
| casaos-app-management | 原始 `5c6d5653…`（`.bak-20261025-192413`）；中间 v0.4.5 `899d540a…`（`.bak-20261025-205258-v045`） | **v0.4.10-alpha2 `6ed86c879d11b9ea30e46f63ff536119446d9a9c4279a520c4272a6f62406c78`** |

运行中进程校验（`sha256sum /proc/<pid>/exe`）与上表新哈希一致：
local-storage `c11c596…`、user-service `cafebdac…`、
**app-management `6ed86c87…`（pid 435412）**。

产物锚定：

| 产物 | sha256 |
|---|---|
| `share/shell/local-storage-helper.sh`（已部署） | `63ba8b55082d16e54c53d94f76ea543a7027a940736beee1022138fea058b0fc` |
| `casaos-localstorage-v0.4.4-blockers.patch` | `1e5083ef65931e88fa1e6dc3becc88b5e899b91ee639fa2db45edc7c18e51cb0` |
| `casaos-userservice-v0.4.8-blockers.patch` | `9e1096018c08231356d419465ac1d4714170c4e94a8915fdf4ec210c9ec82c31` |
| `casaos-appmanagement-v0.4.10-alpha2-blockers.patch` | `bfd1713afddd767c285d0c9cca0174bdff558f7338b017f053614ca2e8ba42fb` |
| `casaos-appmanagement-v0.4.5-blockers.patch`（作废/历史） | `d5543f4bd1815b67e8f7a6049fd5e5d32e0485c41eab025428397bb5b6130dac` |
| `casaos-p3-loong64-0.1.2-appmgr410.tar.gz` | `688fed00656f9ff8a25299989d4ddf28bb6e35b2b10a1964f7acce6efeaa9b14` |
| `casaos-p3-loong64-0.1.1-blockerfix.tar.gz`（已被取代） | `fdfbe2b81447d5bfd5f06918b2bff536a84914ea977afbd71dee89b4a5eaa06a` |

## 5. 验收

### 5.1 设备白名单下沉（loop0）

```bash
truncate -s 64M /tmp/casaos-loop-verify.img
losetup /dev/loop0 /tmp/casaos-loop-verify.img
# token 来自临时改密后的 /v1/users/login（测后已恢复 hash）

curl -X POST http://127.0.0.1:8081/v1/storage -H "Authorization: $TOK" \
  -d '{"path":"/dev/loop0","name":"LoopVerify","format":false}'
# HTTP:403 {"message":"device is not in the supported disk whitelist"}

curl -X PUT http://127.0.0.1:8081/v1/storage -H "Authorization: $TOK" \
  -d '{"path":"/dev/loop0","volume":"/tmp/loopverify","format":"false"}'
# HTTP:403 同上

curl -X PUT http://127.0.0.1:8081/v1/storage -H "Authorization: $TOK" \
  -d '{"path":"/dev/loop0","volume":"/tmp/loopverify","format":"true"}'
# HTTP:403（白名单先于密码检查）
```

结果：

- `blkid /dev/loop0` 始终无输出（无 ext4）；
- `findmnt /tmp/loopverify` 无挂载；
- `o_disk` 中 `/tmp/loopverify` 行数 0；
- 补充负向路径：`/dev/dm-0`、`/dev/mapper/test`、`/dev/nbd0`、`/dev/does-not-exist`
  的 POST 均 **403**（见 `casaos-loop-test-final.log`）；
- helper 直接调用也已拦截：`do_mount /dev/loop0 ...` 与 `FormatDisk /dev/loop0 ext4`
  均返回 1，且未创建挂载目录；
- `losetup -d /dev/loop0`、删除稀疏文件后清理完成；
- 真实盘 `/mnt/Data` 仍 `ext4 rw,noatime`，UUID `678b4321-d7aa-46a1-b53a-e80013fe6ad9` 未变；
- 写入/读回 `/mnt/Data/.casaos-fix-rw` 成功。

密码门（对**支持的白名单设备** `/dev/sda1`，不实际格式化）：

```bash
curl -X PUT .../v1/storage -d '{"path":"/dev/sda1","volume":"/mnt/Data","format":"true"}'
# HTTP:401 Invalid password（无 password）
curl -X PUT .../v1/storage -d '{"path":"/dev/sda1","volume":"/mnt/Data","format":"true","password":"wrong-password"}'
# HTTP:401 Invalid password
# 之后 UUID 仍为 678b4321-...，/mnt/Data 仍挂载
```

### 5.2 首管理员 LAN 抢先（隔离实例）

隔离环境：`/tmp/casaos-us-test`，空 `user.db`，gateway `*:14500`，message-bus/user-service
使用独立 RuntimePath；直接访问 LAN IP `192.168.8.8:14500`。

| 请求 | 结果 |
|---|---|
| LAN `GET /v1/users/status` | **HTTP 403**，`the first administrator must be initialized from localhost` |
| LAN `POST /v1/users/register` | **HTTP 403**，`...registered from localhost` |
| LAN status + 伪造 `X-Forwarded-For: 127.0.0.1` | **HTTP 403** |
| LAN status + 伪造 `X-Real-IP: 127.0.0.1` | **HTTP 403** |
| LAN status + 伪造 `X-Forwarded-For: 127.0.0.1, 192.168.8.8` | **HTTP 403** |
| loopback `GET /v1/users/status` | HTTP 200，`initialized:false`，返回 key |
| loopback `POST /v1/users/register`（带该 key） | HTTP 200，DB 仅 `localtest` admin |
| 初始化后 LAN `GET /v1/users/status` | HTTP 200，`initialized:true`，`key:""` |

伪造头为何也会被拒绝：CasaOS gateway 的 `route/gateway_route.go:rewriteRequestSourceIP`
会先 `Del("X-Forwarded-For")`/`Del("X-Real-IP")`，仅在 `RemoteAddr` 为 loopback 时把
真实上游 hop 重新写回；因此 UserService 取 XFF 首个值即可，且已用上述伪造头实测确认。
原始证据：`/tmp/casaos-us-test-forged.log`。

生产库（已初始化）：LAN `192.168.8.8:8081/v1/users/status` = 200 `initialized:true`；
LAN `POST /v1/users/register` = 400 `Key does not exist`，未新增用户。
生产 `user.db` 始终 `users=1`（`casaos`），无测试用户。

### 5.3 应用安装/卸载与事件链路（memos）

使用最终 v0.4.10-alpha2 二进制（`6ed86c87…`）重跑（2026-10-25 20:54）：

```bash
curl -H "Authorization: $TOK" -H "Accept: application/yaml" \
  http://127.0.0.1:8081/v2/app_management/apps/memos/compose > memos.yaml
curl -X POST 'http://127.0.0.1:8081/v2/app_management/compose?check_port_conflict=true' \
  -H "Authorization: $TOK" -H 'Content-Type: application/yaml' --data-binary @memos.yaml
curl -X DELETE 'http://127.0.0.1:8081/v2/app_management/compose/memos?delete_config_folder=true' \
  -H "Authorization: $TOK"
```

结果：

- 安装 HTTP 200；容器 `memos` Up，`0.0.0.0:18009->5230/tcp`；`curl :18009/` 200；
  `/web/appgrid` 显示 memos running；`/compose/memos/containers` 状态 running；
- 卸载 HTTP 200；容器、`/opt/casaos-p3/apps/memos`、`/DATA/AppData/memos` 删除，
  compose 列表为空，镜像也被移除；
- **事件发布：安装 9/9、卸载 6/6，全部 HTTP 200**；
- 新 app-management 日志 `failed to publish event` = **0**，`message-bus.sock` = **0**；
- 旧二进制最后一次 socket 错误停在 `2026-10-25T18:21:39`，与本次无关；
- 本次安装日志中 `docker:image:pull-begin/progress/pull-end` 均正常，未出现
  `docker:image:pull-error`（镜像已预置；Docker Hub 直连问题见 §8）。
- 原始证据：`/tmp/casaos-app-test-v0410.log`。

说明：宿主 Docker 仍优先解析 Docker Hub 的 IPv6，直接 `docker pull` 会失败；本次用
`curl -4` 拉取后 `docker load` 预置镜像，安装时 `pull-begin/pull-end` 走本地缓存，
未产生 `pull-error`。该宿主 DNS/IPv6 问题仍在 §8，不属于事件通道问题。
拉取尝试中曾临时在 `/etc/hosts` pin IPv4，命令结束立即恢复；恢复前后 sha256 均为
`b05c2f1a…`，一致。

### 5.4 前缀/宿主路径

- `/etc/casaos`、`/var/lib/casaos`、`/usr/share/casaos`、`/etc/casaos.conf` 均**不存在**；
- app-management 重启后日志为 `open /opt/casaos-p3/conf/env`（前缀内），不再访问 `/etc/casaos/env`；
- `run/app-management.url` = `http://127.0.0.1:35499`（v0.4.10-alpha2 实际监听，随重启更新）；
- `/opt/casaos-p3/share/shell` 仅保留 `assist.sh`、`local-storage-helper.sh`、
  `usb-mount.sh`、`usb-mount@.service`。

### 5.5 服务健康与 soak

`healthcheck.sh`：

```
/ping            : pong from gateway service
/                : 200
/v1/sys/version  : 200
/v2/app_management/categories : 200
```

soak：第一次 15 分钟（19:37:48–19:51:50）在中间版本 v0.4.5 上完成；
20:52 切换回 v0.4.10-alpha2 并只重启 app-management+casaos 后，重跑 10 分钟
（20:55:22–21:04:22）作为**最终版本**证据。结果见 §7；24h soak 作为后续/协调者侧继续。

### 5.6 user.db 备份/恢复

- 首次改密前备份：`/tmp/user.db.bak-20261025-192413`（sha256 `5dc790e6…`）；
- 原 hash：`74d1feab1a473f659184ed36676260f5`；
- 每次测试后均 `update o_users set password='74d1feab…'` 恢复；
- 最终：`users=1`，`select password` = `74d1feab…`，`PRAGMA integrity_check` = `ok`；
- 生产库未新增测试用户。
- 文件 sha 与初始备份不同是 SQLite 页重写所致，用户数据/hash 已核对一致。

### 5.7 新包安装自检

`casaos-p3-loong64-0.1.2-appmgr410.tar.gz` 解包后安装到 `/tmp/casaos-pkg-test2`：

```bash
./install.sh --prefix /tmp/casaos-pkg-test2 --store loong64
```

结果：

- 安装退出码 0，未启动任何服务，未写 `/etc/systemd/system/casaos*`；
- `share/shell` 仅含 `assist.sh`、`local-storage-helper.sh`、`usb-mount.sh`、`usb-mount@.service`；
- 三个二进制 sha256 与生产一致（`c11c596…` / `cafebdac…` / `6ed86c87…`）；
- `VERSION` = `0.1.2-appmgr410-p3`；
- `uninstall.sh --purge` 后临时前缀删除。

## 6. 可复现补丁

```bash
cd <CasaOS-LocalStorage v0.4.4>
git apply docs/research/casaos-patches/casaos-localstorage-v0.4.4-blockers.patch
cd <CasaOS-UserService v0.4.8>
git apply docs/research/casaos-patches/casaos-userservice-v0.4.8-blockers.patch
cd <CasaOS-AppManagement v0.4.10-alpha2>
git apply docs/research/casaos-patches/casaos-appmanagement-v0.4.10-alpha2-blockers.patch
```

补丁不含生成的 `codegen/`（见 §3 生成命令）。

可复现性自检：把补丁分别 `git apply` 到干净的 tag 克隆
（v0.4.4 / v0.4.8 / v0.4.10-alpha2），执行
`diff -r --exclude=.git --exclude=codegen` 与本次构建源码树比较，三者均 **IDENTICAL**。
LocalStorage/UserService 另按 §3 从干净树重建，二进制 sha256 与部署值**逐字节一致**：

```
c11c596d…  repro-out/casaos-local-storage
cafebdac…  repro-out/casaos-user-service
```

AppManagement v0.4.10-alpha2 的干净树同样重建成功，二进制
`6ed86c87…` 与部署值**逐字节一致**。

```
6ed86c87…  repro-out/casaos-app-management-v0410
```

## 7. soak 结果

### 7.1 最终版本 AppManagement v0.4.10-alpha2（10 分钟）

命令：`bash /tmp/soak-v0410.sh 10 60`；2026-10-25 20:55:22–21:04:24
（60s × 10），采样 6 服务 PID/RSS/HTTP。

| 服务 | 存活 | HTTP 码 | RSS 首→末 (KB) | RSS 峰值 (KB) | PID |
|---|---|---|---|---|---|
| gateway | 10/10 | 200 ×10 | 22016→17840 | 22528 | 86340 |
| message-bus | 10/10 | 200 ×10 | 33584→35088 | 35088 | 86343 |
| user-service | 10/10 | 200 ×10 | 23888→25424 | 25424 | 391180 |
| app-management | 10/10 | 200 ×10 | 67520→63808 | 67520 | 435412 |
| local-storage | 10/10 | 401 ×10 | 61360→64944 | 64944 | 401778 |
| casaos | 10/10 | 200 ×10 | 34304→35280 | 35280 | 435511 |

- 10/10 样本六服务全部存活；PID 全程不变；无崩溃/重启；
- gateway/message-bus/user-service/app-management/casaos 全 200；
  local-storage `/v1/storage` 全 401 是**未带 JWT 的预期**，且证明服务在响应；
- RSS 无持续上升趋势；app-management 峰值 67,520 KB；
- 原始证据：`/tmp/casaos-soak-v0410.csv`、`/tmp/casaos-soak-v0410.log`。

### 7.2 切换前 v0.4.5（15 分钟，历史证据）

命令：`bash /tmp/soak-fix2.sh 15 60`；2026-10-25 19:37:48–19:51:50（60s × 15）。

| 服务 | 存活 | HTTP 码 | RSS 峰值 (KB) | PID（v0.4.5 时） |
|---|---|---|---|---|
| gateway | 15/15 | 200 ×15 | 19552 | 86340 |
| message-bus | 15/15 | 200 ×15 | 35280 | 86343 |
| user-service | 15/15 | 200 ×15 | 27648 | 391180 |
| app-management | 15/15 | 200 ×15 | 65952 | 394809 |
| local-storage | 15/15 | 401 ×15 | 64512 | 401778 |
| casaos | 15/15 | 200 ×15 | 36624 | 86430 |

- 15/15 样本六服务全部存活；PID 全程不变；无崩溃/重启；
- 因 20:52 将 app-management 替换为 v0.4.10-alpha2 并重启 app-management+casaos，
  该轮不作为最终版本证据；最终证据以 §7.1 为准；
- 原始证据：`/tmp/casaos-soak-fix.csv`、`/tmp/casaos-soak-fix.log`、
  `/tmp/casaos-soak-analysis.txt`。
- **24h 连续运行与真机重启自启未做/由协调者侧继续；C-03 仍不能最终判通过。**

## 8. 未解决/剩余风险

1. **24h soak 与真机重启自启**：本轮完成最终版本 10 分钟 soak（另有一次切换前
   v0.4.5 的 15 分钟）；24h soak 由协调者侧继续/需后续，真机重启自启未验证，
   C-03 仍不能最终判通过。
2. **Docker Hub 镜像拉取路径**：宿主 Docker 优先 IPv6，直连失败；本次用 IPv4 `curl` +
   `docker load` 预置镜像。需修 Docker DNS/代理或镜像源，否则新应用首次安装会失败。
   该问题不影响 CasaOS 事件链路。
3. **AppManagement 版本口径**：最终已恢复为 v0.4.10-alpha2
   （commit `cc80b33…`），并删除其 `PublishEventInSocket` 首调；`-v` 仍显示上游硬编码的
   `v0.4.5`，版本以 tag/commit/哈希为准。中间 v0.4.5 补丁已作废。
4. **PUT `format` 省略的兼容行为**：仍默认格式化（历史行为），但现在必须通过密码
   二次确认；建议客户端始终显式传 bool。
5. **密码二次确认依赖 UserService**：UserService 不可用时格式化会 fail-closed（401）；
   这是有意的安全取舍。
6. **新包/旧包与文档锚点**：新包 `casaos-p3-loong64-0.1.2-appmgr410.tar.gz`
   （`688fed00…`）已移除危险脚本并含最终 v0.4.10-alpha2 二进制；0.1.1 已被取代，
   旧 0.1.0 包 `6efcbb60…` 仍含危险脚本，发布时不得再分发 0.1.0/0.1.1。
   按任务要求未改 `docs/CASAOS-P3.md`（仍锚定 0.1.0），发布前需同步文档/sidecar。
7. `o_disk` 仍有历史 NBD 行 `/mnt/testdisk_nbd0p1`（与本轮无关）。
8. local-storage 的 `DELETE /v1/storage` 未加白名单（仅卸载、不格式化）；如需更严格
   的“所有写操作”口径，可后续补。
9. `POST /v1/storage` 的 `format=true` 仍不要求密码（保持文档 C-01 真机格式化流程），
   但已受服务端白名单约束；如要求所有破坏性路径都二次确认，可后续加密码门。
10. AppManagement v1 的 Docker daemon 配置 API 仍写 `/etc/docker/daemon.json`
    （宿主 Docker 配置的明确例外，类似 systemd unit）；本次验收未调用该 API。
11. 构建时 `/home` 曾 100% 满（150G，0 可用），已清理可再生的 Go build cache；
    当前仍仅约 450MB 可用，建议后续清理宿主 `/home`（本轮未删用户数据/模块缓存）。
