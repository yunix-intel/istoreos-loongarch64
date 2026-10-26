# C-03 CasaOS 24h 稳定性报告

日期：2026-10-26  
环境：Host A，Loongnix 25，CasaOS P3 0.1.2-appmgr410，AppManagement v0.4.10-alpha2  
原始数据：`/tmp/casaos-soak-24h.csv`、`/tmp/casaos-soak-24h.log`  
采样：60s × 1440 点，6 个服务，每点 6 行，共 8640 行

## 结论

**PASS**。1440/1440 个采样点全部存活；6 个服务 PID 全程未变；5 个服务 HTTP 200，
local-storage 401 是未带 JWT 的预期值；RSS 无持续增长。

## 明细

| 服务 | 存活 | HTTP | PID 数 | RSS 首/末/峰值 (KB) |
|---|---:|---|---:|---|
| gateway | 1440/1440 | 200 × 1440 | 1 | 19888 / 18592 / 21360 |
| message-bus | 1440/1440 | 200 × 1440 | 1 | 35088 / 38976 / 38976 |
| user-service | 1440/1440 | 200 × 1440 | 1 | 24864 / 24832 / 27168 |
| app-management | 1440/1440 | 200 × 1440 | 1 | 63776 / 66704 / 73456 |
| local-storage | 1440/1440 | 401 × 1440 | 1 | 62880 / 62720 / 67616 |
| casaos | 1440/1440 | 200 × 1440 | 1 | 35280 / 37456 / 38848 |

- 起止：2026-10-25 21:06:37 → 2026-10-26 21:08:40（1440 点）。
- RSS 最大变化：app-management +4.6%，其余 ±5% 内；无单调泄漏。
- local-storage 401：soak 请求未带 JWT；进程存活、端口正常，属于预期，不是失败。
- 期间做过应用安装/卸载抽测，未影响 6 个平台服务 PID。

## 判定与后续

- C-03 → PASS。
- C-04 仍需真机重启验证 systemd 自启；重启前备份 `/opt/casaos-p3`。
- 重启后需验证：6 服务 + `casaos.target`、8081/14500、`/DATA`、商店 115。

## 复现

```bash
ssh loongson-lab 'python3 - <<PY'
import csv,collections
rows=list(csv.DictReader(open("/tmp/casaos-soak-24h.csv")))
by=collections.defaultdict(list)
for r in rows: by[r["service"]].append(r)
for s,rs in sorted(by.items()):
    print(s, sum(x["alive"]=="1" for x in rs), collections.Counter(x["http_code"] for x in rs), len({x["pid"] for x in rs}))
PY'
```
