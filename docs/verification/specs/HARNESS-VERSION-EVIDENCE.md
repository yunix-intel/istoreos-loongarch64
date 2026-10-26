# HARNESS-VERSION-EVIDENCE — 测试 harness、版本矩阵与证据规范

版本：1.0（骨架，可直接实现）
日期：2026-10-26
状态：已由主会话逐行审查（2026-10-26）；审查通过，示例不构成实测结果
入口：[PHASE-2-FULL-VERIFICATION](../PHASE-2-FULL-VERIFICATION.md)
适用会话：`casaos-gate-exec`、`istore-la5-exec`、`istore-p1-exec`、`casaos-clean-exec`
范围：版本矩阵、115 卡 schema/生成、runner、证据/结果/报告/state、质量门槛。
非范围：本文不执行安装/重启，不写死任何“实测值”；示例卡不构成测试结果。

## 0. 总则

1. 三张事实表必须分开：**预期基线**（计划/文档）、**实测值**（命令输出）、**判定**（PASS/PARTIAL/BLOCKED/NOT TESTED）。禁止把预期抄进实测。
2. 每个结论必须能回答：“哪个环境、哪条命令、什么输出、证据文件在哪、哈希是多少”。
3. 任何检查级 `FAIL` 都不得让卡片 PASS。失败按 `failure_class` 分类：`env|dependency|product|harness|known_limit`；产品缺陷也按 BLOCKED 记录并附复现，修复后复测。
4. 未执行 = `NOT TESTED`，不是 PASS；dry-run = `NOT TESTED`；只打开首页 = 至多 `PARTIAL`。
5. 版本矩阵前置闸门不过，相关环境的卡片只能出 PARTIAL/BLOCKED，不能出 PASS。

## 1. 版本矩阵规范

### 1.1 层与字段

| 层 | 环境 | 必填字段 | 采集命令模板 | 预期基线（非实测） |
|---|---|---|---|---|
| 固件 la5 | E2 | image_file、image_sha256、openwrt_release、version.buildinfo、kernel、page_size、docker/containerd/runc、podman | `sha256sum <img.gz>`；`ssh $H 'cat /etc/openwrt_release; cat /etc/version.buildinfo 2>/dev/null || cat /etc/istoreos_release; uname -a; getconf PAGESIZE; docker version --format "{{json .}}"; containerd --version; runc --version; podman version --format json 2>/dev/null'` | iStoreOS `24.10-la5`，基线 `24.10.8 r0-fb97140` |
| 固件 p1 | E3 | 同上 + private_preset_sha256 | 同上；另 `sha256sum /build/firmware/personal-p1-20261019.img.gz` | `personal-p1-20261019`，同基线 + 私人预置；镜像 381MB |
| Host A | E0/E1/E5 | os_release、kernel、page_size、glibc、systemd、cpu、mem、docker_api、storage_driver | `cat /etc/os-release; uname -a; getconf PAGESIZE; ldd --version | head -1; systemctl --version | head -1; lscpu; free -b; docker version --format "{{json .}}"; docker info --format "{{json .}}"` | Loongnix 25，kernel `6.6.52-loong64`，页大小 `16384` |
| CasaOS 9 组件 | E0/E1 | 组件名、版本、二进制 SHA256、unit、健康端口 | `cat /opt/casaos-p3/VERSION`；`jq -r '.components[]? | [.name,.version,.sha256] | @tsv' /opt/casaos-p3/VERSION`（非 JSON 时用 `grep`）；`sha256sum <binary>`；`systemctl list-units 'casaos*'` | casaos `v0.4.15`、gateway `v0.4.9-alpha4`、message-bus `v0.4.4-3-alpha2`、user-service `v0.4.8`、app-management `v0.4.10-alpha2`、local-storage `v0.4.4`、CLI `v0.4.4-3-alpha1`、UI `v0.4.25`、AppStore `v0.4.5` |
| CasaOS 包 | E0/E1/E5 | package、sha256、安装方式、干净安装标记 | `sha256sum casaos-p3-loong64-0.1.3-store115.tar.gz` | `0.1.3-store115`，sha256 前缀 `7262d39c…50426`；回退 `0.1.2-appmgr410` |
| 容器运行时 | E0/E1/E2/E3 | docker、api、containerd、runc、podman、crun、conmon、netavark、cgroup、storage driver | 同固件/Host A 模板 | Host A：Docker `26.1.5+dfsg1`、API `1.45`、containerd `1.7.24`、runc `1.1.15`；iStore 以实测为准 |
| 115 应用镜像 | E0/E1/E2/E3 | repo、tag、RepoDigest、os/arch、size、label version、created、source | `docker image inspect <ref> --format '{{json .RepoDigests}} {{.Os}}/{{.Architecture}} {{.Size}} {{json .Config.Labels}}'`；`crane config <ref>`；`docker manifest inspect <ref>` | 每个 `yunixintel/<id>:24.10-la5`，`linux/loong64` |
| 3 基础层 | 全部 | 同上 | 同上 | `node:24.22.1`（legacy `22.23.3` 允许但非主）、`node-sharp:24.22.1`、`lbrowser-runtime:3.4.2293.2` |
| sidecar 7 镜像 | E0-E3 | 镜像、tag、健康命令、UID/GID、数据路径、preload | 同上 + `docker inspect --format '{{json .Config.Healthcheck}}'` | postgres `15.18`、mariadb `10.11.18`、redis `7.2.14`、minio `RELEASE.2025-10-15T17-29-55Z`、lbrowser `3.4.2293.2`、node-sharp `24.22.1`、node `24.22.1` |
| 商店集合 | E0-E3 | CasaOS 定义 115、iStore app-meta 115+1、feed SHA256 | `python -I store/casaos/validate_definitions.py`；`python -I store/istore/validate.py`；`sha256sum feed/*/all/*/Packages*` | 四处集合完全一致：catalog 115 应用 + 3 基础层、descriptions 115、CasaOS Apps 115、iStore app-meta 115 |

**强制例外（写死，不得当 drift）**：`yunixintel/lbrowser-runtime` 只有 `linux/loong64` / `3.4.2293.2`，没有 `24.10-la5`；`yunixintel/node-sharp` 只有 `linux/loong64` / `24.22.1`。引用这两个镜像的卡片必须按实际 tag 检查，不得要求 `24.10-la5`。CasaOS compose 的 `postgres`/`mariadb` 允许 `:loong64`；iStore sidecar 模板要求 `:24.10-la5`。`local/*` 只允许 E1/E3，E0/E2 出现即红线。

### 1.2 VERSION-MATRIX.json 记录格式

```json
{"schema":1,"env":"E0","layer":"image","component":"joplin-server",
 "field":"RepoDigest","expected":"sha256:<expected-or-null>","expected_source":"BUILDLOG/catalog",
 "actual":"sha256:<from docker image inspect>","actual_source":"docker image inspect ...",
 "collected_at":"<UTC>","collector":"collect_versions.sh","drift":"D0|D1|D2|D3|D4|D5",
 "severity":"info|warn|block","note":""}
```

`VERSION-MATRIX.md` 由 JSON 渲染，必须含：预期值、实际值、差异级别、证据路径、结论。原始命令输出放 `docs/verification/evidence/<env>/versions/`；大文件放 `/build/verify-evidence/<run-id>/versions/`。

### 1.3 drift 规则

| 级别 | 含义 | 处理 |
|---|---|---|
| D0 | 完全一致 | 通过 |
| D1 | 仅格式差异（`v` 前缀、显示空白） | 归一化后一致；禁止归一化数字/构建号 |
| D2 | 命中白名单例外（1.1 强制例外） | 记录，不阻塞 |
| D3 | 实质不一致（tag、digest、arch、版本、页大小、集合数量） | 阻塞该环境；卡片最高 PARTIAL/BLOCKED |
| D4 | 缺失/无法采集（镜像不存在、命令失败） | 阻塞；附错误原文，不得用替代 tag |
| D5 | 预期文档过期（重新推送后） | 先回写 BUILDLOG/catalog，再复跑；旧结果作废 |

- 固件：la5/p1 的 `version.buildinfo` 必须记录；p1 必须证明“同基线 + 私人预置”，出现公开镜像/凭据即 D3。
- 镜像 digest 与 catalog/BUILDLOG 不一致时，以 `docker image inspect` 为准；有重新推送证据则 D5，否则 D3。
- 应用集合必须严格 115；多一个/少一个都是 D3。基础层不计入 115。
- 页大小不是 `16384`（Host A）为 D3；iStore 记录实测值，不套用 Host A。
- 同一组件的版本字符串按“去 `v` 前缀”归一化；`+dfsg1`、`-alpha2` 等后缀必须保留。

### 1.4 前置闸门

`verify/phase2/preflight.py --env E0` 必须依次通过：版本采集完整 -> 集合 115 一致 -> 镜像 arch/os/tag 正确 -> 必需 sidecar 可解析 -> 端口计划无冲突 -> 证据目录可写。任一 D3/D4 时返回非零，runner 不得把任何卡片标 PASS。

## 2. 115 张测试卡 schema

文件：`docs/verification/cards/<id>.yaml`，与 115 个 app id 一一对应。卡片是**可执行清单**，不是描述文档。

### 2.1 必填字段

`schema`、`id`、`title`、`category`、`environment`、`image`（public/private/arch/tag_exception）、`upstream_version`、`dependencies`、`ports`、`volumes`、`accounts`、`preconditions`、`feature_inventory`、`checks`、`evidence`、`timeouts`、`cleanup`、`owner`。
`feature_inventory` 必须同时有 `covered[]` 与 `not_covered[]`；`not_covered` 不能省略，空时必须写 `coverage_complete: true` 和理由。

### 2.2 checks 原语

| type | 关键字段 | 断言 | 证据 |
|---|---|---|---|
| `install` | adapter、expect（running/healthy）、sidecars | 容器/应用 + sidecar 健康，镜像 digest 与矩阵一致 | 安装日志、`docker ps/inspect`、镜像 digest |
| `http` | method、path、port、headers、body、expect_status、expect_body/json_path、follow_redirects | 状态码 + 响应内容 | request/response headers、body、sha256 |
| `tcp` | host、port、proto、expect_open | 端口可连 | `ss`/连接结果 |
| `docker_exec` | container、argv、expect_exit、stdout_contains/regex、stderr_not_contains | 退出码 + 输出 | 命令、stdout/stderr、容器 id |
| `sql` | engine、container、query、expect_rows/value、readonly | 查询结果 | 查询文本（脱敏）、结果、引擎版本 |
| `browser` | url、actions、assert（title/selector/text）、screenshot | UI 行为 | 截图 + 页面标题/URL/UA |
| `restart` | target（app/container/host）、wait、then[] | 重启后复跑指定 check + 数据仍在 | 重启前后状态、then 证据 |
| `upgrade` | strategy（same-tag rebuild/new digest）、then[] | 升级成功、数据保留、版本端点 | 新旧 digest、数据校验 |
| `uninstall` | mode（rm/purge）、expect（data_dir_exists/data_dir_absent） | 数据保留策略符合预期 | 卸载前后目录、卷 |
| `log` | container、since、tail、expect_contains/expect_not_contains/regex | 日志断言 | 日志摘录 + 完整日志路径 |
| `manual` | steps、operator、evidence、if_unmet | 人工步骤完成 | 截图/录像 + 操作者 + 时间 |

负向检查必须显式 `polarity: negative`，例如期望 500/403/非零退出；不得把失败写成成功。每个 check 必须有 `evidence_required`。

### 2.3 示例卡 A：Joplin Server（自动 + PostgreSQL sidecar + 已知限制）

> 示例用于说明 schema 与检查原语，不是 runner 可直接执行的最终脚本。Joplin 的
> `/api/items/...`、`/api/shares` 路径和 share_id 需按实际 API 改写；BookStack 的
> `POST /books`/`/pages`/`/images` 受 CSRF/session 保护，必须用 browser 或先取
> token，不能把示例里的裸 POST 当可执行命令。

```yaml
schema: 2
id: joplin-server
title: Joplin Server
category: Utilities
environment: [E0, E1, E2, E3]
image:
  public: yunixintel/joplin-server:24.10-la5
  private: null
  arch: linux/loong64
  tag_exception: false
upstream_version: 3.7.21
dependencies:
  sidecars: [postgres]
  apps: []
  devices: []
  host_features: []
ports:
  - {name: http, container: 22300, host: 18139, proto: tcp, primary: true}
volumes:
  - {name: data, container: /data, host_casaos: /DATA/AppData/joplin-server/data, host_istore: /srv/joplin-server/data, mode: rw, primary: true}
accounts:
  admin: {user: admin@localhost, secret_ref: joplin_admin, create: installer_or_first_login}
preconditions:
  automation: auto
  manual: []
  required_env: [APP_BASE_URL]
  preload: []
feature_inventory:
  covered:
    - {id: health, source: upstream-api, checks: [ping]}
    - {id: login, source: upstream-api, checks: [admin_login]}
    - {id: notes, source: upstream-api, checks: [create_note, read_note]}
    - {id: share, source: upstream-api, checks: [share_create, share_get]}
    - {id: persistence, source: plan, checks: [restart_persistence]}
    - {id: lifecycle, source: plan, checks: [upgrade_keep_data, uninstall_keep_data]}
  not_covered:
    - {id: desktop_sync, reason: 无桌面客户端，未验证双端同步}
    - {id: ldap_saml_stripe_email, reason: 未配置外部服务}
  coverage_complete: false
checks:
  - {id: install, type: install, adapter: auto, expect: healthy, evidence_required: [install_log, docker_ps, sidecar_status]}
  - {id: ping, type: http, method: GET, path: /api/ping, port: 22300, expect_status: 200, expect_json: {status: ok}, evidence_required: [http]}
  - id: admin_login
    type: http
    method: POST
    path: /api/login
    port: 22300
    body: {email: admin@localhost, password: "${secret:joplin_admin}"}
    expect_status: 200
    evidence_required: [http]
  - {id: create_note, type: http, method: POST, path: /api/items/root:/notes/demo.md, body: {body: "phase2"}, expect_status: 200, evidence_required: [http]}
  - {id: read_note, type: http, method: GET, path: /api/items/root:/notes/demo.md, expect_status: 200, evidence_required: [http]}
  - {id: share_create, type: http, method: POST, path: /api/shares, body: {type: 1}, expect_status: 200, evidence_required: [http]}
  - {id: share_get, type: http, method: GET, path: /shares/{share_id}, expect_status: 200, evidence_required: [http, screenshot]}
  - {id: restart_persistence, type: restart, target: app, wait: 30, then: [ping, admin_login, read_note], evidence_required: [restart_log, http]}
  - {id: upgrade_keep_data, type: upgrade, strategy: same_tag_recreate, then: [ping, read_note], evidence_required: [digest_before_after, http]}
  - {id: uninstall_keep_data, type: uninstall, mode: rm, expect: data_dir_exists, evidence_required: [dir_before_after]}
  - id: known_limit_sqlite_vec
    type: log
    container: joplin-server
    expect_contains_any: ["sqlite-vec", "vector search disabled"]
    polarity: negative
    evidence_required: [log_excerpt]
evidence:
  summary_max_bytes: 1048576
  screenshots: [share_get]
timeouts: {install: 300, http: 30, restart: 120, upgrade: 300, uninstall: 120}
cleanup: {mode: rm_keep_data, purge_data: false}
owner: casaos-gate-exec
```

### 2.4 示例卡 B：wg-easy（manual 前置 + 设备/UDP + 已知限制）

```yaml
schema: 2
id: wg-easy
title: wg-easy
category: Utilities
environment: [E0, E1, E2, E3]
image: {public: "yunixintel/wg-easy:24.10-la5", private: null, arch: linux/loong64, tag_exception: false}
upstream_version: 15.4.0
dependencies:
  sidecars: []
  apps: []
  devices: []
  host_features: [NET_ADMIN, SYS_MODULE, "/lib/modules", "sysctl net.ipv4.ip_forward"]
ports:
  - {name: wireguard, container: 51820, host: 51820, proto: udp, primary: false}
  - {name: http, container: 51821, host: 51821, proto: tcp, primary: true}
volumes:
  - {name: wireguard, container: /etc/wireguard, host_casaos: /DATA/AppData/wg-easy/wireguard, host_istore: /srv/wg-easy/wireguard, mode: rw, primary: true}
  - {name: modules, container: /lib/modules, host: /lib/modules, mode: ro, primary: false}
accounts:
  admin: {user: admin, secret_ref: wg_admin, create: init_env}
preconditions:
  automation: needs_config
  manual:
    - id: reachable_host
      description: 把 INIT_HOST 改成公网/VPN 可达地址
      gate_check: {type: tcp, host: "${HOST_IP}", port: 51821, expect_open: true}
      if_unmet: BLOCKED
    - id: peer_device
      description: 用真实 WireGuard 客户端做双向握手/转发/NAT
      gate_check: {type: manual, steps: ["导入客户端配置", "ping 对端", "访问内网服务"], evidence: [screenshot, packet_capture]}
      if_unmet: PARTIAL
feature_inventory:
  covered:
    - {id: install, source: plan, checks: [install]}
    - {id: web_setup, source: upstream, checks: [web_root, setup_page]}
    - {id: db_and_config, source: image, checks: [wg0_conf, db_files]}
    - {id: restart, source: plan, checks: [restart_persistence]}
    - {id: ipv4_only, source: quirks, checks: [known_limit_ipv6]}
    - {id: no_amneziawg, source: quirks, checks: [known_limit_awg]}
  not_covered:
    - {id: external_nat, reason: 外网转发/NAT 需真实客户端与网络，未验证}
    - {id: ipv6, reason: 默认 DISABLE_IPV6=true，外网 IPv6 受 Docker 限制}
  coverage_complete: false
checks:
  - {id: install, type: install, expect: healthy, evidence_required: [install_log, docker_ps]}
  - {id: web_root, type: http, method: GET, path: /, port: 51821, expect_status_in: [200, 302], evidence_required: [http]}
  - {id: setup_page, type: http, method: GET, path: /setup/1, port: 51821, expect_status_in: [200, 302], evidence_required: [http, screenshot]}
  - {id: wg0_conf, type: docker_exec, container: wg-easy, argv: ["test", "-s", "/etc/wireguard/wg0.conf"], expect_exit: 0, evidence_required: [exec_log]}
  - {id: db_files, type: docker_exec, container: wg-easy, argv: ["sh", "-c", "ls -l /etc/wireguard"], expect_exit: 0, evidence_required: [exec_log]}
  - {id: restart_persistence, type: restart, target: app, wait: 30, then: [web_root, wg0_conf, db_files], evidence_required: [restart_log, exec_log]}
  - {id: known_limit_ipv6, type: docker_exec, container: wg-easy, argv: ["sh", "-c", "grep -q '^DISABLE_IPV6=true' /etc/wireguard/wg0.conf"], expect_exit: 0, polarity: negative, evidence_required: [exec_log]}
  - {id: known_limit_awg, type: docker_exec, container: wg-easy, argv: ["sh", "-c", "! command -v awg"], expect_exit: 0, polarity: negative, evidence_required: [exec_log]}
  - {id: manual_peer, type: manual, steps: ["客户端握手", "转发/NAT"], if_unmet: PARTIAL, evidence_required: [screenshot, packet_capture]}
evidence: {screenshots: [setup_page, manual_peer]}
timeouts: {install: 180, http: 30, restart: 120, manual: 1800}
cleanup: {mode: rm_keep_data}
owner: istore-la5-exec
```

### 2.5 示例卡 C：BookStack（MariaDB + 首次建管理员）

```yaml
schema: 2
id: bookstack
title: BookStack
category: Productivity
environment: [E0, E1, E2, E3]
image: {public: "yunixintel/bookstack:24.10-la5", private: null, arch: linux/loong64, tag_exception: false}
upstream_version: 26.09.2
dependencies:
  sidecars: [mariadb]
  apps: []
  devices: []
  host_features: []
ports:
  - {name: http, container: 80, host: 18109, proto: tcp, primary: true}
volumes:
  - {name: storage, container: /var/www/bookstack/storage, host_casaos: /DATA/AppData/bookstack/storage, host_istore: /srv/bookstack/storage, mode: rw, primary: true}
  - {name: uploads, container: /var/www/bookstack/public/uploads, host_casaos: /DATA/AppData/bookstack/uploads, host_istore: /srv/bookstack/uploads, mode: rw, primary: false}
accounts:
  admin: {user: admin@example.com, secret_ref: bookstack_admin, create: docker_exec_create_admin}
preconditions:
  automation: manual
  manual:
    - id: create_admin
      description: 首次用 docker exec 执行 bookstack:create-admin 创建管理员
      gate_check: {type: docker_exec, container: bookstack, argv: ["php", "artisan", "bookstack:create-admin", "--email=admin@example.com", "--name=Admin", "--password=${secret:bookstack_admin}"], expect_exit: 0}
      if_unmet: BLOCKED
  required_env: [APP_URL, DB_HOST, DB_DATABASE, DB_USERNAME, DB_PASSWORD]
  preload: []
feature_inventory:
  covered:
    - {id: install, source: plan, checks: [install, db_migration]}
    - {id: login, source: upstream, checks: [login_page, admin_login]}
    - {id: content, source: upstream, checks: [create_book, create_page, read_page]}
    - {id: upload, source: upstream, checks: [upload_image]}
    - {id: persistence, source: plan, checks: [restart_persistence]}
    - {id: lifecycle, source: plan, checks: [upgrade_keep_data, uninstall_keep_data]}
    - {id: sqlite_unsupported, source: quirks, checks: [known_limit_no_sqlite]}
  not_covered:
    - {id: ldap_saml_oidc, reason: 未配置外部身份源}
    - {id: pdf_export, reason: 未验证 PDF 导出依赖}
  coverage_complete: false
checks:
  - {id: install, type: install, expect: healthy, evidence_required: [install_log, docker_ps, sidecar_status]}
  - {id: db_migration, type: log, container: bookstack, expect_not_contains: ["Migration failed", "SQLSTATE"], evidence_required: [log_excerpt]}
  - {id: login_page, type: http, method: GET, path: /login, port: 18109, expect_status: 200, evidence_required: [http, screenshot]}
  - {id: create_admin, type: manual, steps: ["docker exec bookstack php artisan bookstack:create-admin ..."], evidence_required: [exec_log, screenshot]}
  - {id: admin_login, type: http, method: POST, path: /login, port: 18109, body: {email: admin@example.com, password: "${secret:bookstack_admin}"}, expect_status_in: [200, 302], evidence_required: [http]}
  - {id: create_book, type: http, method: POST, path: /books, port: 18109, expect_status_in: [200, 302], evidence_required: [http]}
  - {id: create_page, type: http, method: POST, path: /pages, port: 18109, expect_status_in: [200, 302], evidence_required: [http]}
  - {id: read_page, type: http, method: GET, path: /books/demo/page/demo, port: 18109, expect_status: 200, evidence_required: [http, screenshot]}
  - {id: upload_image, type: http, method: POST, path: /images, port: 18109, expect_status_in: [200, 302], evidence_required: [http]}
  - {id: known_limit_no_sqlite, type: docker_exec, container: bookstack, argv: ["sh", "-c", "test ! -f database/database.sqlite"], expect_exit: 0, polarity: negative, evidence_required: [exec_log]}
  - {id: restart_persistence, type: restart, target: app, wait: 30, then: [admin_login, read_page], evidence_required: [restart_log, http]}
  - {id: upgrade_keep_data, type: upgrade, strategy: same_tag_recreate, then: [admin_login, read_page], evidence_required: [digest_before_after, http]}
  - {id: uninstall_keep_data, type: uninstall, mode: rm, expect: data_dir_exists, evidence_required: [dir_before_after]}
evidence: {screenshots: [login_page, read_page, create_admin]}
timeouts: {install: 300, http: 30, restart: 180, upgrade: 300, manual: 900}
cleanup: {mode: rm_keep_data}
owner: casaos-gate-exec
```

### 2.6 卡片校验规则

`verify/phase2/validate_cards.py` 必须拒绝：id 与文件名不一致；缺必填字段；`feature_inventory` 缺 `not_covered`；check type 不在白名单；负向检查没有 `polarity: negative`；`manual` 应用缺 `preconditions.manual`；secret_ref 未在 `/build/verify-secrets/index.yaml` 登记；`${...}` 未解析（secret 除外）；端口/依赖不存在；卡片声称 115 但集合不齐。

## 3. 卡片生成算法

输入与优先级（高 -> 低）：`verify/phase2/overrides/<id>.yaml` > `store/istore/data/runtime-overrides.json` > `store/casaos/port-plan.json` > `store/loong64-descriptions.json` > `images/catalog.json` > `docs/LOONG64-QUIRKS.md`。

```pseudo
desc = load("store/loong64-descriptions.json").apps
catalog = load("images/catalog.json")                  # 118 = 115 + 3 base
casaos = dirs("store/casaos/Apps/*/docker-compose.yml")
istore = dirs("store/istore/src/app-meta/*")
port_plan = load("store/casaos/port-plan.json").apps
overrides = load_all("verify/phase2/overrides/*.yaml")
assert set(desc) == set(casaos) == set(istore) == set(port_plan) and len(desc)==115

for app_id in sorted(desc):
    d = desc[app_id]; o = overrides.get(app_id, {})
    card = base_schema(app_id, d.title, d.category)
    card.image.public = "yunixintel/%s:24.10-la5" % app_id
    card.image.tag_exception = False  # 基础层不在 115，tag 例外见 version-exceptions.yaml
    card.ports = port_plan[app_id].host_port + runtime_overrides[app_id].ports
    card.dependencies.sidecars = runtime_overrides[app_id].sidecars
    card.feature_inventory = feature_template(d.category) + quirks_negative(app_id, d.missing)
    card.preconditions = manual_preconditions(app_id) if automation=="manual" else {automation: ...}
    card.checks = render_checks(card.feature_inventory, d.verification, o.checks)
    card.not_covered += explicit_uncovered(d.missing, o.not_covered)
    write("docs/verification/cards/%s.yaml" % app_id, card)

run("python -I verify/phase2/validate_cards.py --expect 115")
```

映射规则：
- 分类模板固定 11 类：Media、Developer、Productivity、Utilities、Networking、Downloaders、Cloud、Monitoring、Backup、Home Automation、Security；每类至少 3 个核心功能 check。
- `review.automation == manual` 的 25 个应用必须有 `preconditions.manual[]` 与 `if_unmet`；`needs_config` 的 7 个应用必须有配置 gate。
- `dependencies.zh_cn` 中的“必须 PostgreSQL/MariaDB/Redis/MinIO/设备/host 网络”自动转成 `dependencies` 与 install 前置检查。
- QUIRKS 的“缺失功能”只在能机器判定时生成负向 check；不能判定的写入 `not_covered`，不得假装覆盖。
- `linkwarden`/`karakeep`：public 变体检查 LBrowser sidecar + `/opt/apps/lbrowser:ro` 宿主字节；private 变体检查单镜像 `local/*` 且无 LBrowser 行。`lbrowser-runtime` 版本固定 `3.4.2293.2`。
- 不覆盖项必须逐条有 `id`、`reason`、`disposition`（PARTIAL/NOT TESTED）、`owner`；不得用空数组糊弄。
- 生成器不得手改卡片；人工差异只进 override。重新生成后跑 diff，任何未解释变化阻断。

## 4. runner 架构

```text
run.py
  ├─ preflight（版本矩阵 + 集合 + 端口 + 磁盘/内存）
  ├─ scheduler（批次、并发上限 2、DB 独占锁）
  ├─ adapters/
  │    ├─ base.py      prepare/install/status/exec/restart/upgrade/uninstall/logs/cleanup
  │    ├─ casaos.py    CasaOS API + docker inspect
  │    └─ istore.py    SSH + opkg + /usr/libexec/istorec/<id>.sh + uci
  ├─ evidence.py       命令/HTTP/截图/日志/脱敏/哈希
  ├─ assertions.py     PASS/FAIL/SKIP/BLOCKED + verdict 计算
  ├─ reporters/        JUnit XML、JSON、Markdown
  └─ state.py          原子写 state + events.jsonl
```

适配器契约：
```pseudo
prepare(card) -> {ok, reason}                 # 依赖/预载/设备/secret
install(card) -> {ok, app_ref, sidecars, digest}
status(card) -> {running, healthy, started_at, image_digest}
exec(card, argv) -> {exit, stdout, stderr}    # CasaOS: docker exec；iStore: ssh docker exec
restart(card) -> {ok, before, after}
upgrade(card) -> {ok, old_digest, new_digest}
uninstall(card, mode) -> {ok, data_present}
logs(card, since, tail) -> text
cleanup(card) -> {ok, leftover}
```
`adapter.mode` 只能是 `real` 或 `dry-run`。`dry-run` 的结果强制 `NOT TESTED`，不得 PASS。

CasaOS 适配器：
- 固定 `GET http://127.0.0.1:8081/v2/app_management/apps`，期望 `data.list` 长度 115。
- 认证 token 从 `/build/verify-secrets/casaos.env` 读取；登录/安装/卸载端点必须在 preflight 写入 `verify/phase2/adapters/casaos.endpoints.yaml`；未确认的端点标 BLOCKED，不得猜路径。
- 每次调用记录请求/响应头（Authorization/Cookie 脱敏）和耗时。
- 安装后必须 `docker inspect` 校验镜像 digest 与 VERSION-MATRIX 一致，不能只看 API 返回。

iStore 适配器：
```sh
ssh "$ISTORE_HOST" "opkg update && opkg install app-meta-$APP"
ssh "$ISTORE_HOST" "/usr/libexec/istorec/$APP.sh install"
ssh "$ISTORE_HOST" "/usr/libexec/istorec/$APP.sh status-all"
ssh "$ISTORE_HOST" "uci get $APP.main.variant"     # E2=public, E3=private
ssh "$ISTORE_HOST" "docker inspect --format '{{.Image}}' $APP"
```
E2 必须 `variant=public` 且无 `local/*`；E3 的 Linkwarden/Karakeep 必须 `local/*`，LBrowser 按变体检查。`lbrowser-runtime` 可自动 pull；若宿主 `/opt/apps/lbrowser`（浏览器字节）缺失，public 的 Linkwarden/Karakeep 抓取类功能记 BLOCKED，不得假 PASS。

证据采集：每个 check 建 `<evidence>/<app>/<check>/`，写 `command.txt`、`stdout.txt`、`stderr.txt`、`meta.json`；HTTP 另写 `request.http`、`response.http`、`body.sha256`；截图写 PNG + 同名 `.json`。写入前脱敏；原始大日志存 `/build/verify-evidence/<run-id>/`，仓库只放摘要和哈希。

报告：
- `results/<env>/<app>.json`：机读结果，含 verdict、failure_class、每 check 状态、证据路径、版本快照、重试。
- JUnit：一个 testsuite/app，一个 testcase/check；FAIL -> `<failure>`；NOT TESTED/BLOCKED -> `<skipped message=...>`。
- Markdown：`reports/BATCH-<n>.md` 和 `reports/PHASE-2-FINAL.md`，按分类/环境/verdict 汇总，列出所有 not_covered 和 BLOCKED 根因。
- 不得在报告里把 NOT TESTED 计入通过数。

并发与守卫：
- 同时最多 2 个应用；数据库/对象存储类独占；`verify/state/locks/<app>.lock`，TTL 30 分钟。
- 磁盘 `/build`、`/var` 可用 < 2GB 暂停；内存 `MemAvailable` < 1GB 暂停；端口从 `port-plan.json` 租用，冲突即 BLOCKED。
- 每个应用结束清理容器/临时网络；`rm` 保留数据，`purge` 需显式 `ISTORE_PURGE_DATA=1`；清理后记录残留。
- 重试：网络/拉镜像/SSH 超时最多 2 次（5s/15s 退避）；断言不匹配 0 次；每 check 总尝试 <=3；失败即隔离并写 state，不跨批无限重试。
- 每批结束提交报告 + state；失败项先定位再重跑。

## 5. 目录结构与 Git 边界

```text
verify/phase2/
  README.md  gen_cards.py  validate_cards.py  collect_versions.sh  preflight.py  run.py  gate.py
  adapters/  lib/  schemas/  templates/  overrides/  version-exceptions.yaml  .run/
docs/verification/
  specs/HARNESS-VERSION-EVIDENCE.md
  cards/<app>.yaml
  results/<env>/<app>.json
  evidence/<env>/<app>/...
  reports/  VERSION-MATRIX.md  VERSION-MATRIX.json
/build/verify-evidence/<run-id>/...    # 仓库外
/build/verify-secrets/                 # 0700，仓库外
```

Git：specs、cards、overrides、schemas、results JSON、reports、VERSION-MATRIX、摘要证据/关键截图（每应用 <=1MB、<=2 张）进 Git。原始日志、完整视频、DB dump、镜像 tar、`.run/`、`/build/*`、secret 不进 Git。`.gitignore` 需含 `verify/phase2/.run/`、`docs/verification/evidence/**/raw/`；仓库不放大日志。

## 6. 证据规范

公共信封：`evidence_id`、`run_id`、`env`、`app`、`check_id`、`verdict`、`command`、`started_at/ended_at`、`exit_code`、`stdout/stderr` 路径、`http`、`screenshots`、`logs`、`artifacts[{path,sha256,bytes}]`、`redactions`、`actual_source`、`environment_fingerprint`。

| verdict | 最低证据 | 禁止 |
|---|---|---|
| PASS | 每个必测 check 的命令+输出+预期/实际；HTTP 头；关键截图；每个已知限制的负向证据；重启/持久化；preflight 无 D3/D4；清理完成；证据哈希 | 只有首页 200；只有一次手动点击；缺负向检查 |
| PARTIAL | 主路径 PASS 证据 + 完整 `not_covered`（原因/owner）+ 已覆盖项证据；未执行项显式列出 | 把未覆盖说成通过 |
| BLOCKED | 复现命令、错误原文、退出码、依赖/设备/镜像缺失证据、已尝试步骤、根因 `failure_class` | 用替代 tag 冒充；只写“失败” |
| NOT TESTED | 未执行原因、前置条件、owner、计划时间；state 同步；无截图冒充 | 默认 PASS；dry-run 当实测 |

截图命名：`<env>_<app>_<check>_<seq>_<UTC>.png`，例 `E0_joplin-server_share_get_01_20261027T031500Z.png`；完整页加 `_full`；同名 `.json` 记录 URL/title/viewport/UA。密码字段必须遮挡。
HTTP：`curl -sS -D response.http -o body --max-time N`；记录 method/URL/请求头（脱敏）/请求体（脱敏）/状态/响应头/body 前 64KB/sha256；不默认 `-L`，重定向链要记录；禁止无证据的 `-k`（TLS 限制需单独说明）。
日志：`docker logs --since <start> --tail 200`，记录容器 id、镜像 digest、退出码；仓库摘录 <=200 行，全文在 `/build`；脱敏后写入。
Secret：只从 `/build/verify-secrets/` 读取（0700/0600），证据只写 `secret_ref` 和“present”，绝不写值；脱敏键含 password/passwd/token/secret/key/authorization/cookie/session/dsn；提交前跑 secret 扫描。测试密码/账号不得进 Git。

## 7. 会话 state 与交接

路径：`verify/state/<session>.yaml`，事件 `verify/state/<session>.events.jsonl`。仅 owner 会话可写自己的 state/evidence。

```yaml
schema: 1
session: casaos-gate-exec
phase: [A, B]
env: [E0, E1]
run_id: "<UTC>-<rand>"
status: running            # running|paused|closed|failed
started_at: "<UTC>"
updated_at: "<UTC>"
current_batch: B1
cursor: {app: joplin-server, check: admin_login}
completed: [{app: gatus, verdict: PASS, evidence: "docs/verification/results/E0/gatus.json", at: "<UTC>"}]
failed: [{app: x, check: y, failure_class: product, evidence: "...", retry: 0}]
blocked: [{app: linkwarden, reason: "宿主 /opt/apps/lbrowser 浏览器字节未预置", evidence: "..."}]
not_tested: [{app: ente-server, reason: "无外部 S3", owner: istore-p1-exec}]
pending_retest: []
locks: []
ports_held: [18139]
evidence_roots: ["docs/verification/evidence/E0", "/build/verify-evidence/<run-id>"]
last_commit: "<sha>"
next_action: "继续 B1：miniflux install"
handoff: {to: null, summary: null, evidence_manifest: null}
```

更新规则：每个 check 前后原子写（tmp+rename）；事件 JSONL 追加；state 与 evidence manifest 哈希一致；每批报告后更新 `last_commit`。交接条件：本会话 exit criteria 达成、`status: closed`、无锁、evidence manifest 完整、写出 `handoff.summary`（完成/失败/待复测/环境状态）。新会话只读交接文件，不复用旧 run_id；旧结果保留但不得冒充新证据。

| 会话 | 环境/阶段 | 产物 | 结束条件 |
|---|---|---|---|
| `casaos-gate-exec` | E0/E1，A+B | C-03/C-04/C-05/C-06、CasaOS 平台矩阵、115 应用结果 | G1a + CasaOS 全量报告 |
| `istore-la5-exec` | E2，C | ISO 保存、U 盘、la5、public feed、115 应用 | la5 报告 + 隔离审计 |
| `istore-p1-exec` | E3，D | p1、private feed、local 镜像、115 应用 | p1 报告 + 隔离审计 |
| `casaos-clean-exec` | E5，A4 | B 机 sdb 干净安装 | G1b 结论；未释放则 NOT TESTED |

## 8. 质量门槛

| 门槛 | 通过条件 | 失败处理 |
|---|---|---|
| G0 规范一致 | 本文与 PHASE-2 的环境/判定/红线一致 | 退回修改 |
| G1 版本前置 | preflight 无 D3/D4；集合严格 115 | 该环境不得出 PASS |
| G2 卡片 | 115 张齐全、schema 通过、manual/负向检查齐全 | 不得开跑 |
| G3 证据 | 每个 PASS 有命令/输出/截图/哈希；每个已知限制有负向证据 | 降级 PARTIAL/BLOCKED |
| G4 反伪造 | 无首页 200 冒充、无 dry-run 冒充、无未测默认 PASS、无复用证据 | 整批结果作废 |
| G5 隔离 | E0/E2 无 `local/*`；E3 私人镜像不公开；无 secret 进 Git | 阻断发布 |
| G6 发布 | G1-G5 全过；E5 干净安装完成（否则 G1 只能分项） | 不发布 |

禁止模式与检测：
1. 首页 200 冒充全功能：卡片核心功能 check <3，或所有 http 都是 `path: /` -> gate 拒绝。
2. dry-run 冒充真机：`adapter_mode != real` 且 verdict PASS -> gate 拒绝。
3. 未测默认 PASS：PASS 但必测 check 无证据 -> gate 拒绝。
4. 预期抄成实测：`actual == expected` 且 `actual_source` 为空 -> gate 拒绝。
5. 证据复用：同一截图/输出 sha256 出现在不同 run/app -> gate 拒绝。
6. 手动一次当全回归：manual 应用 PASS 但缺少完整回归证据 -> 最高 PARTIAL。
7. 公私混用：`grep -R "local/" docs/verification/results/E0 docs/verification/results/E2` 命中 -> 阻断。
8. 凭据泄漏：`grep -RInE '(password|passwd|token|secret|api[_-]?key|BEGIN .*PRIVATE KEY)' docs/verification verify/phase2` 命中且无 allowlist -> 阻断。
9. 未解释失败：`failure_class` 为空或 `product` 未附复现 -> 不得关闭批次。
10. 过期证据：证据时间早于 run 开始或 state.run_id 不一致 -> gate 拒绝。

`gate.py` 伪代码：
```pseudo
for env in envs:
  m = load_version_matrix(env); assert no D3/D4
  for app in apps:
    r = load_result(env, app)
    assert r.card_sha256 == sha256(card)
    if r.verdict == "PASS": assert all_mandatory_pass_with_evidence(r)
    if r.adapter_mode != "real": assert r.verdict != "PASS"
    assert no_expected_copied_as_actual(r)
    assert evidence_hashes_unique(r)
    assert not public_private_mix(r)
    assert no_secret(r)
write_gate_report()
```

## 附录 A：结果 JSON 最小字段

```json
{"schema":1,"run_id":"...","env":"E0","app":"joplin-server","card_sha256":"...",
 "image":"yunixintel/joplin-server:24.10-la5","image_digest":"sha256:...",
 "adapter_mode":"real","verdict":"PASS|PARTIAL|BLOCKED|NOT TESTED",
 "verdict_reason":"","failure_class":null,"started_at":"...","ended_at":"...",
 "checks":[{"id":"ping","type":"http","status":"PASS","expected":"200","actual":"200",
            "actual_source":"curl ...","evidence":["..."],"duration_ms":123}],
 "feature_coverage":{"covered":6,"not_covered":2,"items":["..."]},
 "versions":{...},"retries":[],"cleanup":{"ok":true,"leftover":[]},
 "evidence_manifest":"...sha256","owner":"casaos-gate-exec"}
```

## 附录 B：执行前检查清单

- [ ] `collect_versions.sh` 已跑，VERSION-MATRIX 无 D3/D4
- [ ] 115 卡由生成器产出并通过 `validate_cards.py --expect 115`
- [ ] `/build/verify-secrets` 权限 0700、文件 0600、无值进 Git
- [ ] 端口租约/磁盘/内存守卫通过
- [ ] E0/E2 public 无 `local/*`；E3 private 已预载 `local/*`；public 的 `lbrowser-runtime` 可自动 pull，宿主 `/opt/apps/lbrowser` 已预置
- [ ] `node-sharp:24.22.1` 已按 loong64 检查，未误查 `24.10-la5`
- [ ] manual 应用的前置 gate 已定义，未满足时 `if_unmet` 生效
- [ ] state 文件已初始化，`run_id` 唯一
- [ ] 任何 dry-run 会话已标记，不会产出 PASS
