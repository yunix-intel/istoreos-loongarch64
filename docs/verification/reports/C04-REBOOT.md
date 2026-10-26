# C-04 CasaOS 重启自启与安装链路报告（Host A）

日期：2026-10-26  
环境：Host A，Loongnix 25，CasaOS P3 0.1.2-appmgr410  
备份：`/build/backup/casaos-p3-pre-reboot-20261026.tar.gz`，sha256
`be7fa4b4deb44e5a41a7ec3fe5876761e8785550d5f3ac8e33d35d216c88cd4b`

## 结论

**Host A 闸门部分 PASS**：

- 冷重启 26 秒后 SSH 恢复；
- `casaos.target` 及 6 个服务 unit 全部 active，无 failed；
- AppManagement API 返回 115；
- Docker 自启（mihomo Up）；
- 2TB SATA `sda1` 自动挂载 `/mnt/Data`；
- 商店安装 Gatus → HTTP 200 → 卸载后端口释放。

**未完成**：B 机 sdb 干净安装（G1b）按用户要求等龙芯 NAS 项目完成后执行。

## 证据

| 检查 | 结果 |
|---|---|
| `systemctl is-active casaos.target` + 6 服务 | 7/7 active |
| `systemctl --failed` | 空 |
| `ss -ltnp` 8081 | casaos-gateway 监听 |
| `/v2/app_management/apps` | 115 |
| `docker ps` | mihomo Up |
| `sda1` 挂载 | `/mnt/Data` ext4 rw,noatime |
| Gatus 安装 | 容器 Up，`http://127.0.0.1:18124/` 200 |
| Gatus 卸载 | 容器删除，18124 释放 |

## 非阻塞告警

- local-storage 启动时对 `/dev/sdb`（58G USB，USB bridge 0x058f:0x6366）执行 SMART
  失败：`Unknown USB bridge`，不影响启动；SATA `/dev/sda` 的 SMART 此前已通过。
- local-storage 日志写 “This process is not running as a systemd service.”，但
  systemd unit 为 active 且端口正常；属于二进制内的检测提示，记为观察项。
- `/DATA` 是根文件系统下的目录，不是独立挂载；CasaOS 数据路径正常。

## 复现

```bash
ssh loongson-lab 'systemctl is-active casaos.target casaos-gateway casaos-message-bus casaos-user-service casaos-app-management casaos-local-storage casaos'
ssh loongson-lab 'curl -s http://127.0.0.1:8081/v2/app_management/apps | python3 -c "import sys,json;print(len(json.load(sys.stdin)[\"data\"][\"list\"]))"'
```

## 后续

- G1b：B 机 sdb 干净安装 CasaOS 0.1.3-store115（等 NAS 项目完成）。
- C-04 的整体发布结论需等 G1b；Host A 部分可先作为通过证据。
