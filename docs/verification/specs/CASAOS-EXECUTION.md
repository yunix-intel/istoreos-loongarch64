# CasaOS P3 闸门与全量功能验证执行规范

日期：2026-10-26  
适用会话：`casaos-gate-exec`（阶段 A + B）  
上位计划：[PHASE-2-FULL-VERIFICATION.md](../PHASE-2-FULL-VERIFICATION.md)  
关联：[CASAOS-P3.md](../../CASAOS-P3.md)、[CASAOS-PLAN.md](../../CASAOS-PLAN.md)、
[verify-casaos-store.md](../../research/verify-casaos-store.md)、
[verify-casaos.md](../../research/verify-casaos.md)

> **执行状态（2026-10-26 22:20）**：C-03 soak PASS、A2 商店 115 已通过、C-04 Host A
> 重启自启 PASS（报告 `../reports/C03-SOAK.md`、`../reports/C04-REBOOT.md`）。
> 新执行会话从 §5（S-C5）和 §6/§7（平台/应用矩阵）开始；§2–§4 只作为已完成证据，
> 除非状态变化，不要重复重启。B sdb 干净安装（G1b）等 NAS 项目完成后由
> `casaos-clean-exec` 执行。

本规范只覆盖 CasaOS（E0/E1）。iStore la5/p1、B 机 sdb 干净安装、OMV 分别由
`ISTORE-EXECUTION.md`、`casaos-clean-exec`、`OMV-O01-O03.md` 负责。

## 0. 使用方式、判定与红线

### 0.1 执行入口

1. 每个执行会话先读本规范与 `PHASE-2-FULL-VERIFICATION.md`，不得自行改变判定口径。
2. 所有命令默认在 Host A 上执行；先登录：

```bash
ssh -o ClearAllForwardings=yes -o BatchMode=yes loongson-lab
```

> Host A 的默认 SSH 配置带有 `127.0.0.1:18081` 本地转发，直接 `ssh loongson-lab`
> 会失败：`bind [127.0.0.1]:18081: Address already in use`。必须加
> `-o ClearAllForwardings=yes`，或由用户修正 `~/.ssh/config`。这是实测结论，不是可选项。

3. 统一变量：

```bash
export B=http://127.0.0.1:8081
export P=/opt/casaos-p3
export EV=/build/verify-evidence/e0
mkdir -p "$EV"/{a1,a2,a3,a5,platform,batches}
```

4. 证据路径：仓库内 `docs/verification/evidence/e0/...` 只放摘要、HTTP 头、截图、哈希；
   原始大日志放 `/build/verify-evidence/e0/...`。凭据只放 `/build/verify-secrets`
   （目录 0700、文件 0600），不得进 Git。
5. 命令中的 `<id>`、`<container>`、`<image>`、`<secret>`、`<sha256>`、`<date>` 等
   是执行时必须替换的占位符；不要把尖括号原样执行。密码只在 shell 变量/凭据文件
   中出现，证据中打码。

### 0.2 判定

| 判定 | 条件 |
|---|---|
| PASS | 有命令输出/HTTP 状态/截图/日志，结果与预期一致，且证据路径已写入结果 JSON |
| PARTIAL | 主路径通过，但有明确未覆盖功能/环境限制；必须在 `not_covered` 写明 |
| BLOCKED | 上游、硬件、外部依赖或安全前置阻塞；附复现命令、根因、证据 |
| NOT TESTED | 未执行；必须写原因，不能默认通过 |

### 0.3 红线

1. 不能把“首页 200”写成“功能全通过”。
2. 不能把 `dry-run`、`validate_definitions.py` 或“商店计数 115”写成“安装通过”。
3. 不能把“手动点击成功一次”写成“全部功能回归”。
4. 不能把 `local-storage` 的 401 当失败；它是未带 JWT 的基线值，必须按第 2 节比对。
5. 不能对 2TB `/dev/sda`（`/dev/sda1` → `/mnt/Data`）做任何格式化、分区、写测试、
   `mkfs`、`dd`、`wipefs`、`local-storage` 写操作；只允许只读查看和只读 SMART。
6. 不能格式化或写入 58G `/dev/sdb`（`LOONGSONISO`）；iStore 写盘不属于本规范。
7. 不能用公开镜像替代 `local/*` 做 E1 私人版验证；公开版测试不得出现 `local/*`。
8. 任何 PASS 都必须能回答“证据在哪个路径、哈希是什么”。

## 1. 前置检查与备份

### 1.1 Host A 基线（执行前 15 分钟）

在 Host A 上执行并保存到 `$EV/preflight.txt`：

```bash
{
  date -Is
  hostname
  uname -a
  . /etc/os-release && echo "$PRETTY_NAME"
  systemctl --version | head -1
  docker version --format 'server={{.Server.Version}} api={{.Server.APIVersion}}'
  cat "$P/VERSION"
  sha256sum "$P"/bin/*
  systemctl list-unit-files 'casaos*' --no-pager
  systemctl is-enabled casaos.target
  ss -lntp | grep -E ':(8081|40157|34989|35499|35133|43811)\b' || true
  findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS /mnt/Data
  lsblk -o NAME,SIZE,TYPE,TRAN,SERIAL,MODEL,FSTYPE,MOUNTPOINT
  df -h /DATA /mnt/Data /build /var /
} | tee "$EV/preflight.txt"
```

预期/必须记录：

| 项 | 当前实测 | 说明 |
|---|---|---|
| 主机 | `yunix-pc` | Host A，LoongArch64 3A6000 |
| 系统 | Loongnix GNU/Linux 25 | 内核 `6.6.52-loong64`，systemd `257` |
| Docker | `26.1.5+dfsg1`，API 1.45 | 容器运行时 |
| CasaOS 安装 | `/opt/casaos-p3`，网关 `:8081` | 2026-10-26 重启后由 systemd `casaos.target` 管理；前缀 `start.sh` 仅作回退 |
| `/opt/casaos-p3/VERSION` | `0.1.2-appmgr410-p3+store115` | 2026-10-26 已修正；原 0.1.2 包内元数据为 0.1.0-p3，0.1.3 包会写 0.1.3-store115-p3 |
| app-management 二进制 | `sha256 6ed86c87…6c78` | 已修复版 v0.4.10-alpha2 |
| 6 个服务 | systemd `casaos.target` 拉起 | 2026-10-26 重启后 7 unit 全 active；前缀 `start.sh` 仅作回退 |
| `/mnt/Data` | `/dev/sda1` ext4 `rw,noatime` | 2TB 数据盘，只读 |
| `/DATA` | 根文件系统上的普通目录 | 不是 `/mnt/Data` 的挂载点；应用数据写入这里 |
| 磁盘余量 | `/DATA` 13G、`/build` 4.8G、`/var` 4.5G | `/build`、`/var` 偏紧，按第 7.6 节阈值暂停 |

补充检查：

```bash
# 凭据文件：不存在时由用户提供密码后创建；不要回显密码
if [ ! -f /build/verify-secrets/casaos.env ]; then
  sudo install -d -m 700 /build/verify-secrets
  sudo sh -c 'umask 077; cat > /build/verify-secrets/casaos.env <<EOF
CASAOS_USER=casaos
CASAOS_PASSWORD=REPLACE_WITH_USER_PROVIDED_PASSWORD
EOF'
  echo "edit password before continuing"; exit 1
fi
sudo chmod 600 /build/verify-secrets/casaos.env
```

```bash
# 6 个 systemd 服务必须 active；run/*.pid 可能是旧前缀实例的陈旧文件
for u in casaos-gateway casaos-message-bus casaos-user-service \n         casaos-app-management casaos-local-storage casaos; do
  printf "%s %s pid=%s
" "$u" "$(systemctl is-active "$u")" "$(systemctl show -p MainPID --value "$u")"
done

# 商店定义数量：两个目录都应为 115
find "$P/appstore/default/Apps" -mindepth 1 -maxdepth 1 -type d | wc -l
find "$P/appstore/loong64/Apps" -mindepth 1 -maxdepth 1 -type d | wc -l

# 当前 API 预期 115（A2 已重启 app-management）
curl -s "$B/v2/app_management/apps" | jq '.data.list | length'
```

> 当前 `data.list` 是“以 app id 为 key 的对象”，不是数组。计数用 `length`，
> 取 id 用 `keys[]`；不要写 `list[0]`。

### 1.2 备份

在改动任何文件、重启任何服务之前执行：

```bash
TS=$(date +%F-%H%M)
sudo tar czf "/build/backup-casaos-p3-$TS.tar.gz" \
  -C "$P" conf apps appstore data VERSION scripts systemd
sudo tar czf "/build/backup-casaos-systemd-$TS.tar.gz" \
  -C /etc/systemd/system casaos.target casaos-gateway.service \
  casaos-message-bus.service casaos-user-service.service \
  casaos-app-management.service casaos-local-storage.service casaos.service
sudo sha256sum "/build/backup-casaos-p3-$TS.tar.gz" \
  "/build/backup-casaos-systemd-$TS.tar.gz" \
  | sudo tee "/build/backup-casaos-$TS.sha256"
sudo tar tzf "/build/backup-casaos-p3-$TS.tar.gz" | head -20
```

验收：

- 两个 tar.gz 存在，sha256 文件存在；
- `tar tzf` 能看到 `conf/gateway.ini`、`data/db/user.db`、`appstore/default/Apps/joplin-server/docker-compose.yml`；
- 备份后再次 `sha256sum` 与文件内容一致；
- 备份路径和 sha256 写入 `verify/state/casaos-gate-exec.yaml`。

### 1.3 禁写清单（每次批次开始前复述）

| 设备/路径 | 规则 |
|---|---|
| `/dev/sda`、`/dev/sda1`、`/mnt/Data` | 2TB Asgard SATA，已有用户数据；只读 `lsblk`/`findmnt`/`df`/`smartctl -a`；禁止格式化/分区/挂载写/测试文件 |
| `/dev/sdb`、`/dev/sdb1` | 58G `LOONGSONISO` U 盘；只读 `udevil info`；禁止写盘/格式化/挂载写 |
| `/dev/loop*`、`/dev/nbd*`、`/dev/dm-*` | 不作为写测试目标；只用于“必须被拒绝”的负向测试 |
| `/opt/casaos-p3` 以外系统目录 | 不修改 `/etc`、`/usr`、`/var/lib/casaos`；systemd unit 的例外仅限本规范第 4 节 |

### 1.4 soak 完成与时间窗口

```bash
[ "$(date +%s)" -ge "$(date -d '2026-10-26 21:06:00' +%s)" ] \
  && echo soak-window-open || { echo wait-until-2106; exit 1; }
wc -l /tmp/casaos-soak-24h.csv
```

预期 `8641` 行（1 行表头 + 6 服务 × 1440 采样）。若少于 8641，等待，不开始 A1。

## 2. C-03 24h soak 分析

### 2.1 冻结证据

```bash
mkdir -p "$EV/a1"
sha256sum /tmp/casaos-soak-24h.csv /tmp/casaos-soak-24h.log \
  | tee "$EV/a1/soak.sha256"
cp /tmp/casaos-soak-24h.csv "$EV/a1/casaos-soak-24h.csv"
cp /tmp/casaos-soak-24h.log "$EV/a1/casaos-soak-24h.log"
```

本规范编写时实测锚点：

| 文件 | sha256 |
|---|---|
| `/tmp/casaos-soak-24h.csv` | `067510de7ec21cc0fd4a73198771012f98565653395f4a7deeca9b71679f8d9a` |
| `/tmp/casaos-soak-24h.log` | `b8b64f7c86baaa6fe554b4e2d194dcd9f29234ec89b542b561aa7935dd2751b0` |

执行时若哈希不同，先确认 CSV 是否被追加/重写，再以新哈希记录；不得直接覆盖旧证据。

### 2.2 统计命令

```bash
python3 - <<'PY' | tee "$EV/a1/soak-stats.txt"
import csv, collections, datetime, statistics
p = "/tmp/casaos-soak-24h.csv"
rows = list(csv.DictReader(open(p)))
print("rows", len(rows))
by = collections.defaultdict(list)
for r in rows:
    by[r["service"]].append(r)
for s, rs in sorted(by.items()):
    n = len(rs)
    alive = sum(int(r["alive"]) for r in rs)
    pids = [r["pid"] for r in rs]
    rss = [int(r["rss_kb"]) for r in rs]
    codes = collections.Counter(r["http_code"] for r in rs)
    ts = [datetime.datetime.fromisoformat(r["timestamp"]) for r in rs]
    gaps = [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]
    print(f"{s:16s} n={n} alive={alive}/{n} pid_uniq={len(set(pids))} "
          f"pid={pids[0]} rss_first={rss[0]} rss_last={rss[-1]} "
          f"rss_min={min(rss)} rss_max={max(rss)} codes={dict(codes)} "
          f"max_gap_s={max(gaps) if gaps else 0}")
print("first_ts", rows[0]["timestamp"], "last_ts", rows[-1]["timestamp"])
PY
```

### 2.3 判定规则（必须逐条落表）

| 规则 | 通过条件 |
|---|---|
| 采样完整性 | 总行数 8641；每个服务 1440 行；无重复时间戳 |
| 存活 | 每个服务 `alive=1440/1440` |
| PID | 每个服务 `pid_uniq=1`；若 PID 变化，说明重启/崩溃，C-03 不通过 |
| 时间跨度 | 首末时间跨度 ≥ 23h50m；最大采样间隔 ≤ 120s（60s 采样允许抖动） |
| HTTP 基线 | gateway/message-bus/user-service/app-management/casaos 全 200；local-storage 全 401 |
| RSS | 首末差值不超过 `max(20%, 8MB)`，峰值 < 100MB；无单调增长趋势 |
| 日志 | soak 日志无 panic、无 `bind: address already in use`、无连续重连失败 |

**local-storage 401 说明**：`/v1/disks` 等接口需要 JWT；soak 探针未带 token，
401 是预期基线，不是失败。若出现 200，记录“基线变化”，不要直接判失败，也不要
把它当作磁盘功能通过。

### 2.4 实测基线（2026-10-25 21:06:37 → 2026-10-26 21:08:40）

| 服务 | 采样 | 存活 | PID | HTTP | RSS 首→末（KB） | RSS 峰值 |
|---|---:|---:|---|---|---|---:|
| gateway | 1440 | 1440 | 86340 | 200 ×1440 | 19888→18592 | 21360 |
| message-bus | 1440 | 1440 | 86343 | 200 ×1440 | 35088→38976 | 38976 |
| user-service | 1440 | 1440 | 391180 | 200 ×1440 | 24864→24832 | 27168 |
| app-management | 1440 | 1440 | 435412 | 200 ×1440 | 63776→66704 | 73456 |
| local-storage | 1440 | 1440 | 401778 | 401 ×1440 | 62880→62720 | 67616 |
| casaos | 1440 | 1440 | 435511 | 200 ×1440 | 35280→37456 | 38848 |

- 总行数 8640；首末跨度 24.03h；最大采样间隔 63s。
- 六服务 PID 全程不变；RSS 均 <74MB，无泄漏趋势。
- 结论：按 2.3 规则 **PASS**。该结论只对 0.1.2-appmgr410 soak 窗口成立；
  A2 重启 app-management 后 PID 改变，不影响本结论。

### 2.5 报告模板

写入 `docs/verification/reports/C03-SOAK.md`：

```markdown
# C-03 24h Soak

- 结论：PASS / BLOCKED
- 环境：Host A，Loongnix 25，6.6.52-loong64
- 证据：/tmp/casaos-soak-24h.csv（sha256 ...）、...log（sha256 ...）
- 采样：first ... last ...，总行数 ...，每服务 ...

| 服务 | 采样 | 存活 | PID 唯一 | HTTP 码 | RSS 首/末/峰 | 判定 |
|---|---:|---:|---|---|---|---|

## 异常与解释
- local-storage 401：基线，未带 JWT。
- 其他：

## 判定规则
- ...
```

## 3. A2：商店 115（S-C6 / C-06）

### 3.1 前置

- C-03 已分析并留证（2.5 报告存在）。
- 备份已完成（1.2）。
- 历史前置是 API 18（进程内缓存）；2026-10-26 重启后已为 115。若复测，先记录当前值：

```bash
curl -s "$B/v2/app_management/apps" | jq '.data.list | length' \
  | tee "$EV/a2/pre-count.txt"
```

- 记录 app-management 启动时间与 appstore 目录时间：

```bash
systemctl show -p MainPID -p ActiveEnterTimestamp --value casaos-app-management \
  | tee "$EV/a2/pre-process.txt"
stat -c '%y %n' "$P/appstore/default/Apps" "$P/appstore/default/category-list.json" \
  | tee -a "$EV/a2/pre-process.txt"
```

若进程启动时间早于 115 个定义同步时间，18 是旧缓存，重启即可；这是预期路径。
若 `pre-count.txt` 已经是 115，说明 app-management 已被重启过：记录后跳过 3.2，
直接执行 3.3。

### 3.2 重启 app-management（已完成；systemd 优先）

A2 已在 C-04 之前执行；当前由 systemd 管理。若复测：

```bash
if systemctl is-active --quiet casaos-app-management; then
  sudo systemctl restart casaos-app-management
else
  # 回退：前缀实例
  PID=$(cat "$P/run/app-management.pid")
  kill "$PID"
  for i in $(seq 1 50); do kill -0 "$PID" 2>/dev/null || break; sleep 0.2; done
  "$P/scripts/start.sh"
fi
for i in $(seq 1 30); do
  systemctl is-active --quiet casaos-app-management && break
  sleep 1
done
systemctl is-active casaos-app-management
```

> 不要 kill `run/*.pid`：C-04 之后这些文件可能是旧前缀实例的陈旧 PID。

### 3.3 API 验证

```bash
for i in $(seq 1 60); do
  n=$(curl -s "$B/v2/app_management/apps" | jq '.data.list | length' 2>/dev/null || echo 0)
  [ "$n" = "115" ] && break
  sleep 1
done
echo "api-count=$n" | tee "$EV/a2/api-count.txt"
[ "$n" = "115" ] || { echo "A2 FAIL: expected 115"; exit 1; }

# 保存完整清单
curl -s "$B/v2/app_management/apps" > "$EV/a2/apps-115.json"

# id 集合与 Host A 定义目录一致
curl -s "$B/v2/app_management/apps" | jq -r '.data.list | keys[]' | sort \
  > "$EV/a2/api-ids.txt"
find "$P/appstore/default/Apps" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort \
  > "$EV/a2/fs-ids.txt"
diff -u "$EV/a2/fs-ids.txt" "$EV/a2/api-ids.txt" | tee "$EV/a2/ids.diff"
[ ! -s "$EV/a2/ids.diff" ]

# 分类计数：All=115；非 All 之和=115
curl -s "$B/v2/app_management/categories" > "$EV/a2/categories.json"
jq '[.data[] | select(.name=="All") | .count] | .[0]' "$EV/a2/categories.json"
jq '[.data[] | select(.name!="All") | .count] | add' "$EV/a2/categories.json"
```

预期：

- `api-count=115`；
- `ids.diff` 为空；
- `All.count=115`，非 All 计数之和 115；
- `categories.json` 含 32 个分类定义（其中部分 count=0），UI 只展示有应用的
  11 个分类（Developer/Media/Utilities/Productivity/Networking/Downloaders/
  Cloud/Monitoring/Backup/Home Automation/Security）。

图标抽查/全量：

```bash
curl -s "$B/v2/app_management/apps" | jq -r '.data.list[].icon' | sort -u \
  > "$EV/a2/icons.txt"
while read -r u; do
  code=$(curl -s -L -o /dev/null -w '%{http_code}' --max-time 15 "$u")
  echo "$code $u"
done < "$EV/a2/icons.txt" | tee "$EV/a2/icons.tsv"
awk '$1 !~ /^2/ {print}' "$EV/a2/icons.tsv" | tee "$EV/a2/icons-bad.txt"
[ ! -s "$EV/a2/icons-bad.txt" ]
```

> 图标来自 `selfh.st/icons`，若出现 429/超时，重试 3 次并记录；404 是失败，
> 不能把“有 URL”写成“图标可用”。

### 3.4 浏览器验证（E4，Windows）

打开 `http://192.168.8.8:8081`，用测试账号登录。逐项截图：

1. 商店首页：卡片总数 115；分类导航可见；随机 3 个分类切换后计数正确。
2. 图标：随机 10 张卡片图标实际渲染（不是占位图）。
3. 搜索：搜 `joplin`、`karakeep`、`actual`，结果与定义一致。
4. 详情页：打开 `joplin-server`，确认“龙芯版说明 / 缺失功能 / 额外依赖 / 架构”文本可见。
5. 安装入口：详情页“安装”按钮可打开 compose/配置页；不要求此步真正安装。

证据：

```text
docs/verification/evidence/e0/a2/store-115.png
docs/verification/evidence/e0/a2/store-categories.png
docs/verification/evidence/e0/a2/store-search-joplin.png
docs/verification/evidence/e0/a2/store-detail-joplin.png
```

浏览器 PASS 条件：计数、分类、图标、搜索、详情说明五项都有截图；缺一项即 PARTIAL。

### 3.5 失败分支

#### 3.5.1 重启后仍为 18

按顺序排查，不猜测：

```bash
echo "process:"; ps -o pid,lstart,cmd -p "$(cat "$P/run/app-management.pid")"
echo "apps:"; find "$P/appstore/default/Apps" -name docker-compose.yml | wc -l
echo "config:"; grep -E 'AppStorePath|AppsPath' "$P/conf/app-management.conf"
echo "parse errors:"; grep -c 'failed to parse compose app' "$P/log/app-management.log" || true
grep 'failed to parse compose app' "$P/log/app-management.log" | tail -5
echo "catalog logs:"; grep -E 'No appstore registered|Using default appstore' "$P/log/app-management.log" | tail -5
```

判定：

- `find ... | wc -l` 不是 115：定义未同步；从仓库 `store/casaos/Apps` 重新同步，
  不手工编辑。同步命令：

```bash
# 在仓库根目录（Windows/Git Bash）执行；路径写死，避免本地 $P 未定义
tar -C store/casaos/Apps -cf - . \
  | ssh -o ClearAllForwardings=yes loongson-lab \
      "sudo rm -rf /opt/casaos-p3/appstore/default/Apps.new && sudo mkdir -p /opt/casaos-p3/appstore/default/Apps.new && sudo tar -C /opt/casaos-p3/appstore/default/Apps.new -xf -"

# 在 Host A 上替换（先保留旧目录）
sudo mv /opt/casaos-p3/appstore/default/Apps \
        "/opt/casaos-p3/appstore/default/Apps.bak-$(date +%F-%H%M)"
sudo mv /opt/casaos-p3/appstore/default/Apps.new \
        /opt/casaos-p3/appstore/default/Apps
sudo chown -R root:root /opt/casaos-p3/appstore/default/Apps
```

  替换后重启 app-management，再回到 3.3 复验。不要手工编辑生产 YAML。

- `failed to parse compose app` > 0：记录文件路径和错误；用仓库同名文件
  `sha256sum` 对比，只替换损坏文件；重启后重试。解析失败的应用不能计入 115。
- `No appstore registered` + `Using default appstore` 是**正常回退日志**，不是失败；
  关键看 default 目录内容。
- 进程启动时间早于定义同步时间：再次重启 app-management。
- 仍为 18：C-06 记 BLOCKED，附 `apps` 目录清单、日志、API JSON；不得用 18 冒充 115，
  也不得继续 A5 的商店安装（A3 重启自启仍可独立执行，但 G1 已阻断）。

#### 3.5.2 API 115 但 UI 仍 18

- 浏览器硬刷新/清 Service Worker；换无痕窗口；
- 检查 `apps-115.json` 是否真的 115；
- 若 API 115、UI 18，记 UI 缓存问题，C-06 PARTIAL，附截图与 API JSON；重启 gateway
  不解决问题时不要反复重启，先定位前端缓存。

#### 3.5.3 app-management 起不来

```bash
tail -50 "$P/log/app-management.stdout.log"
ss -lntp | grep 8081
"$P/scripts/healthcheck.sh"
```

若端口被旧进程占用，先 `"$P/scripts/stop.sh"` 再 `"$P/scripts/start.sh"`；
仍失败则 C-06 BLOCKED，附日志；不要删除 `run/` 下的数据库。

### 3.6 A2 验收与证据

| 项 | PASS 条件 | 证据 |
|---|---|---|
| API 计数 | 115 | `$EV/a2/api-count.txt`、`apps-115.json` |
| ID 一致 | `ids.diff` 为空 | `$EV/a2/ids.diff` |
| 分类 | All=115，非 All 和=115 | `$EV/a2/categories.json` |
| 图标 | 无 404/非 2xx | `$EV/a2/icons.tsv`、`icons-bad.txt` |
| UI | 五项截图 | `evidence/e0/a2/*.png` |

把计数、ID diff、分类、图标、浏览器截图汇总到 `docs/verification/reports/C06-STORE.md`；
结论只能是 PASS/PARTIAL/BLOCKED，不能只写“看到 115”。

## 4. A3：C-04 重启与 systemd 自启 — 2026-10-26 已完成（Host A）

### 4.1 重启前记录

```bash
mkdir -p "$EV/a3"
{
  date -Is
  cat /proc/sys/kernel/random/boot_id
  uptime
  systemctl is-enabled casaos.target
  systemctl is-active casaos.target || true
  for u in casaos-gateway casaos-message-bus casaos-user-service \
           casaos-app-management casaos-local-storage casaos; do
    printf '%s is-active=%s is-enabled=%s\n' "$u" \
      "$(systemctl is-active "$u" 2>/dev/null)" \
      "$(systemctl is-enabled "$u" 2>/dev/null)"
  done
  ss -lntp | grep -E ':(8081|40157|34989|35499|35133|43811)\b' || true
  cat "$P"/run/*.url 2>/dev/null || true
  findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS /mnt/Data
  test -d /DATA/AppData && echo /DATA/AppData=present
  curl -s "$B/v2/app_management/apps" | jq '.data.list | length'
  "$P/scripts/healthcheck.sh"
} | tee "$EV/a3/pre-reboot.txt"
```

预期：API 115（A2 已完成）；6 个服务由 systemd 拉起，`casaos.target` 与 6 unit
均 active（2026-10-26 已实测）。若仍看到前缀实例，先按 4.2/4.3 切换。

> 若 A2 已判 BLOCKED，4.1/4.4 的“API 115”改为“记录实际值”；C-04 的自启验证仍可
> 独立执行，但 C-06/G1 已经阻断，不能把 C-04 通过写成 G1 通过。

### 4.2 systemd 预检

```bash
for u in casaos.target casaos-gateway.service casaos-message-bus.service \
         casaos-user-service.service casaos-app-management.service \
         casaos-local-storage.service casaos.service; do
  f=/etc/systemd/system/$u
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done
diff -u "$P/systemd/casaos.target" /etc/systemd/system/casaos.target
for u in casaos-gateway casaos-message-bus casaos-user-service \
         casaos-app-management casaos-local-storage casaos; do
  diff -u "$P/systemd/$u.service" "/etc/systemd/system/$u.service"
done
sudo systemctl daemon-reload
sudo systemd-analyze verify /etc/systemd/system/casaos.target \
  /etc/systemd/system/casaos-*.service
sudo systemctl enable casaos.target
ls -l /etc/systemd/system/multi-user.target.wants/casaos.target
```

预期：diff 为空；`systemd-analyze verify` 退出码 0；target 的 wants 符号链接存在。
服务 unit 可以是 disabled，因为 `casaos.target` 的 `Wants=` 会拉起六个服务；
不要为了“好看”逐个 enable 服务。

### 4.3 切换到 systemd 并重启（已完成；仅复测时重跑）

先停前缀实例，释放 8081，再让 systemd 接管：

```bash
"$P/scripts/stop.sh"
sleep 2
ss -lntp | grep 8081 && { echo "8081 still busy"; exit 1; }
sudo systemctl start casaos.target
sleep 3
for u in casaos-gateway casaos-message-bus casaos-user-service \
         casaos-app-management casaos-local-storage casaos; do
  printf '%s %s\n' "$u" "$(systemctl is-active "$u")"
done
systemctl is-active casaos.target
curl -s "$B/v2/app_management/apps" | jq '.data.list | length'
```

预期：6 个服务 active、target active、API 115、`/ping` pong。若这里失败，先修
systemd 启动，不要直接 reboot；把失败日志写入 `$EV/a3/pre-reboot-systemd.txt`。

然后：

```bash
sync
sudo systemctl reboot
```

> 重启会中断 SSH。这是本规范唯一允许的系统级重启窗口；执行前确认没有其它测试
> 会话占用 Host A。重启后重新连接必须带 `-o ClearAllForwardings=yes`。

### 4.4 重启后验证（已完成，证据见 reports/C04-REBOOT.md）

```bash
for i in $(seq 1 60); do
  ssh -o ClearAllForwardings=yes -o BatchMode=yes -o ConnectTimeout=5 \
    loongson-lab true 2>/dev/null && break
  sleep 5
done

ssh -o ClearAllForwardings=yes -o BatchMode=yes loongson-lab '
  export B=http://127.0.0.1:8081 P=/opt/casaos-p3 EV=/build/verify-evidence/e0
  # 给 systemd 最多 60s 稳定
  for i in $(seq 1 30); do
    n=$(for u in casaos-gateway casaos-message-bus casaos-user-service \
             casaos-app-management casaos-local-storage casaos; do
          systemctl is-active "$u" 2>/dev/null
        done | grep -c "^active$")
    [ "$n" = "6" ] && break
    sleep 2
  done
  {
    date -Is
    cat /proc/sys/kernel/random/boot_id
    uptime
    systemctl is-active casaos.target
    for u in casaos-gateway casaos-message-bus casaos-user-service \
             casaos-app-management casaos-local-storage casaos; do
      printf "%s %s %s\n" "$u" "$(systemctl is-active "$u")" "$(systemctl show -p MainPID --value "$u")"
    done
    ss -lntp | grep -E ":(8081|40157|34989|35499|35133|43811)\b" || true
    findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS /mnt/Data
    test -d /DATA/AppData && echo /DATA/AppData=present
    curl -s "$B/v2/app_management/apps" | jq ".data.list | length"
    "$P/scripts/healthcheck.sh"
  } | tee "$EV/a3/post-reboot.txt"
'
```

验收：

| 检查 | 预期 |
|---|---|
| boot_id | 与 `pre-reboot.txt` 不同 |
| `casaos.target` | `active` |
| 6 个服务 | 全部 `active` |
| 8081 | LISTEN |
| 内部端口 | message-bus/user-service/app-management/local-storage/casaos 各自 LISTEN（端口以 `run/*.url` 为准） |
| `/mnt/Data` | `/dev/sda1 ext4 rw,noatime` |
| `/DATA/AppData` | 存在 |
| API | 115 |
| healthcheck | `/ping` pong；`/`、`/v1/sys/version`、`/v2/app_management/categories` 200 |

> `/DATA` 是根文件系统目录，不是 `/mnt/Data` 的挂载点。此处检查“目录存在”和
> “2TB 挂载仍在”，不要写 `/DATA` 是 2TB 盘。

### 4.5 重启后安装/卸载一个代表性应用（已完成：Gatus 200/卸载释放）

用 `gatus`（单容器、无 sidecar、无宿主写路径、端口 18124）：

```bash
set -a; . /build/verify-secrets/casaos.env; set +a
B=${B:-http://127.0.0.1:8081}
LOGIN=$(jq -n --arg u "$CASAOS_USER" --arg p "$CASAOS_PASSWORD" '{username:$u,password:$p}')
TOK=$(curl -s -X POST "$B/v1/users/login" -H 'Content-Type: application/json' \
  -d "$LOGIN" | jq -r '.data.token.access_token')
[ -n "$TOK" ] && [ "$TOK" != "null" ]

curl -s -H "Authorization: $TOK" -H 'Accept: application/yaml' \
  "$B/v2/app_management/apps/gatus/compose" -o /tmp/gatus.yaml
curl -s -o /tmp/gatus-install.json -w 'install_http=%{http_code}\n' \
  -X POST "$B/v2/app_management/compose?check_port_conflict=true" \
  -H "Authorization: $TOK" -H 'Content-Type: application/yaml' \
  --data-binary @/tmp/gatus.yaml

for i in $(seq 1 60); do
  st=$(curl -s -H "Authorization: $TOK" \
    "$B/v2/app_management/compose/gatus/containers" | jq -r '.. | .State? // empty' | head -1)
  [ "$st" = "running" ] && break
  sleep 2
done
docker ps --filter 'name=gatus' --format '{{.Names}} {{.Status}}'
curl -s -o /dev/null -w 'gatus_http=%{http_code}\n' http://127.0.0.1:18124/

curl -s -o /tmp/gatus-delete.json -w 'delete_http=%{http_code}\n' \
  -X DELETE "$B/v2/app_management/compose/gatus?delete_config_folder=true" \
  -H "Authorization: $TOK"
docker ps -a --filter 'name=gatus' --format '{{.Names}}'
```

预期：install 200、容器 running、18124 200、delete 200、容器消失。
若 `containers` 的 JSON 结构与 `jq` 表达式不匹配，保留原始 JSON 到
`$EV/a3/gatus-containers.json`，用 `docker ps` 作为辅助证据；不要因此判 PASS。

### 4.6 失败回退（恢复，不等于通过）

若重启后 `casaos.target` 或任一服务未 active：

```bash
sudo systemctl stop casaos.target 2>/dev/null || true
sudo pkill -f '/opt/casaos-p3/bin/casaos' 2>/dev/null || true
sleep 2
sudo rm -f "$P"/run/*.pid
"$P/scripts/start.sh"
"$P/scripts/healthcheck.sh"
```

同时保存：

```bash
systemctl status casaos.target --no-pager
for u in casaos-gateway casaos-message-bus casaos-user-service \
         casaos-app-management casaos-local-storage casaos; do
  systemctl status "$u" --no-pager
done
journalctl -u casaos.target -u 'casaos-*' -n 200 --no-pager
```

判定：C-04 **BLOCKED**（自启失败）。`scripts/start.sh` 只能用于恢复服务、继续取证；
不能把“回退后能跑”写成“systemd 自启通过”。若失败原因是 unit 路径/配置，修复后
重跑 4.2–4.4；不能在未复测的情况下改判 PASS。

无论 PASS/BLOCKED，把 `pre-reboot.txt`、`post-reboot.txt`、systemd 状态、gatus
安装/卸载输出汇总到 `docs/verification/reports/C04-REBOOT.md`。

## 5. A5：S-C5 升级/卸载/数据保留（6 类代表应用）

### 5.1 选择

| 类型 | 应用 | 端口 | 数据路径 | 说明 |
|---|---|---|---:|---|
| 单容器 | `linkding` | 18011 | `/DATA/AppData/linkding/config` | SQLite，登录/书签 |
| PostgreSQL | `joplin-server` | 18139 | `/DATA/AppData/joplin-server/{data,postgres}` | sidecar `joplin-postgres` |
| MariaDB | `bookstack` | 18109 | `/DATA/AppData/bookstack/{storage,uploads,mariadb}` | sidecar `bookstack-db` |
| 对象存储 | `minio` | 18153/18500 | `/DATA/AppData/minio/data` | 控制台 + S3 端口 |
| host 网络 | `homeassistant` | 8123（host） | `/DATA/AppData/homeassistant/config` | 不发布端口；先检查 8123 |
| 设备类 | `scrutiny` | 18181 | `/DATA/AppData/scrutiny/config` | 只读 nvme SMART；不碰 `/dev/sda` |

> 设备类不使用 `zigbee2mqtt`（需要 USB 协调器，当前无设备）；`scrutiny` 只读取
> compose 中的 `/dev/nvme0*`，不写 2TB 盘。若 nvme 设备不存在，标 BLOCKED，
> 不要临时把 `/dev/sda` 加进 devices。
>
> `homeassistant` 是 host 网络，安装前先检查：`ss -lntp | grep ':8123'`。若 8123
> 已被占用，改用 `homebridge` 作为 host 网络代表，并在结果 JSON 的 `not_covered`
> 写清替换原因；不能两个都跳过。

### 5.2 通用 API helper

```bash
set -a; . /build/verify-secrets/casaos.env; set +a
B=${B:-http://127.0.0.1:8081}
EV=${EV:-/build/verify-evidence/e0}
LOGIN=$(jq -n --arg u "$CASAOS_USER" --arg p "$CASAOS_PASSWORD" '{username:$u,password:$p}')
TOK=$(curl -s -X POST "$B/v1/users/login" -H 'Content-Type: application/json' \
  -d "$LOGIN" | jq -r '.data.token.access_token')
[ -n "$TOK" ] && [ "$TOK" != "null" ] || { echo "login failed"; exit 1; }

get_compose() {
  curl -sS -H "Authorization: $TOK" -H 'Accept: application/yaml' \
    "$B/v2/app_management/apps/$1/compose" -o "/tmp/$1.yaml"
}
install_app() {
  get_compose "$1"
  curl -sS -o "/tmp/$1.install.json" -w '%{http_code}' \
    -X POST "$B/v2/app_management/compose?check_port_conflict=true" \
    -H "Authorization: $TOK" -H 'Content-Type: application/yaml' \
    --data-binary "@/tmp/$1.yaml"
}
app_status() { # start|restart|stop
  curl -sS -o "/tmp/$1.status.json" -w '%{http_code}' \
    -X PUT "$B/v2/app_management/compose/$1/status" \
    -H "Authorization: $TOK" -H 'Content-Type: application/json' \
    -d "\"$2\""
}
app_health() {
  curl -sS -o /dev/null -w '%{http_code}' \
    -H "Authorization: $TOK" "$B/v2/app_management/compose/$1/healthcheck"
}
app_containers() {
  curl -sS -H "Authorization: $TOK" \
    "$B/v2/app_management/compose/$1/containers" \
    | tee "/tmp/$1.containers.json" | jq '.'
}
uninstall_app() { # $2 = true|false (delete_config_folder)
  curl -sS -o "/tmp/$1.uninstall.json" -w '%{http_code}' \
    -X DELETE "$B/v2/app_management/compose/$1?delete_config_folder=$2" \
    -H "Authorization: $TOK"
}
```

> v1/v2 CasaOS API 使用**裸 token**（`Authorization: $TOK`），不要加 `Bearer`；
> 这是本环境已验证的调用方式。

### 5.3 每应用流程

对每个应用按以下顺序执行，每步写 `results/e0/<id>.json` 的 `checks`：

1. **安装**：`install_app <id>` 预期 200；记录 compose、HTTP 响应。
2. **健康**：轮询 `app_containers` 直到主容器 `running`/`healthy`（最长 180s）；
   `app_health <id>` 预期 200；直接访问端口。
3. **写数据**：按 5.4 的应用动作创建一条可识别数据。
4. **重启持久化**：`app_status <id> restart` 预期 200；等待健康；数据仍在。
5. **升级**：按 5.5；有同 tag 新 digest 才做版本升级，否则明确 NOT TESTED。
6. **卸载保留**：`uninstall_app <id> false` 预期 200；容器消失，数据目录仍在。
7. **重装**：再次 `install_app <id>`；健康后数据仍可见。
8. **清理**：`uninstall_app <id> true`；确认容器/数据清理；只清测试数据。

### 5.4 写数据与验证

| 应用 | 写数据动作 | 验证命令/预期 |
|---|---|---|
| linkding | 打开 `http://127.0.0.1:18011`，注册/登录，新增书签 `CasaOS-Retention-Test` → `https://example.com` | `sqlite3 /DATA/AppData/linkding/config/db.sqlite3 "select count(*) from bookmarks_bookmark;"` 计数增加；若文件名不同，先 `find /DATA/AppData/linkding -name '*.sqlite3'`；重启/重装后仍能搜到该书签 |
| joplin-server | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18139/api/ping` 期望 200；用 `admin@localhost` + compose 中 `DEFAULT_ADMIN_PASSWORD` 登录，创建笔记 `CasaOS-Retention-Test` | `docker exec joplin-postgres psql -U joplin -d joplin -tAc 'select count(*) from notes;'`（表名先用 `\dt` 确认）计数增加；笔记仍在 |
| bookstack | `docker exec bookstack php artisan bookstack:create-admin --email=admin@local --name=Admin --password=<secret>`；登录后创建页面 `CasaOS-Retention-Test` | `docker exec bookstack-db mysql -uroot -pbookstack-root -N -e 'select count(*) from bookstack.pages;'` 计数增加；页面仍在 |
| minio | 打开 `http://127.0.0.1:18153`，用 `admin`/`change-me-12345` 登录；创建 bucket `retention-test`，上传 `marker.txt` | `ls -l /DATA/AppData/minio/data/retention-test` 能看到对象；重启/重装后 bucket 仍在（若镜像无 shell，用宿主机路径验证，不用 `docker exec`） |
| homeassistant | 打开 `http://127.0.0.1:8123` 完成 onboarding；创建一个名为 `CasaOS Retention` 的仪表盘/自动化 | `test -d /DATA/AppData/homeassistant/config/.storage`；`grep -R "CasaOS Retention" /DATA/AppData/homeassistant/config` 有命中（或截图） |
| scrutiny | 打开 `http://127.0.0.1:18181`，确认能看到 nvme 设备与 SMART 健康 | UI 截图；`test -f /DATA/AppData/scrutiny/config/scrutiny.db`；不得出现 `/dev/sda` 写入 |

> 密码/令牌只从 `/build/verify-secrets` 读取；证据中的 `Authorization`、密码、
> 邮箱等必须打码。
>
> linkding/bookstack 若首次没有管理员，按镜像 `BUILD.md` 的 `createsuperuser`/
> `bookstack:create-admin` 方式创建测试管理员；创建命令和账号写入测试卡，
> 不得把测试密码写进仓库。

### 5.5 升级

```bash
mkdir -p "$EV/a5/<id>"
# 记录旧镜像（.Id 一定存在；RepoDigests 可能为空，单独尝试）
docker inspect -f '{{.Image}}' <container> \
  | tee "$EV/a5/<id>/image-before.txt"
docker image inspect -f '{{.Id}}' <image> \
  | tee -a "$EV/a5/<id>/image-before.txt"
docker image inspect -f '{{json .RepoDigests}}' <image> \
  | tee -a "$EV/a5/<id>/image-before.txt" || true

# 只有拿到同 tag 的新 digest/新镜像时才执行
docker pull <image>            # 或 docker load -i <new.tar>
docker image inspect -f '{{.Id}}' <image> \
  | tee "$EV/a5/<id>/image-after.txt"
docker image inspect -f '{{json .RepoDigests}}' <image> \
  | tee -a "$EV/a5/<id>/image-after.txt" || true

# 应用现有 compose（PUT 会按新镜像重建）
curl -sS -o /tmp/<id>.upgrade.json -w '%{http_code}' \
  -X PUT "$B/v2/app_management/compose/<id>?check_port_conflict=true" \
  -H "Authorization: $TOK" -H 'Content-Type: application/yaml' \
  --data-binary "@/tmp/<id>.yaml"

# 若没有新 digest，可用 PATCH 验证幂等重建，但这不算版本升级
curl -sS -o /tmp/<id>.patch.json -w '%{http_code}' \
  -X PATCH "$B/v2/app_management/compose/<id>?force=true" \
  -H "Authorization: $TOK"
```

判定：

- 新镜像 ID/digest 与旧值不同，且数据仍在 → 升级 PASS；
- 只能 `PATCH` 重建、digest 未变 → “重建幂等 PASS，版本升级 NOT TESTED”；
- 不得把“容器重建成功”写成“升级通过”。

> 宿主 Docker Hub 可能优先解析 IPv6 导致 `docker pull` 失败；按 `CASAOS-P3.md`
> 第 11 节的代理/预置方式处理，或使用已 `docker load` 的镜像。不要长期改
> `/etc/hosts`；临时改必须记录并在测试后恢复。

### 5.6 卸载/重装/数据保留判定

```bash
uninstall_app <id> false
test -d "/DATA/AppData/<id>" && echo data-kept || echo DATA-LOST
docker ps -a --filter "label=com.docker.compose.project=<id>" --format '{{.Names}} {{.Status}}'
# 预期：无容器；data-kept

install_app <id>
# 等待健康后再次执行 5.4 的验证命令；数据仍在才算 PASS
```

- `delete_config_folder=false` 后 `/DATA/AppData/<id>` 必须存在；若被删，S-C5
  **BLOCKED**（产品行为与预期不符），附 `uninstall.json` 与目录检查。
- 另用已完成保留测试的 `linkding` 验证默认策略：`uninstall_app linkding true` 后
  `/DATA/AppData/linkding` 应被删除；若未删除，记录实际策略（这是文档项，不是
  6 个代表应用的保留测试）。不要用无卷的 `gatus` 证明数据删除策略。
- 重装后应用自身数据可见（书签/笔记/页面/bucket/仪表盘）才算 PASS；仅目录存在
  不算。

### 5.7 A5 报告

写入 `docs/verification/reports/S-C5-DATA-RETENTION.md`：

| 应用 | 安装 | 写数据 | 重启 | 升级 | 卸载保留 | 重装 | 结论 | 证据 |
|---|---|---|---|---|---|---|---|---|
| linkding | | | | | | | | `evidence/e0/a5/linkding/` |
| joplin-server | | | | | | | | ... |
| bookstack | | | | | | | | ... |
| minio | | | | | | | | ... |
| homeassistant | | | | | | | | ... |
| scrutiny | | | | | | | | ... |

## 6. 平台功能矩阵（CasaOS E0/E1）

> 先执行 5.2 的 `set -a; . /build/verify-secrets/casaos.env; set +a` 与登录 helper，
> 后续表中的 `$TOK`/`$CASAOS_USER` 才有定义。每项执行前先
> `mkdir -p "$EV/platform/<case-id>"`，命令输出用 `tee` 落到该目录；表中的证据列
> 是仓库相对路径，原始大日志另放 `/build/verify-evidence/e0/platform/<case-id>/`。
>
> 应用测试不能替代平台测试。每行必须有“操作、预期、证据”；失败时先修平台，
> 再继续应用矩阵。E1 私人版只对 Linkwarden/Karakeep 使用 `local/*`，其余同 E0。

### 6.1 认证/用户

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| AUTH-01 | `POST /v1/users/login`，body `{"username":"$CASAOS_USER","password":"$CASAOS_PASSWORD"}` | 200，`data.token.access_token` 非空 | `evidence/e0/platform/AUTH-01/` |
| AUTH-02 | `GET /v1/users/current` 不带 token | 401 `token is invalid` | 同上 |
| AUTH-03 | `POST /v1/users/login` 错密码 | 401，无 token | 同上 |
| AUTH-04 | `GET /v1/users/status`：loopback 与 `192.168.8.8:8081` | 已初始化时均 200 `initialized:true`；空库时 LAN 必须 403 | `evidence/e0/platform/AUTH-04/` |
| AUTH-05 | 隔离实例 14500：空 `user.db`，LAN `status/register`，伪造 `X-Forwarded-For`/`X-Real-IP` | 403；loopback 200；初始化后 LAN status 200、register 400 | `evidence/e0/platform/AUTH-05/` |
| AUTH-06 | 隔离实例：`GET /v1/users/current`、`PUT /v1/users/current`、`PUT /v1/users/current/password`、`DELETE /v1/users/:id` | 200/预期错误码；生产库不改 | `evidence/e0/platform/AUTH-06/` |

> 本版本 UserService 没有“管理员创建任意用户”的公开路由；不要把“多用户增删”
> 写成 PASS。生产库只做只读/登录验证；改密、删用户、空库注册都在隔离实例
> 14500–14599 做，测后删除临时前缀。
>
> 隔离实例的可执行搭法：复制前缀到 `/tmp/casaos-us-test`，只保留 bin/www/conf/
> share/scripts，使用空的 `data/db/user.db`；把 `conf/gateway.ini` 的 `Port` 改为
> `14500`，把所有 `RuntimePath` 指到 `/tmp/casaos-us-test/run`；用
> `/tmp/casaos-us-test/scripts/start.sh` 启动。详细命令与 2026-10-25 实测结果见
> `docs/research/casaos-blocker-fix.md` 5.2；若本会话不重建实例，则引用该证据并在
> `results` 标 `PARTIAL`，不能写 PASS。

### 6.2 商店

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| STORE-01 | `GET /v2/app_management/apps` | 200，`data.list` 115 | `evidence/e0/platform/STORE-01/` |
| STORE-02 | `GET /v2/app_management/categories` | All=115；非 All 和=115 | 同上 |
| STORE-03 | 115 个 `icon` URL HEAD/GET | 无 404/非 2xx | `evidence/e0/platform/STORE-03/icons.tsv` |
| STORE-04 | UI 搜索 `joplin`/`karakeep`；详情页 | 结果正确；“龙芯版说明/缺失功能/额外依赖”可见 | `evidence/e0/platform/STORE-04/*.png` |
| STORE-05 | 详情页安装入口/`GET /apps/<id>/compose` | 200，YAML 可解析；不要求此刻安装 | 同上 |

### 6.3 应用管理

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| APP-01 | `bash store/casaos/dryrun_all.sh`（本地仓库，HOST=loongson-lab） | `pass=115 fail=0` | `evidence/e0/platform/APP-01/dryrun.txt` |
| APP-02 | `POST /v2/app_management/compose?dry_run=true` 单个无效 YAML | 4xx，不创建容器 | `evidence/e0/platform/APP-02/` |
| APP-03 | 安装 gatus（4.5 节） | 200，容器 running，18124 200 | `evidence/e0/platform/APP-03/` |
| APP-04 | 同一端口再装一个应用 | 4xx（端口冲突），不产生第二个容器 | 同上 |
| APP-05 | `PUT /compose/gatus/status` body `"restart"`/`"stop"`/`"start"` | 200，状态按预期变化 | `evidence/e0/platform/APP-05/` |
| APP-06 | `GET /compose/gatus/containers`、`/logs?lines=100`、`/healthcheck` | 200，日志有内容，healthcheck 200 | 同上 |
| APP-07 | 安装一个 `depends_on: service_healthy` 的 sidecar 应用（joplin） | sidecar healthy 后才启动主服务；无 unhealthy 循环 | `evidence/e0/platform/APP-07/` |

> `store/casaos/dryrun_all.sh` 内部使用 `ssh "$HOST"`；如果 `~/.ssh/config` 仍有
> `127.0.0.1:18081` 的 LocalForward，脚本会在第一个 ssh 失败。先修正 SSH 配置，
> 或使用下面的等价命令（带 `ClearAllForwardings=yes`）：

```bash
# 本地仓库执行；先同步定义
tar -C store/casaos/Apps -cf - . \
  | ssh -o ClearAllForwardings=yes loongson-lab \
      'rm -rf /tmp/casaos-defs && mkdir -p /tmp/casaos-defs && tar -C /tmp/casaos-defs -xf -'

ssh -o ClearAllForwardings=yes loongson-lab 'BASE=http://127.0.0.1:8081/v2/app_management; REMOTE_DIR=/tmp/casaos-defs; pass=0; fail=0; for f in "$REMOTE_DIR"/*/docker-compose.yml; do id=$(basename "$(dirname "$f")"); code=$(curl -sS -o /tmp/.dry -w "%{http_code}" -X POST "$BASE/compose?dry_run=true&check_port_conflict=true" -H "Content-Type: application/yaml" --data-binary "@$f"); if [ "$code" = 200 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL $id HTTP $code $(head -c 200 /tmp/.dry)"; fi; done; echo "dry-run pass=$pass fail=$fail"; [ "$fail" = 0 ]'
```

> 该命令只调用 `dry_run=true`，证明 compose 能被 CasaOS 解析；**不是安装通过**。
> 必须另行执行 APP-03/APP-07 的真实安装。

### 6.4 本地存储 / 磁盘 / USB / SMART

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| STOR-01 | `GET /v1/disks` 带 token | 200；包含 `/dev/sda`（2TB SATA）与 `/dev/nvme0n1`；USB `/dev/sdb` 不出现 | `evidence/e0/platform/STOR-01/disks.json` |
| STOR-02 | `GET /v1/storage` 带 token | 200；`/mnt/Data` 记录存在；只读检查，不卸载/不写 | 同上 |
| STOR-03 | `GET /v1/disks` 中 sda 的 health/temperature；`smartctl -a /dev/sda` | SMART PASSED；温度/通电时间可读；只读 | `evidence/e0/platform/STOR-03/smart.txt` |
| STOR-04 | `GET /v1/disks/usb`；`udevil info /dev/sdb1` | USB 列表为空（实现过滤 usb）；udevil 识别 removable/iso9660；不挂载/不写 | `evidence/e0/platform/STOR-04/` |
| STOR-05 | `POST/PUT /v1/storage` 指向 `/dev/loop0`（若存在）带 token | 403；无挂载目录、无格式化 | `evidence/e0/platform/STOR-05/` |
| STOR-06 | 格式化的密码门 | 引用 2026-10-25 证据：`/dev/sda1` `format:true` 无/错密码 401，UUID 未变；**本轮不再对 2TB 发 PUT** | `evidence/e0/platform/STOR-06/README.md` |
| STOR-07 | 正向格式化/挂载/卸载 | 无备用空盘，**NOT TESTED**；不得用 `/dev/sda` 或 `/dev/sdb` 代替 | `evidence/e0/platform/STOR-07/NOT-TESTED.md` |

> `local-storage` 只接受 `sata/nvme/sas/spi/virtio/mmc`；USB 被过滤是当前实现。
> 正向格式化测试需要一块可丢弃空盘；在获得之前只能记 NOT TESTED，不能拿历史
> NBD 结果冒充当前代码通过。
>
> STOR-05 若 `/dev/loop0` 不存在，可创建 64M 稀疏文件 fixture：
> `truncate -s 64M /tmp/loopverify.img; sudo losetup /dev/loop0 /tmp/loopverify.img`；
> 测后 `sudo losetup -d /dev/loop0; rm -f /tmp/loopverify.img`。fixture 只写 `/tmp`，
> 不碰真实盘；若系统不允许 loop，则记 NOT TESTED。

### 6.5 文件/共享

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| FILE-01 | UI 文件管理打开 `/DATA`；上传 `verify.txt` 到 `/DATA/verify-tmp/`，下载/改名/删除 | 列表可见；上传/下载/删除成功 | `evidence/e0/platform/FILE-01/*.png` |
| FILE-02 | `GET /v3/file?path=/DATA` 带 token；无 token | 带 token 200；无 token 401 | `evidence/e0/platform/FILE-02/` |
| FILE-03 | `GET /v1/samba/shares`；UI 创建共享 `/DATA/verify-tmp`；`smbclient -L localhost -N` | 接口 200；`smbd` 当前 inactive，若未获授权启动则 PARTIAL，不安装 Samba | `evidence/e0/platform/FILE-03/` |
| FILE-04 | NFS `showmount -e localhost` | 当前未配置则 NOT TESTED；不安装 nfs-kernel-server | 同上 |

> 文件测试只写 `/DATA/verify-tmp`（根文件系统），测后删除；不写 `/mnt/Data`。

### 6.6 系统 / 事件总线

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| SYS-01 | `GET /v1/sys/version` | 200，`current_version=0.4.15` | `evidence/e0/platform/SYS-01/` |
| SYS-02 | UI 仪表盘：CPU/内存/磁盘/网络 | 数值变化合理；无 500/空白 | `evidence/e0/platform/SYS-02/*.png` |
| SYS-03 | UI 设置/通知/日志页 | 可打开；设置持久化（重启后仍在） | 同上 |
| EVT-01 | 安装/卸载 gatus 前后 `grep -c 'failed to publish event' app-management.log` | 增量为 0；无 `message-bus.sock` | `evidence/e0/platform/EVT-01/` |
| EVT-02 | `grep -c 'message-bus.sock' app-management.log`；message-bus 进程/端口 | 0；message-bus 进程在、40157 LISTEN；`/v2/message_bus` 裸访问 400 属正常路由行为 | 同上 |

> 事件总线不再依赖 `/tmp/message-bus.sock`。`/v2/message_bus` 裸访问返回 400
> “no matching operation”是路由行为，不是事件链路失败；以安装/卸载事件日志为准。

### 6.7 安全负向

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| SEC-01 | 静态扫描 115 定义中的 `docker.sock` | 仅 `dozzle/dpanel/portainer/watchtower/woodpecker-agent` 等白名单；无未知应用 | `evidence/e0/platform/SEC-01/` |
| SEC-02 | 静态扫描 `privileged`、`cap_add`、host 网络、`/` 挂载 | 无 privileged；caps 仅 `NET_ADMIN`（easytier/mihomo/wg-easy）、`SYS_RAWIO/SYS_ADMIN`（scrutiny/smartctl-exporter）、`SYS_MODULE`（wg-easy）；host 网络仅 easytier/homeassistant/homebridge/mihomo/pihole；根挂载仅 node-exporter | 同上 |
| SEC-03 | 无 token 访问 `/v1/disks`、`/v1/storage`、`/v1/users/current` | 401 | `evidence/e0/platform/SEC-03/` |
| SEC-04 | 隔离实例空库 LAN 注册/status + 伪造 XFF/X-Real-IP | 403；loopback 才能注册 | `evidence/e0/platform/SEC-04/` |
| SEC-05 | `/dev/loop0` 写操作 | 403；真实盘 UUID 不变 | `evidence/e0/platform/SEC-05/` |

### 6.8 升级/回滚

| ID | 操作 | 预期 | 证据 |
|---|---|---|---|
| UPG-01 | 解包 `casaos-p3-loong64-0.1.3-store115.tar.gz` 到 `/tmp`，`install.sh --prefix /tmp/casaos-p3-upg --store loong64` | 退出码 0；`appstore/default/Apps` 115；不启动服务、不写 `/etc/systemd/system` | `evidence/e0/platform/UPG-01/` |
| UPG-02 | 从 1.2 备份恢复到 `/tmp/casaos-restore`，对比 `conf/`、`data/db/user.db` | 文件存在、hash/内容一致；不覆盖生产前缀 | `evidence/e0/platform/UPG-02/` |
| UPG-03 | 生产 0.1.2→0.1.3 包升级 | **不在本会话**；E5 干净安装/后续发布评审负责 | `NOT-TESTED.md` |

把 6.1–6.8 的每条结果、失败分支、未测原因汇总到
`docs/verification/reports/PLATFORM-CASAOS.md`；平台项失败时应用矩阵暂停，不能
把平台失败改记成“应用问题”。

## 7. 115 应用矩阵

### 7.1 测试卡 schema

以 `PHASE-2-FULL-VERIFICATION.md` 4.1 为准；卡片路径
`docs/verification/cards/<id>.yaml`，至少包含：

- `id/title/image/upstream_version/dependencies/ports/volumes/accounts`；
- `feature_inventory.covered` 与 `feature_inventory.not_covered`；
- `checks[]`：`install`、`http`、`api`、`log`、`restart`、`upgrade`、
  `uninstall_keep_data` 等；
- `manual_preconditions`（25 个 manual 应用必填）；
- `evidence_root` 与 `cleanup`。

卡片生成器/runner 由 `HARNESS-VERSION-EVIDENCE.md` 负责；本规范只定义执行口径，
不复制另一套 schema。

### 7.2 批次清单（按分类/依赖）

固定 115 个，合计 115；批次之间不重试失败项，先定位。

| 批次 | 数量 | 内容 | 并发上限 | 预计人时 |
|---|---:|---|---:|---:|
| B0 | 3 | 数据库/缓存基础层 | 1（独占） | 2 |
| B1 | 40 | 低风险单容器、监控、开发、生产力 | 2 | 10 |
| B2 | 30 | 媒体/下载/网络/云 | 2 | 12 |
| B3 | 20 | 多服务、数据库 sidecar、对象存储 | 1（独占） | 16 |
| B4 | 15 | 设备/安全/网络/manual | 1 | 14 |
| B5 | 7 | 私人 overlay + 复测 | 1 | 8 + 4 |

**B0（3）**：`postgres`, `mariadb`, `redis`

**B1（40）**：
`actual-budget`, `alertmanager`, `apprise-api`, `changedetection`, `code-server`,
`dozzle`, `dpanel`, `firefly-iii`, `freshrss`, `gatus`, `gogs`, `gotify`, `grafana`,
`heimdall`, `hermes`, `homeassistant`, `homebox`, `homebridge`, `it-tools`, `komga`,
`linkding`, `mealie`, `memcached`, `memos`, `mosquitto`, `node-exporter`, `node-red`,
`ntfy`, `pocket-id`, `portainer`, `prometheus`, `readeck`, `registry`, `shiori`,
`uptimekuma`, `vaultwarden`, `vikunja`, `watchtower`, `webvirtcloud`, `wizarr`

**B2（30）**：
`audiobookshelf`, `calibre-web`, `chinesesubfinder`, `drawio`, `excalidraw`,
`jellyfin`, `jellyseerr`, `lanraragi`, `mediamtx`, `mymind`, `navidrome`, `owntone`,
`stirling-pdf`, `tautulli`, `xteve`, `autobrr`, `bazarr`, `jackett`, `metube`,
`prowlarr`, `qbittorrent-ee`, `radarr`, `sabnzbd`, `sonarr`, `caddy`, `dashy`,
`homer`, `nginx-proxy-manager`, `kodexplorer`, `sftpgo`

**B3（20）**：
`paperless-ngx`, `penpot-backend`, `penpot-frontend`, `ente-server`, `ente-web`,
`piwigo`, `homarr`, `jellystat`, `joplin-server`, `miniflux`, `bookstack`, `matomo`,
`nextcloud`, `gitea`, `openwebui`, `nocodb`, `one-api`, `minio`, `filebrowser`,
`syncthing`

**B4（15）**：
`mihomo`, `easytier`, `adguardhome`, `kopia`, `wallabag`, `phpmyadmin`, `pihole`,
`zigbee2mqtt`, `smartctl-exporter`, `go2rtc`, `scrutiny`, `headscale`, `backrest`,
`authelia`, `wg-easy`

**B5（7）**：
`linkwarden`, `karakeep`, `typecho`, `rest-server`, `woodpecker-server`,
`woodpecker-agent`, `unpackerr`

> B5 中的 Linkwarden/Karakeep 先在 E0 用公开定义执行；E1 私人版另用
> `store/casaos-private/Apps/` 下的两个定义 + `local/*` 镜像，单独出证据。
> 私人版不计入 115 的公开计数，但必须验证无公开镜像替代、无 LBrowser 宿主挂载。

每批结束立即写 `docs/verification/reports/BATCH-<Bn>.md`，列出 PASS/PARTIAL/BLOCKED/
NOT TESTED 计数、失败证据、未测原因；不要等全部 115 跑完再补。

### 7.3 并发与资源

- 全局同时最多 2 个应用；`B0`、`B3` 的数据库/多服务应用独占，不能与其它应用并发。
- `B1` 中 `homeassistant`/`homebridge`（host 网络）、`portainer`/`dozzle`/`dpanel`/
  `watchtower`（docker.sock）、`webvirtcloud` 必须串行，不与其它 host 网络/
  docker.sock 应用同时跑。
- `B2` 的媒体转码/下载器最多 2 个，先跑一个再做下一个；不要同时拉多个大镜像。
- `B4` 全部串行；host 网络应用先查端口冲突。
- `B5` 串行；私人与公开变体分开，不混用镜像。

### 7.4 单应用流程（每个应用都按此执行）

```text
预检（卡片/端口/镜像/磁盘）
→ 安装（POST compose）
→ 健康（containers running/healthy + healthcheck 200 + 端口 HTTP）
→ 首启/认证（卡片 accounts）
→ 功能清单 ≥3 项（API/UI）
→ 写数据
→ 重启持久化（PUT status restart）
→ 升级（有同 tag 新 digest 才做）
→ 卸载保留（DELETE delete_config_folder=false）
→ 重装 → 数据仍在
→ 清理（DELETE true + 测试目录）
```

每一步都写 `results/e0/<id>.json`；失败立即停止该应用，保存日志/容器状态，
不继续“猜”。安装失败不能跨批重试；先定位镜像/端口/依赖。

### 7.5 25 个 manual 应用前置条件

`store/istore/data/build-manifest.json` 中 `automation=manual` 的 25 个应用。
每个都必须写“前置条件、可自动验证部分、必须人工/设备部分、未测原因”。

| 应用 | 前置条件 | 可自动验证 | 必须人工/设备 |
|---|---|---|---|
| mihomo | `/DATA/AppData/mihomo/config` 有可用 config.yaml；host 网络；宿主已有 mihomo 容器/TUN 时不要并发 | 安装、容器启动、配置目录存在 | 配置代理规则、验证出站 |
| easytier | `/DATA/AppData/easytier/config/network.toml`；host 网络 | 安装、容器启动 | 组网对端、路由验证 |
| adguardhome | 宿主 53 未被 dnsmasq/systemd-resolved 占用；host 网络 | 安装、UI 302/200 | 首次向导、DNS 查询 |
| pihole | 宿主 53 空闲；host 网络 | 安装、容器启动 | Web 密码、DNS 查询 |
| wg-easy | `INIT_HOST` 改为客户端可达地址；UDP 51820 | 安装、UI 302、端口监听 | VPN 客户端握手 |
| kopia | Web UI 创建仓库 + Basic 认证 | 安装、UI 200 | 创建仓库、快照/恢复 |
| backrest | Web UI 创建账号/仓库 | 安装、UI 200 | 仓库配置、备份任务 |
| typecho | Web 安装向导；默认 SQLite 可用 | 安装、安装页 200 | 填写站点/管理员 |
| wallabag | 首次安装需镜像内 CLI 或文档创建管理员 | 安装、容器启动 | CLI 创建管理员、登录 |
| phpmyadmin | 外部 MySQL/MariaDB 地址/用户 | 安装、登录页 200 | 连接外部数据库 |
| rest-server | 首次运行 `create_user` 创建用户 | 安装、容器启动 | 创建用户、上传/恢复 |
| bookstack | `bookstack:create-admin` 创建管理员 | 安装、sidecar healthy、`/login` 200 | 创建页面、权限 |
| matomo | Web 安装向导；`matomo-db` 用户/密码 | 安装、sidecar healthy、安装页 200 | 完成安装、报表 |
| ente-server | MinIO 中创建 `b2-eu-cen` bucket（mc） | 安装、sidecar healthy、API 200 | bucket/密钥、客户端登录 |
| ente-web | `ENTE_API_ORIGIN` 指向 ente-server 可达地址 | 安装、页面 200 | 客户端登录/上传 |
| woodpecker-server | Gitea URL/Client/Secret 写入 env 文件 | 安装、UI 200 | OAuth 登录、流水线 |
| woodpecker-agent | 从 server 的 `/var/lib/woodpecker/agent-secret` 取 secret | 安装、容器启动 | agent 注册、任务执行 |
| headscale | `HEADSCALE_SERVER_URL` 改为客户端可达 HTTPS | 安装、容器启动 | 节点注册、DNS/TLS |
| authelia | OIDC 提供方 + HTTPS；cookie domain 不是 localhost | 安装、登录页 302 | OIDC 流程、2FA |
| go2rtc | Web 配置摄像头流 | 安装、UI 200 | 摄像头/流验证 |
| mediamtx | `mediamtx.yml` 配置流 | 安装、容器启动 | 推流/拉流 |
| scrutiny | 真实磁盘设备（compose 内 nvme）；只读 SMART | 安装、UI 200、设备健康 | 磁盘故障注入（不做） |
| smartctl-exporter | 真实磁盘设备 `/dev/sdX`；只读 | 安装、metrics 200 | Prometheus 抓取/告警 |
| zigbee2mqtt | USB 协调器 `/dev/serial/by-id/...` | 安装、UI 200（有设备时） | 配对设备 |
| unpackerr | Sonarr/Radarr URL + API key | 安装、容器启动 | 下载完成回调验证 |

判定：前置满足则跑“可自动验证”；人工/设备部分未做写 PARTIAL；前置不满足写
BLOCKED/NOT TESTED，附 `ss`/`ls`/env 检查证据。不能因为“manual”跳过整张卡。

### 7.6 清理与磁盘阈值

每个应用/批次前后：

```bash
df -h /DATA /build /var
docker system df
docker ps -a --format '{{.Names}} {{.Status}}' | head -30
```

阈值：

| 路径 | 开始批次最低 | 暂停阈值 | 处理 |
|---|---:|---:|---|
| `/DATA`（根 FS） | 5GB | 2GB | 清理测试容器/数据；不删用户数据 |
| `/build` | 2GB | 2GB | 清理 `verify-data` 临时文件；原始证据转 `/mnt/Data` 需用户批准 |
| `/var` | 2GB | 2GB | 清理测试镜像/停止容器；**不得** `docker system prune -a` 删除共享镜像 |

清理规则：

- 只删除本应用/本批次的容器、compose 项目、`/DATA/AppData/<id>` 测试数据；
- 不删除 `yunixintel/*:24.10-la5`、`local/*`、`node`/`node-sharp`/`lbrowser-runtime`
  等共享镜像；需要删时先 `docker image inspect` 确认无其它容器使用；
- 测试脚本/结果放 `/build/verify-data`；大日志放 `/build/verify-evidence`；
- 低于阈值时暂停批次，写 `state` 的 `blockers`，不要“边删边猜”。

### 7.7 全量口径

每个应用至少覆盖：安装、健康、首启/认证、3 个核心功能、持久化、重启、升级
（有 digest 时）、卸载/数据保留、已知限制负向检查。UI 类至少 2 张截图（登录后
首页 + 核心页）；API 类至少 3 个端点；集成类至少 1 条真实集成路径。
`not_covered` 必须写明原因，最终报告汇总。未测项不能默认 PASS。

## 8. 证据、结果、报告、state

### 8.1 路径

```text
docs/verification/
  cards/<app>.yaml
  results/e0/<app>.json
  results/e0/batches/B0..B5.json
  evidence/e0/a1/...
  evidence/e0/a2/...
  evidence/e0/a3/...
  evidence/e0/a5/<app>/...
  evidence/e0/platform/<case-id>/...
  evidence/e0/batches/<batch>/<app>/...
  reports/C03-SOAK.md
  reports/C04-REBOOT.md
  reports/C06-STORE.md
  reports/S-C5-DATA-RETENTION.md
  reports/PLATFORM-CASAOS.md
  reports/BATCH-B0.md ... BATCH-B5.md
  reports/CASAOS-GATE-FINAL.md
verify/state/casaos-gate-exec.yaml
```

原始大日志：`/build/verify-evidence/e0/...`；仓库内单文件建议 <2MB，截图用压缩
PNG/JPG；每个原始文件在结果 JSON 中写 `sha256` 和路径。

### 8.2 结果 JSON

```json
{
  "app": "joplin-server",
  "env": "e0",
  "batch": "B3",
  "image": "yunixintel/joplin-server:24.10-la5",
  "verdict": "PASS",
  "checks": [
    {"id": "install", "status": "PASS", "evidence": ["evidence/e0/batches/B3/joplin-server/install.json"]},
    {"id": "ping", "status": "PASS", "evidence": ["evidence/e0/batches/B3/joplin-server/ping.txt"]}
  ],
  "not_covered": ["OIDC 未接真实提供方"],
  "evidence_root": "evidence/e0/batches/B3/joplin-server/",
  "finished_at": "2026-10-27T12:00:00+08:00"
}
```

`verdict` 只能是 `PASS/PARTIAL/BLOCKED/NOT_TESTED`；`checks[].status` 用同一套词。

### 8.3 state YAML 格式

`verify/state/casaos-gate-exec.yaml`：

```yaml
session: casaos-gate-exec
plan: docs/verification/PHASE-2-FULL-VERIFICATION.md
spec: docs/verification/specs/CASAOS-EXECUTION.md
started_at: "2026-10-26T22:00:00+08:00"
updated_at: "2026-10-26T22:00:00+08:00"
phase: A
batch: A1
status: in_progress        # in_progress|blocked|done
last_completed: null
current: C-03
backup:
  path: /build/backup-casaos-p3-<date>.tar.gz
  sha256: <sha256>
soak:
  csv: /tmp/casaos-soak-24h.csv
  sha256: <sha256>
  rows: 8640
  verdict: PASS
disk:
  data_free_gb: 13
  build_free_gb: 4.8
  var_free_gb: 4.5
counts:
  apps_total: 115
  apps_pass: 0
  apps_partial: 0
  apps_blocked: 0
  apps_not_tested: 0
blockers: []              # {id,severity,evidence,next}
retest: []
next:
  - A2
notes: "VERSION 文件 0.1.0-p3 与运行基线 0.1.2 不一致，已记录"
```

每完成一项/批次更新 `updated_at`、`last_completed`、`current`、`counts`；遇到阻塞写
`status: blocked` 和 `blockers`，不要只写在聊天里。

### 8.4 失败分级

| 级别 | 条件 | 处理 |
|---|---|---|
| S0 闸门 | C-03/C-04/C-06/S-C5 任一核心项失败 | G1 BLOCKED，停止发布；先修再复测 |
| S1 安全 | 白名单/密码门/首管理员/未授权访问负向测试失败 | 停止应用矩阵；安全修复前不继续 |
| S2 应用阻塞 | 安装/健康/依赖失败 | 停止该应用，记 BLOCKED；不跨批重试 |
| S3 功能缺口 | 应用可运行但部分功能失败/未覆盖 | 记 PARTIAL，列 `not_covered` |
| S4 环境/人工 | 无设备/外部服务/无备用盘 | 记 NOT TESTED/BLOCKED，附前置证据 |

任何 PASS 都需要“命令输出/HTTP 状态/截图 + 证据路径”；只有描述没有证据，按
NOT TESTED 处理。

### 8.5 预计工时

| 项 | 人时 |
|---|---:|
| A0 前置 + 备份 | 1 |
| A1 C-03 分析/报告 | 2 |
| A2 商店 115（API + 浏览器） | 3 |
| A3 C-04 重启/自启 | 2 |
| A5 S-C5 六类应用 | 7 |
| 平台功能矩阵 | 10 |
| B0 | 2 |
| B1 | 10 |
| B2 | 12 |
| B3 | 16 |
| B4 | 14 |
| B5 公开 | 8 |
| B5 私人 overlay | 4 |
| 报告/汇总/复测 | 4 |
| **合计** | **约 95 人时** |

按每日 10 小时、并发 2 个应用，日历约 6–7 个工作日；25 个 manual 应用的外部
依赖、USB/设备可用性可能延长。失败项按“阻塞证据”处理，不无限重试。

## 9. 明确不包含

1. **B 机 `/dev/sdb` 干净安装（E5）**：等龙芯 NAS 项目完成后再做；本规范不碰
   `172.16.100.66`、不碰 `/dev/sdb`/`rpool`，也不碰 B 机 sda。
2. **iStore USB/la5/p1 真机**：保存 ISO、写 58G U 盘、feed、opkg/LuCI 由
   `ISTORE-EXECUTION.md` 负责；本规范只做 CasaOS。
3. **OMV O-01~O-03**：由 OMV 子代理/规范负责；本规范不用 QEMU 做 OMV。
4. **2TB `/dev/sda` 格式化/写测试**：任何情况下不做；正向格式化测试无空盘时
   记 NOT TESTED。
5. **生产密码/用户变更**：生产库只登录/只读；改密/删用户在隔离实例做。
6. **应用镜像重建/商店重设计/私人 feed 发布**：不在本规范；B5 私人 overlay 只用
   现有 `local/*` 镜像。
7. **生产 0.1.3 包升级**：本会话只做临时前缀安装/回滚验证；生产升级由发布评审
   单独批准。

## 10. 快速执行清单

1. `ssh -o ClearAllForwardings=yes loongson-lab`；确认 Host A/6 服务/115 定义。
2. 备份 `/opt/casaos-p3` 与 systemd units，记 sha256。
3. C-03：冻结 CSV，跑 2.2 统计，按 2.3 判 PASS/BLOCKED，写 `C03-SOAK.md`。
4. A2：重启 app-management，API 115、ID diff 空、分类和 115、图标无 404。
5. 浏览器验证分类/图标/搜索/详情/龙芯版说明。
6. A3：记录 pre、停前缀、`systemctl start casaos.target`、reboot、post 检查 6 服务/
   端口/挂载/115，安装卸载 gatus；失败回退并判 BLOCKED。
7. A5：6 类应用安装→写数据→重启→升级→卸载保留→重装→数据仍在；升级无 digest
   时明确 NOT TESTED。
8. 平台矩阵：按第 6 节逐项；安全负向优先，存储正向格式化无空盘记 NOT TESTED。
9. 115 矩阵：B0→B5，按第 7 节批次与并发；每应用写结果 JSON；每批写报告。
10. 汇总 `CASAOS-GATE-FINAL.md`，更新 state、计划、CASAOS-P3、research 文档；
    只提交摘要证据，不提交凭据/大日志。

## 附录 A：常用 API 速查

| 用途 | 方法与路径 |
|---|---|
| 登录 | `POST /v1/users/login` |
| 当前用户 | `GET /v1/users/current` |
| 商店列表 | `GET /v2/app_management/apps`（`data.list` 是对象） |
| 商店分类 | `GET /v2/app_management/categories` |
| 应用 compose | `GET /v2/app_management/apps/<id>/compose`（`Accept: application/yaml`） |
| dry-run | `POST /v2/app_management/compose?dry_run=true&check_port_conflict=true` |
| 安装 | `POST /v2/app_management/compose?check_port_conflict=true`（body YAML） |
| 已装列表 | `GET /v2/app_management/compose` |
| 已装 compose | `GET /v2/app_management/compose/<id>` |
| 改配置/升级 | `PUT /v2/app_management/compose/<id>?check_port_conflict=true` |
| 更新镜像 | `PATCH /v2/app_management/compose/<id>?force=true` |
| 启动/停止/重启 | `PUT /v2/app_management/compose/<id>/status`，body `"start"`/`"stop"`/`"restart"` |
| 容器 | `GET /v2/app_management/compose/<id>/containers` |
| 日志 | `GET /v2/app_management/compose/<id>/logs?lines=200` |
| 健康 | `GET /v2/app_management/compose/<id>/healthcheck` |
| 卸载 | `DELETE /v2/app_management/compose/<id>?delete_config_folder=false` |
| 磁盘 | `GET /v1/disks` |
| 存储 | `GET/POST/PUT/DELETE /v1/storage` |
| USB | `GET /v1/disks/usb`、`GET/PUT /v1/usb/usb-auto-mount` |
| 文件 | `GET /v3/file?path=/DATA`（带 token） |
| 共享 | `GET /v1/samba/shares` |
| 系统版本 | `GET /v1/sys/version` |

## 附录 B：本规范编写时实测锚点

```text
Host A: yunix-pc, Loongnix 25, 6.6.52-loong64, systemd 257, Docker 26.1.5+dfsg1
Install: /opt/casaos-p3, gateway :8081, VERSION=0.1.2-appmgr410-p3+store115
6 services (post-C-04 systemd): gateway 1768, message-bus 1771, user-service 1786,
  local-storage 1781, app-management 1780, casaos 1796
AppStore: default/Apps=115, loong64/Apps=115; API post-A2=115
Soak: 8640 rows, 1440/service, first 2026-10-25T21:06:37+08:00,
  last 2026-10-26T21:08:40+08:00, max gap 63s
HTTP: gateway/message-bus/user-service/app-management/casaos=200×1440;
  local-storage=401×1440
RSS peak (KB): gateway 21360, message-bus 38976, user-service 27168,
  app-management 73456, local-storage 67616, casaos 38848
Disk: /DATA 13G free (root FS), /build 4.8G free, /var 4.5G free,
  /mnt/Data 1.9T free (2TB SATA, read-only)
Devices: /dev/sda 1.9T SATA ext4 /mnt/Data; /dev/sdb 58.2G USB iso9660 (LOONGSONISO)
Platform: smbd inactive; rclone missing; jq/python3/sqlite3/smartctl/smbclient present
```
