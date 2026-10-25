# CasaOS P3 剩余发布闸门复核

日期：2026-10-25
环境：Host A（SSH `loongson-lab`，`yunix-pc`，LoongArch64/3A6000，Loongnix 25）；
前缀 `/opt/casaos-p3`，gateway `:8081`；真实盘 `/dev/sda1` ext4 → `/mnt/Data`。
方法：只读检查 + 隔离实例（14500–14599）；未重启 A 机、未格式化真实盘。
临时改测试用户密码前备份 `user.db`，测后恢复原 hash（`integrity_check=ok`）；
拉取 memos 镜像时曾临时 pin `/etc/hosts` IPv4，已恢复。

## 结论

| # | 项目 | 状态 | 结论 |
|---|---|---|---|
| 1 | 应用安装/卸载 | PASS | memos 经 v2 API 安装，容器 Up、UI 200；卸载后容器/compose/数据/镜像均清理 |
| 2 | 设备白名单下沉 | FAIL | loop0 未被拒绝；PUT 实际将其格式化为 ext4 并挂载 |
| 2 | 首管理员局域网抢先 | FAIL | 空库隔离实例经 LAN 用 status key 注册 admin 成功 |
| 2 | 端口/前缀路径 | FAIL | 端口固定 8081 且冲突硬失败；但 app-management 仍连 `/tmp/message-bus.sock`，随包 helper 含宿主绝对路径 |
| 3 | 24h 稳定性 | BLOCKED | 36 分钟 soak 通过；24h 未验证，需后续 |
| 4 | systemd 自启（静态） | PASS | 7 unit verify 0 错；未 enable/start，真机自启未验证 |
| 5 | 升级/卸载数据保留 | PASS | 重装保留 conf/data/apps；默认卸载保留 data/apps，`--purge` 全删；文档有路径冲突 |

**发布闸门：保持关闭，CasaOS P3 不发布。**

## 1. 应用安装/卸载（PASS）

- 安装接口：`POST /v2/app_management/compose?check_port_conflict=true`，body 为
  `GET /v2/app_management/apps/memos/compose` 返回的 YAML；token 来自临时改密后的
  `POST /v1/users/login`。商店应用使用自身端口 `18009`（空闲），14500–14599 仅用于隔离实例。
- 结果：容器 `memos` Up，`0.0.0.0:18009->5230/tcp`；`curl :18009/` 200；
  `/v2/app_management/web/appgrid` 显示 `memos running`；
  `/v2/app_management/compose/memos/containers` 状态 `running`。
- 卸载：`DELETE /v2/app_management/compose/memos`（默认 `delete_config_folder=true`）。
  容器、`/opt/casaos-p3/apps/memos`、`/DATA/AppData/memos` 均删除；
  `/v2/app_management/compose` 返回空；镜像 `yunixintel/memos:loong64` 也被移除。
- 备注：宿主 DNS 对 Docker Hub 只返回 AAAA，`docker pull` 失败；临时 pin IPv4 预拉镜像，
  测试后恢复。因此本次验证的是 CasaOS 安装/启动/卸载链路，不是镜像拉取链路。
- 商店 `uptimekuma` 定义把卷 target 写成 `"Self-hosted monitoring tool."`，不可用；
  `memos` 定义正常。
- 卸载默认删除持久数据，若产品预期“保留数据”需显式 `delete_config_folder=false`。

## 2. 三个审查 BLOCKER

### 2.1 设备白名单未下沉（FAIL）

代码证据（`/var/tmp/CasaOS-LocalStorage/route/v1/storage.go`）：
- `PostAddStorage` L150：先按 `format` 执行 `DeletePartition/AddPartition`（L175–195），
  L197 才调 `IsDiskSupported`，且只用于“是否把整盘当子项”，不拒绝请求。
- `PutFormatStorage` L301：`js := make(map[string]string)`，不读 `format`；
  L337 无条件 `FormatDisk(path)`；密码二次确认 L308–312 被注释。
- `IsDiskSupported`（`service/disk.go` L783）只接受 sata/nvme/spi/sas/virtio/mmc/ata。

实测（`/dev/loop0` 绑定 64M 稀疏文件，测试后已 detach 并删除）：
```bash
curl -X POST :8081/v1/storage -H "Authorization: $TOK" \
  -d '{"path":"/dev/loop0","name":"LoopVerify","format":false}'
# -> {"success":200,"message":"ok"}；未挂载
curl -X PUT :8081/v1/storage -H "Authorization: $TOK" \
  -d '{"path":"/dev/loop0","volume":"/tmp/loopverify","format":"false"}'
# -> 200；findmnt: /tmp/loopverify /dev/loop0 ext4 rw；blkid TYPE=ext4
# o_disk 新增 UUID=84f22cb6... /tmp/loopverify
```
- `format:"false"` 仍触发格式化；loop 属非白名单设备，写操作未返回 4xx。
- 真实盘 `/dev/sda1` 全程未动，仍挂 `/mnt/Data`。
- 清理：`DELETE /v1/storage {"path":"/dev/loop0","volume":"/tmp/loopverify"}` 200，
  DB 行删除；`losetup -l` 为空。
- 结论：审查要求“loop/nbd 写操作返回 4xx”未实现，BLOCKER 仍在。

### 2.2 首管理员可被局域网抢先（FAIL）

隔离实例：同一二进制、空 `user.db`、gateway `*:14500`，未暴露公网。
```bash
curl http://192.168.8.8:14500/v1/users/status
# {"initialized":false,"key":"2e84f18a-..."}
curl -X POST http://192.168.8.8:14500/v1/users/register \
  -d '{"username":"lantest","password":"VerifyLan-2026","key":"2e84f18a-..."}'
# -> {"success":200}; o_users: 1|lantest|admin
```
- `status` 未认证即返回 key；key 每次请求变化，但任意 LAN 客户端都能获取；
  注册未限制 `127.0.0.1`。结论：BLOCKER 仍在。
- 测试后已停止隔离实例、删除临时前缀；生产库未新增用户。

### 2.3 端口/前缀路径（FAIL；端口子项 PASS）

- 端口：`conf/gateway.ini` 固定 `Port=8081`。占用 8081 再启一个 gateway：
  `listen tcp :8081: bind: address already in use`，未漂移到 8082，符合“不静默 first-free”。
- 前缀：6 个服务 conf、7 个 unit、start/health 脚本均指向 `/opt/casaos-p3`；
  安装未在 `/etc/casaos*`、`/usr/share/casaos` 新增路径。
- 运行时 socket 未重定向：memos 安装/卸载期间 app-management 记录 15 个事件发布失败，
  均为 `dial unix /tmp/message-bus.sock: no such file or directory`；
  message-bus 实际为 `http://127.0.0.1:40157`，`/tmp/message-bus.sock` 不存在。
  事件/通知链路实际不可用。
- 随包 `share/shell/delete-old-service.sh` 仍写 `/etc/casaos.conf`、`/usr/share/casaos/shell`、
  `/var/lib/casaos/{conf,db,temp}`，并 `rm` `/usr/local/bin/casaos`、`systemctl restart casaos`；
  `helper.sh` 仍含 `systemctl stop docker`、`cp -r /var/lib/docker/*`。两者未被 unit 引用，
  但作为随包脚本存在，前缀路径审计未闭环。
- 结论：端口口径 PASS；运行时 socket/随包 helper FAIL（审查 MAJOR 项未关闭）。

## 3. 24h 稳定性（BLOCKED）

- soak：60s × 36 次，采样 2026-10-25 18:23:11–18:58:20（跨度 35m09s），记录 6 服务 PID/RSS/健康。
- 结果：36/36 样本六服务健康 200；6 个 PID 全程不变；无崩溃/重启。
- RSS（首→末，KB）：gateway 19296→21712（+2416）；message-bus 35120→33408；
  user-service 23520→22432；app-management 66496→59648；local-storage 62752→66800；
  casaos 37104→36224。峰值 RSS（KB）：gateway 21712、message-bus 35120、
  user-service 23520、app-management 66496、local-storage 67328、casaos 38032
  （均 <68MB）；无明显泄漏趋势。
- 原始证据：`/tmp/casaos-soak-verify.csv`、`/tmp/casaos-soak-verify.log`。
- **24h 连续运行、系统级重启自启、长时间日志/内存趋势未验证，C-03 不能判通过。**
- 历史风险：`user-service.stdout.log` 在 2026-10-20 10:22 因 message-bus 断连，
  `EventListen` nil pointer panic 一次；前缀 `start.sh` 无 supervisor，若复现会直接停服。

## 4. systemd 自启（静态 PASS）

- 7 个 unit（6 服务 + target），`ExecStart` 均为 `/opt/casaos-p3/bin/...`，
  `Environment=CASAOS_CONFIG_PATH=/opt/casaos-p3/conf`，`Restart=on-failure`，
  `After=network-online.target docker.service`。
- `systemd-analyze verify /opt/casaos-p3/systemd/*` 退出码 0，无 CasaOS 相关告警
  （仅有宿主机 `printermonitor.service` 的无关 syslog 警告）。
- `/etc/systemd/system/casaos*` 不存在；`systemctl is-enabled casaos.target` = not-found，
  `is-active` = inactive；未 enable/start。真机重启自启未验证（按要求不做）。
- 缺口：unit 无 `NoNewPrivileges`/`ProtectSystem`/`PrivateTmp`/`User=` 等 hardening；
  服务以 root 运行并持 docker.sock。

## 5. 升级/卸载数据保留（PASS，文档有冲突）

- 隔离前缀实测：`install.sh` 二次执行（模拟升级）→ `data/db/retention.marker`、
  `apps/memos/retention.marker`、自定义 `conf/gateway.ini` 均保留；日志
  `keep existing conf` 6 条。
- `uninstall.sh`（无 `--purge`）→ 程序目录/README/VERSION 删除，`data/`、`apps/` 保留；
  `--purge` → 前缀全删；`/DATA` 未动。与 README 一致。
- 风险：升级无 DB 备份/迁移/回滚步骤；`APP-DESIGNS.md` 5.1.3/5.1.4 仍写数据在
  `/var/lib/casaos`，实际为 `$PREFIX/data`，按旧路径备份/恢复会漏数据。
- 安装包 sha256 `6efcbb60…7bea` 与 sidecar 一致；`/opt` 二进制与 stage 二进制 sha256 一致。

## 剩余风险 / 发布判定

- 2.1 任意已登录用户可对 loop/nbd 等非白名单设备触发格式化，且无密码二次确认 → 高危。
- 2.2 首次启动窗口内 LAN 任意主机可抢占 admin（等同宿主 root + docker.sock）→ 高危。
- 2.3 事件链路因 `/tmp/message-bus.sock` 失效；随包旧 helper 可改宿主 `/etc`、`/var/lib` → 中危。
- `o_disk` 仍残留旧 NBD 行 `/mnt/testdisk_nbd0p1`（历史测试数据，与本次无关）。
- C-03 24h 与真机重启自启未完成；C-04 评审未通过。
- **结论：CasaOS P3 不发布。** 修复 2.1/2.2/2.3 并重跑本报告后，再做 24h soak。
