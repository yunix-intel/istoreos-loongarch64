# S-C5 数据保留首轮（actual-budget）

日期：2026-10-26  
环境：Host A，CasaOS P3，AppManagement v0.4.10-alpha2

## 结论

**PARTIAL**：安装、重启、`delete_config_folder=false` 保留数据、重装后数据仍在，
均通过；**CasaOS 默认 DELETE 会删除数据目录**，必须在卡片/文档写明；升级路径未测
（当前无新 digest）。

## 步骤与结果

| 步骤 | 命令/动作 | 结果 |
|---|---|---|
| 安装 | `POST /v2/app_management/compose?check_port_conflict=true` | 200；容器 Up；`http://127.0.0.1:18101/` 200 |
| 写数据 | `/DATA/AppData/actual-budget/data/verify.txt` | 写入成功 |
| 重启 | `PUT /compose/actual-budget/status` body `"restart"` | 200；容器重建；`verify.txt` 仍在；HTTP 200 |
| 默认卸载 | `DELETE /compose/actual-budget` | 200；**`/DATA/AppData/actual-budget` 被删除** |
| 保留卸载 | `DELETE /compose/actual-budget?delete_config_folder=false` | 200；`verify.txt` 保留 |
| 重装 | 再次 POST 同一 compose | 200；容器 Up；`verify.txt` 仍为 `verify-keep`；HTTP 200 |
| 清理 | `DELETE ...?delete_config_folder=false` + 手工删除测试目录 | 端口 18101 释放 |

## 关键发现

`DeleteConfigFolder` 的 OpenAPI 默认值是 **true**。CasaOS UI/API 默认卸载会删除
`/DATA/AppData/<id>` 下的应用数据；需要保留数据时必须显式传
`?delete_config_folder=false`。这会影响所有应用的升级/卸载策略，商店卡片和文档
必须写明，不能默认“卸载保留数据”。

## 未完成

- 升级：没有同 tag 的新 digest，`PATCH` 只能验证幂等重建；标 NOT TESTED。
- 其他 5 类代表应用（PostgreSQL、MariaDB、对象存储、host 网络、设备类）待
  `casaos-gate-exec` 会话执行。
- 应用自身数据（预算文件/DB）未通过 UI 创建；本轮只验证卷持久化与卸载策略。
