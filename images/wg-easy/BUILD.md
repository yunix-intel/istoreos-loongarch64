# wg-easy v15.4.0（loong64）构建记录

## 结论

- 镜像：`yunixintel/wg-easy:loong64` / `yunixintel/wg-easy:24.10-la5`
- 架构：`linux/loong64`；两个 tag 的 manifest digest 相同
- digest：`sha256:52bd56b2cf5cd8c14183199ec6f65489c3a27837c05421e90849e2b5529c38ea`
- 大小：本地 509 MB（`docker images`）；Hub 压缩后 169.1 MiB（177,276,810 B）
- 状态：构建、启动、DB 迁移、`wg0.conf` 生成、HTTP 302→`/setup/1`、数据卷持久化、healthcheck 均通过
- **未验证**：真实 WireGuard 客户端握手/隧道、真实 `wg-quick` + 内核模块、宿主防火墙/NAT

## 版本

| 组件 | 版本 |
|---|---|
| wg-easy | v15.4.0（AGPL-3.0） |
| Node | 24.22.1（`yunixintel/node:24.22.1`，openEuler 24.03 SP4，glibc 2.38） |
| 前端 | Nuxt 4.5.2 / Nitro，Vite 8.2.1，Rolldown 1.2.3，Rollup 4.62.4，esbuild 0.28.2 |
| 数据库 | Drizzle 0.45.2，`@libsql/client` 0.17.4，`libsql` 0.5.29 + loong64 原生绑定 0.5.13 |
| 密码 | hash-wasm 4.12.0（替换 argon2 0.45.1） |
| 包管理 | pnpm 11.21.0（纯 JS，匹配上游 `packageManager`） |
| 运行时工具 | openEuler EPOL `wireguard-tools` 1.0.20210914-2，`iproute`，`iptables`，`procps-ng` |

## 构建上下文

路径：`/build/appimages/wg-easy`（vendor 二进制不入仓库）

```text
/build/appimages/wg-easy/
├── Dockerfile
├── docker-entrypoint.sh
├── patches/0001-replace-argon2-with-hash-wasm.patch
└── vendor/
    ├── wg-easy-v15.4.0.tar.gz
    ├── pnpm-11.21.0.tgz
    ├── libsql/index.node
    ├── oxc-parser-binding/{package.json,parser.linux-loong64-gnu.node}
    ├── oxc-transform-binding/{package.json,transform.linux-loong64-gnu.node}
    ├── rolldown-binding/{package.json,rolldown-binding.linux-loong64-gnu.node}
    └── lightningcss-binding/lightningcss.linux-loong64-gnu.node
```

### vendor SHA-256

| 文件 | SHA-256 |
|---|---|
| `wg-easy-v15.4.0.tar.gz` | `87aa90b91bd22309d4c4a27e49a340a243582821e3964b6a878e865e88efc05c` |
| `pnpm-11.21.0.tgz` | `87237d37eadb79dc626a0576eb3a52d23d70422c323ae5e00fc05c91f4323780` |
| `libsql/index.node` | `51a33acb8bf898efe5dcff16adc1b74b6448ed9883a719f439ecd5ce29570650` |
| `oxc-parser-binding/parser...node` | `1db1640cff937736cf27a7b4394e0040a7f9361ad4d8158e511f01e203093187` |
| `oxc-transform-binding/transform...node` | `c54826133550648edd7f74b54d5d308820dd5163dd3c05b7cdf41e338dd493c5` |
| `rolldown-binding/rolldown...node` | `6cdaba3c15d543b949b54f2e5c0a1eaa977c5ecf852f075e1cef7c5c7c3a50f0` |
| `lightningcss-binding/lightningcss...node` | `3038e2b1321a40f3fc2dcf715eabc92a1cd16f37aa7367b01836613ebdb3bb73` |

- 源码：`https://codeload.github.com/wg-easy/wg-easy/tar.gz/refs/tags/v15.4.0`。
- pnpm：`https://registry.npmjs.org/pnpm/-/pnpm-11.21.0.tgz`。
- 4 个 loong64 绑定来自 `https://registry.loongnix.cn:5873`（`@libsql/linux-loong64-gnu@0.5.13`、`@oxc-parser/binding-linux-loong64-gnu@0.152.0`、`@oxc-transform/binding-linux-loong64-gnu@0.152.0`、`lightningcss-linux-loong64-gnu@1.33.0`）；Rolldown 绑定为 `@rolldown/binding-linux-loong64-gnu@1.2.3`。
- 版本错配（libsql JS 0.5.29 / native 0.5.13；oxc JS 0.141 / binding 0.152）已实测可用；升级时需重跑构建与 DB 冒烟。

## 补丁

`patches/0001-replace-argon2-with-hash-wasm.patch`：

1. `src/server/utils/password.ts` 的 3 处调用：
   - `isPasswordValid()` 的 `hash === null` 分支：`argon2.verify(DUMMY_HASH)` → `argon2Verify`；
   - `isPasswordValid()` 正常分支：`argon2.verify(hash)` → `argon2Verify`；
   - `hashPassword()`：`argon2.hash()` → `argon2id()`。
2. `hash-wasm` 参数：argon2id，`m=65536, t=3, p=4`，16 字节随机盐，32 字节输出，PHC 编码。
3. `package.json`：删除 `argon2`，加入 `hash-wasm: 4.12.0`。

原因：`argon2@0.45.1` 无 loong64 预编译；源码 `node-gyp` 可编过且 hash/verify 正确，但进程退出时 `free(): invalid pointer`/段错误（0.40.2 同样）。hash-wasm 为纯 WASM，实测 rc=0。

## 构建

```bash
cd /build/appimages/wg-easy
docker build \
  -t yunixintel/wg-easy:loong64 \
  -t yunixintel/wg-easy:24.10-la5 .
```

Dockerfile 要点：

- 构建阶段：解包 v15.4.0 源码 → 打补丁 → pnpm 11.21.0 `install --ignore-scripts --no-frozen-lockfile` → 放入 5 个 loong64 绑定 → `pnpm build` → 把 `libsql/index.node` 注入 `.output/server/node_modules/libsql/`（Nitro 只复制包、不复制原生模块）。
- 运行阶段：基于同一 `yunixintel/node:24.22.1`；安装 `wireguard-tools iproute iptables procps-ng`。**openEuler 必须保留 EPOL 源**，`wireguard-tools` 只在 EPOL 中。
- `ENTRYPOINT /usr/local/bin/docker-entrypoint.sh`：`mkdir -p /etc/wireguard`、`export LIBSQL_JS_DEV=1`、检查 `index.node`，然后 `exec node server/index.mjs`。不修改宿主网络或防火墙。

## 运行

```bash
docker run -d --name wg-easy --restart unless-stopped \
  -p 51820:51820/udp -p 51821:51821/tcp \
  -v etc_wireguard:/etc/wireguard \
  -v /lib/modules:/lib/modules:ro \
  --cap-add NET_ADMIN --cap-add SYS_MODULE \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  -e INSECURE=true \
  -e INIT_ENABLED=true -e INIT_USERNAME=admin -e INIT_PASSWORD='change-me' \
  -e INIT_HOST=vpn.example.com -e INIT_PORT=51820 \
  -e DISABLE_IPV6=true \
  yunixintel/wg-easy:loong64
```

- `NET_ADMIN` 必需；`SYS_MODULE` + `/lib/modules` 用于容器内 `modprobe wireguard`（宿主已 `modprobe wireguard` 时可去掉）。
- `NET_RAW` 仅 Podman 需要；`/dev/net/tun` 仅 AmneziaWG/用户态 WireGuard 需要。
- 宿主需放行 51820/udp（以及按需的 51821/tcp）：`firewall-cmd --permanent --add-port=51820/udp`。本机未装 `docker compose` 插件，可直接用上面的 `docker run`。
- 直连 HTTP 时设 `INSECURE=true`；公网建议反代并保持 `false`。默认关闭 IPv6。
- 数据卷 `/etc/wireguard` 保存 `wg-easy.db` 与 `wg0.conf`，必须持久化。

## 测试（2026-10-24，A 机）

为避免修改宿主网络/防火墙，测试使用 bridge 网络、不发布端口、`wg-quick` 用桩程序（`wg genkey/pubkey` 用真实 `/usr/bin/wg`），在容器内用 `node fetch` 访问 51821。

| 项 | 结果 |
|---|---|
| DB 迁移 | `Database Migration complete` |
| 初始用户（`INIT_*`） | `users_table` 查询返回 `admin` |
| 配置生成 | `/etc/wireguard/wg0.conf` 667 B，`10.8.0.1/24`、`ListenPort 51820` |
| 新卷首次访问 | `GET /` → 302，`Location: /setup/1`；`/setup/1` → 200 |
| 配置后访问 | `GET /` → 302，`Location: /login` |
| 持久化 | 重启容器后 DB SHA-256 不变（`615c8915…f8c7ec6`），DB/conf 仍在 |
| healthcheck | `healthy`（重启前后均通过） |

**未验证**：真实内核 `wg-quick up wg0`、客户端握手、`ping 10.8.0.1`、经隧道访问外网、宿主 firewalld/NAT。发布前需在测试机按上述 `docker run` 加载模块并完成端到端验收。

## 已知限制

- 镜像基于已验证的绑定组合，不建议单独升级 libsql/oxc/lightningcss；升级需重跑构建、DB 迁移与启动冒烟并更新 SHA。
- AmneziaWG 未启用：Loongnix 无 `amneziawg` 内核模块；用户态 `amneziawg-go` 需 Go 1.25 + `/dev/net/tun`，留待二期。
- IPv6 默认关闭；上游的 IPv6 子网/sysctls 待实测后再加。
- AGPL-3.0：分发镜像需提供对应源码与上述补丁。
