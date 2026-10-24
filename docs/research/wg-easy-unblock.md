# wg-easy 龙芯（LoongArch64）解锁报告

- 日期：2026-10-24
- 目标：wg-easy v15.4.0 → Loongnix 25 / 3A6000 / loong64（构建容器 openEuler 24.03，glibc 2.38，16K 页）
- 结论：**GO**。v15.4.0 全量构建与运行冒烟已在龙芯本机通过；真实 WireGuard 隧道待真机验收。预计 2–3 人日。

## 1. 结论与证据
**做 v15.4.0，不做 v14，AmneziaWG 放二期。** 关键不是“试试”，而是以下四项已实测：

| # | 结论 | 证据 |
|---|---|---|
| 1 | 内核 WireGuard 可用 | `CONFIG_WIREGUARD=m`；`wireguard.ko` 已签名，`modprobe -n wireguard` 依赖齐全 |
| 2 | libsql 有可用的 loong64 绑定 | 龙芯 npm 镜像的 `@libsql/linux-loong64-gnu@0.5.13` 与 `libsql@0.5.29` JS 层、Drizzle 0.45 全链路跑通 |
| 3 | Nuxt/Nitro 可在龙芯原生构建 | 在 `yunixintel/node:24.22.1` 内 `pnpm build` 成功，`.output` 30MB |
| 4 | 运行时可启动 | 容器内 DB 迁移、`wg0.conf` 生成、HTTP 302 → `/setup/1` 全部正常 |

尚未验证：真实 `wg-quick up` + 内核模块 + 客户端握手/转发。这是发布前唯一硬门槛，风险低（模块与工具链均已确认）。

## 2. 版本与结构（v15.4.0，tag，AGPL-3.0）

| 组件 | 版本 | 说明 |
|---|---|---|
| wg-easy | v15.4.0 | 上游 `wg-easy/wg-easy`，AGPL-3.0；v14 是 CC BY-NC-SA 4.0（**非商用**，不适合应用商店） |
| Node | 24.22.1 | `yunixintel/node:24.22.1`，openEuler 24.03 SP4，loong64 ABI2 |
| 前端 | Nuxt 4.5.2 + Nitro | Vite 8 / Rolldown 1.2.3 / Rollup 4.62.4 / esbuild 0.28.2 |
| 数据库 | Drizzle 0.45.2 + `@libsql/client` 0.17.4 + `libsql` 0.5.29 | 本地 `file:/etc/wireguard/wg-easy.db` |
| 密码 | argon2 0.45.1 → **hash-wasm 4.12.0** | 原生 argon2 在 loong64 退出时崩溃，必须替换 |
| VPN | `wg`/`wg-quick`，实验性 `awg`/`awg-quick` | 标准 WireGuard 为默认路径 |

数据库层集中在 `src/server/database/sqlite.ts`：`createClient({url:'file:/etc/wireguard/wg-easy.db'})` + `drizzle({client})`；7 个 repository 全部通过 Drizzle 查询。Drizzle 的 libsql 驱动只依赖 Client 的 `execute/batch/migrate/transaction` 与 ResultSet（rows 为数组）。迁移为 0000–0009 共 10 个 SQLite SQL。

v15 已移除 `PASSWORD`/`PASSWORD_HASH`，首次启动用 Web 向导或 `INIT_ENABLED/INIT_USERNAME/INIT_PASSWORD/INIT_HOST/INIT_PORT`；`WG_HOST` 也不再是环境变量。

## 3. 数据库方案对比（核心解锁点）

| 方案 | 改动面 | 工作量 | 风险 | 结论 |
|---|---|---|---|---|
| A. 复用龙芯预编译 libsql 绑定 | 仅构建脚本 + `LIBSQL_JS_DEV=1` | 0.5 天 | 低（版本错配已实测可用） | **采用** |
| B. 从 Rust 源码构建 libsql-js | 新增 Rust/Neon 构建阶段 | 1–2 天 | 中 | 备选，镜像不可用时启用 |
| C. 换 better-sqlite3 / `node:sqlite` | 7 个 repository + `sqlite.ts`，或写 Client shim | 1–3 天 | 中 | 不必要 |
| D. 旧版 v14（无 DB，JSON 配置） | 直接构建 | 0.5–1 天 | 低 | 不推荐（EOL + 非商用许可） |

### 3.1 方案 A（采用）实测
`@libsql/linux-loong64-gnu@0.5.13` 从 `registry.loongnix.cn:5873` 取得，ELF `LoongArch`、`e_flags=0x43`（ABI2.0），在 glibc 2.38 的 openEuler 镜像中可加载。`libsql@0.5.29` 的 JS 层通过 `LIBSQL_JS_DEV=1` 走 `load(__dirname)`，只找同目录 `index.node`，完全绕开 `@neon-rs/load` 对 loong64 的架构拒绝。

已用 `@libsql/client` + `drizzle-orm/libsql` 跑通：wg-easy 全部迁移、CRUD、异步事务、`sql.placeholder` 预编译语句、batch、JSON/boolean 列。绑定 `index.node` SHA-256：`51a33acb8bf898efe5dcff16adc1b74b6448ed9883a719f439ecd5ce29570650`。

注意：npm 上 `libsql` 的 `cpu` 字段不含 `loong64`，`pnpm install` 会跳过平台包；构建时用 `--force` 或直接把绑定放到 `node_modules/.pnpm/libsql@0.5.29/node_modules/libsql/index.node`。**必须 vendor 该 .node 并锁 SHA-256**，不要依赖镜像长期存在。

### 3.2 方案 B（备选）：libsql 源码构建
- 源码：`tursodatabase/libsql-js` tag `v0.5.29`；Rust 1.78+，`libsql 0.9.30`（`encryption`），Neon 1.0（N-API 6）。
- 命令：`cargo build --release` → 将 `target/release/liblibsql_js.so` 改名为 `index.node` 放入 `libsql` 包；无需 Neon CLI。
- 依赖风险：锁文件里 `ring 0.17.8`；本项目已在 loong64 验证 `ring 0.17.14` 可编译，需 `cargo update -p ring --precise 0.17.14`。无 io-uring/jemalloc；SQLite C 代码可移植。
- 结论：可行，但非首选；只有镜像绑定丢失时才值得投入。

### 3.3 方案 C：换 better-sqlite3 / SQLite

直接改用 `drizzle-orm/better-sqlite3` 不是一行替换：wg-easy 的 repository 大量使用 **异步事务**、`.prepare()` + `sql.placeholder`、`execute({args})`，而 better-sqlite3 驱动是同步事务/不同预备语句 API，需改 7 个 repository 和迁移器，约 2–3 天。另一条路是写一个 200 行左右的 `@libsql/client` 兼容 shim（`execute/batch/migrate/transaction/close`，ResultSet.rows 用数组），底层用 better-sqlite3 或 Node 24 内置 `node:sqlite`，可做到零 repository 改动；`node:sqlite` 的 `columns()`/`setReturnArrays(true)` 已在 Node 24.22.1 实测可用。但方案 A 已通，无需此改动。

### 3.4 必须替换 argon2

`argon2@0.45.1` 无 loong64 预编译；源码 `node-gyp` 可编过、hash/verify 结果正确，但进程退出时 `free(): invalid pointer`/段错误（0.40.2 同样）。改用纯 WASM 的 `hash-wasm`（`argon2id` + `argon2Verify`，m=65536,t=3,p=4，16B 随机盐，输出 PHC 编码），实测 rc=0、verify 通过。改动仅 `src/server/utils/password.ts` 的 3 处调用；`@phc/format` 校验逻辑不变。

## 4. 龙芯内核 WireGuard（只读实测）
```
Linux yunix-pc 6.6.52-loong64 #1 SMP Loongnix 6.6.52-1.11 loongarch64
CONFIG_WIREGUARD=m
/lib/modules/6.6.52-loong64/kernel/drivers/net/wireguard/wireguard.ko
vermagic: 6.6.52-loong64 SMP mod_unload modversions LOONGARCH 64BIT（已签名）
modprobe -n -v wireguard → libchacha/libpoly1305/libcurve25519-generic/udp_tunnel/ip6_udp_tunnel/libchacha20poly1305 全部存在
```
- 用户态工具：Loongnix 25 apt `wireguard-tools 1.0.20210914-3 (loong64)`；openEuler 24.03 **EPOL** 有 `wireguard-tools 1.0.20210914-2.oe2403sp4`。已在 `yunixintel/node:24.22.1` 内 `dnf install` 验证，`wg --version` / `wg-quick` 正常。**构建镜像时不要禁用 EPOL。**
- 内核网络模块：`nf_tables`、`nf_conntrack`、`ip_tables`、`iptable_nat`、`br_netfilter`、`tun` 均在；`/dev/net/tun` 存在；`net.ipv4.ip_forward=1`；openEuler 的 `iptables` 是 legacy 1.8.9，正好与上游一致。
- 宿主 firewalld 正在运行，已有 `docker` zone（docker0/br-*），所以 **bridge + 发布端口** 比 host 网络少踩防火墙；仍建议在 public zone 显式放行 51820/udp（以及受控的 51821/tcp）。
- 当前 `loongson-lab` 未装 `docker compose` 插件（`docker: 'compose' is not a docker command`）；镜像落地前需装 `docker-compose-plugin` 或用下面的 `docker run`。

容器权限清单：

| 项 | 必需性 | 说明 |
|---|---|---|
| `cap_add: NET_ADMIN` | 必需 | 建 wg 接口、iptables、路由 |
| `cap_add: SYS_MODULE` + `/lib/modules:ro` | 建议 | 允许容器内 `modprobe wireguard`；宿主先 `modprobe` 后可去掉 |
| `sysctl net.ipv4.ip_forward=1` | 必需 | 容器 netns 内转发 |
| `sysctl net.ipv4.conf.all.src_valid_mark=1` | 必需 | wg-quick 策略路由校验 |
| `NET_RAW` | 仅 Podman | Docker 不需要 |
| `/dev/net/tun` | 仅用户态 | 仅 AmneziaWG/wireguard-go 需要 |

## 5. AmneziaWG（二期，暂不首发）
- wg-easy 仅在 `EXPERIMENTAL_AWG=true` 时探测 `modinfo amneziawg`；无模块则回退标准 WireGuard。强制走 awg 需 `OVERRIDE_AUTO_AWG=awg`。
- Loongnix 内核无 `amneziawg` 模块；上游镜像自带 `amneziawg-go` + `amneziawg-tools`，可用用户态路线。`wg-quick` 在无内核模块时会回退 `WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go`，因此需设该环境变量、`/dev/net/tun`、`NET_ADMIN`。
- 构建门槛：当前 `amneziawg-go` master 的 `go.mod` 要求 **Go 1.25.0**，A 机是 1.24.4；需装 Go 1.25 loong64 或 pin 旧 tag。`amneziawg-tools` 是 C，openEuler 有 `kernel-headers/gcc/make`，可编。
- 结论：**首发 No-Go**（用户态性能较低、Go 工具链升级、无内核模块）；二期再评估。

## 6. 构建方案（已在本机跑通）
基础镜像用 `yunixintel/node:24.22.1`（openEuler 24.03 SP4、Node 24.22.1、glibc 2.38）。上游 `packageManager` 锁 pnpm 12.14.0，但 pnpm 12 在 loong64 会尝试下载不存在的原生二进制；**改用纯 JS 的 pnpm 11.26.0**（`node pnpm/bin/pnpm.cjs install --ignore-scripts --no-frozen-lockfile`，实测 3 分 14 秒）。

四个 loong64 原生绑定（全部从 `https://registry.loongnix.cn:5873`，实测可用）：

| 包 | 版本 | 用途 | 放置 | SHA-256 |
|---|---|---|---|---|
| `@libsql/linux-loong64-gnu` | 0.5.13 | 数据库 | `libsql/index.node` | `51a33acb…0650` |
| `@oxc-parser/binding-linux-loong64-gnu` | 0.152.0 | Nuxt/i18n 构建 | 根 `node_modules/@oxc-parser/…` | `1db1640c…3187` |
| `@oxc-transform/binding-linux-loong64-gnu` | 0.152.0 | Nuxt/i18n 构建 | 根 `node_modules/@oxc-transform/…` | `c5482613…93c5` |
| `lightningcss-linux-loong64-gnu` | 1.33.0 | CSS 压缩 | 复制到 `$(readlink -f node_modules/lightningcss)/` | `3038e2b1…bb73` |

关键步骤：
```bash
# .npmrc（Rolldown 主包在 npm，loong64 binding 只在龙芯镜像）
@rolldown:registry=https://registry.loongnix.cn:5873/
# 安装（pnpm 11.26，--ignore-scripts 避开 argon2/esbuild 的 build 检查）
node pnpm/bin/pnpm.cjs install --ignore-scripts --no-frozen-lockfile
# 放入四个 vendor 绑定（版本错配的 oxc 0.152 binding + 0.141 JS 已实测可解析/可构建）
# 打 hash-wasm 补丁后构建
node pnpm/bin/pnpm.cjs build
# 关键：Nitro 会把 libsql 包复制进输出但不带原生模块
cp libsql.index.node .output/server/node_modules/libsql/index.node
```
运行时 Dockerfile 骨架：
```dockerfile
FROM yunixintel/node:24.22.1
RUN dnf install -y wireguard-tools iproute iptables procps-ng && dnf clean all
COPY --from=build /app/.output /app
COPY --from=build /app/server/database/migrations /app/server/database/migrations
COPY libsql.index.node /app/server/node_modules/libsql/index.node
ENV LIBSQL_JS_DEV=1 PORT=51821 HOST=0.0.0.0 INSECURE=false \
    INIT_ENABLED=false DISABLE_IPV6=false DEBUG=Server,WireGuard,Database,CMD,Firewall
WORKDIR /app
VOLUME ["/etc/wireguard"]
EXPOSE 51820/udp 51821/tcp
HEALTHCHECK --interval=1m --timeout=5s --retries=3 \
  CMD wg show | grep -q interface || exit 1
CMD ["node", "server/index.mjs"]
```
**运行冒烟结果**（本机容器，`wg-quick` 用桩程序，未触碰宿主网络）：`Database Migration complete`、生成 `/etc/wireguard/wg0.conf`、`WireGuard Interface wg0 started successfully`、`Listening on http://[::]:51821`、`/` 302 到 `/setup/1`、DB 文件 96KB。说明 Nuxt 输出、Nitro 打包、hash-wasm、libsql 绑定、迁移、配置生成均正常。

## 7. 最小 compose（首发：IPv4-only、bridge）
```yaml
services:
  wg-easy:
    image: yunixintel/wg-easy:loong64
    container_name: wg-easy
    restart: unless-stopped
    ports:
      - "51820:51820/udp"
      - "51821:51821/tcp"
    volumes:
      - etc_wireguard:/etc/wireguard
      - /lib/modules:/lib/modules:ro
    cap_add: [NET_ADMIN, SYS_MODULE]      # Podman 再加 NET_RAW
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv4.conf.all.src_valid_mark=1
    environment:
      PORT: "51821"
      INSECURE: "true"                    # 直连 HTTP；公网请反代并改 false
      DISABLE_IPV6: "true"
      INIT_ENABLED: "true"
      INIT_USERNAME: "admin"
      INIT_PASSWORD: "change-me"
      INIT_HOST: "vpn.example.com"        # 公网域名或 IP
      INIT_PORT: "51820"
      LIBSQL_JS_DEV: "1"
volumes:
  etc_wireguard:
```
宿主准备：
```bash
sudo modprobe wireguard
sudo firewall-cmd --permanent --add-port=51820/udp
sudo firewall-cmd --permanent --add-port=51821/tcp   # 建议仅内网/反代
sudo firewall-cmd --reload
```
若未装 compose 插件，用等价的 `docker run`（同上参数）即可。首发不做 IPv6（`DISABLE_IPV6=true`），待 docker 网络 IPv6 与 ip6tables 实测后再开；上游 IPv6 子网与 sysctls 可原样加回。

## 8. 发布前验证（硬门槛）
1. 构建机：按第 6 节构建，确认 `.output/server/node_modules/libsql/index.node` 存在、`file` 显示 LoongArch。
2. 启动：`docker compose up -d`，`docker logs` 出现迁移完成与接口启动；`curl -I http://<host>:51821/` 得到 302。
3. 真机隧道：UI 完成 setup，创建客户端，导入配置；客户端 `wg-quick up` 后 `docker exec wg-easy wg show` 有 handshake，`ping 10.8.0.1` 通，经隧道访问外网正常。
4. 转发/NAT：容器内 `iptables -t nat -L POSTROUTING -n` 有 MASQUERADE；断开后 `wg show` 无 handshake。
5. 重启与升级：`docker compose down && up`，数据卷保留；`docker inspect --format '{{.State.Health.Status}}' wg-easy` 为 healthy。
6. 回归：再跑一次 DB 迁移测试与密码 hash/verify（hash-wasm）。
## 9. 风险与工作量

| 风险 | 概率/影响 | 缓解 |
|---|---|---|
| 龙芯 npm 镜像的绑定被删/漂移 | 中/高 | **vendor 4 个 .node + SHA-256**，构建不依赖在线镜像 |
| libsql/oxc 版本错配（0.5.13 vs 0.5.29；0.152 vs 0.141） | 中/中 | 固定 tag v15.4.0 与版本，构建后跑 DB/构建冒烟；升级需重新验证 |
| 真实 wg 隧道未测 | 低/高 | 首发前按第 8 节在测试机验收（会加载内核模块，需授权） |
| glibc/ABI 不匹配 | 低/中 | 已实测 ABI2.0 绑定在 glibc 2.38 镜像可运行；仍锁同一 artifact |
| firewalld/IPv6/bridge | 中/中 | 首发 IPv4-only + 显式放行端口；docker zone 已存在 |
| 上游 master 已到 0.18/4.6 | 高/低 | 只用 tag v15.4.0，不跟 master |
| AmneziaWG | — | 二期，需 Go 1.25 + /dev/net/tun |
| AGPL 合规 | — | 镜像分发需提供对应源码与补丁（hash-wasm patch 放仓库） |

**工作量**：构建管线 1 天；镜像/entrypoint/compose 0.5 天；真机隧道验收 0.5 天；文档与发布 0.5 天；合计 **2–3 人日**（不含 AmneziaWG）。

## 10. 首发范围与降级
- 支持：标准 WireGuard（内核模块）、Web UI、客户端/二维码/一次性链接、每客户端防火墙（iptables-legacy）、2FA/OAuth（纯 JS）、Prometheus/JSON 指标。
- 关闭：AmneziaWG（无内核模块、Go 1.25）、IPv6（首版）、原生 argon2（已换 hash-wasm）。
- 回退：若龙芯绑定不可用且不愿做 Rust 构建，再评估 v14；但 v14 为 CC BY-NC-SA 4.0（非商用）且已停止维护，不建议进入公开应用源。
