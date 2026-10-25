# wg-easy 15.4.0 loong64 网络功能验证报告

- 日期：2026-10-25
- 环境：Host A（`loongson-lab`，Loongnix 6.6.52-loongarch64，Docker 26.1.5）；镜像 `yunixintel/wg-easy:loong64`（v15.4.0，Node 24.22.1）
- 方法：所有测试在 Docker 容器/网络命名空间内完成，使用端口 14200–14204；未修改宿主 firewalld/路由，未重启 A。IPv6 测试临时 `modprobe ip6table_nat`，结束后已 `rmmod`，测试容器/网络/卷已全部清理。
- 结论：4 项功能 PASS；IPv6 内部 PASS，外网 IPv6 受 Docker 限制为 BLOCKED；AmneziaWG 用户态路线构建与端到端 PASS，但镜像尚未打包。

## 结果总览

| # | 项目 | 状态 | 结论 |
|---|---|---|---|
| 1 | 隧道访问/转发/NAT | **PASS** | 握手、容器 HTTP、跨容器转发、外网访问均通 |
| 2 | IPv6 | **PASS（内部）/ BLOCKED（外网）** | wg0 获得 IPv6，客户端可访问；需内核 `ip6table_nat` + 容器 IPv6 转发 |
| 3 | AmneziaWG | **PASS（用户态 PoC）** | Go 1.25 构建成功，AWG 握手/数据/外网均通；镜像打包与健康检查待修 |
| 4 | 重启与数据保留 | **PASS** | DB/配置/客户端保留；客户端在发送流量后约 15 s 自动重新握手 |
| 5 | 宿主 firewalld/NAT | **PASS（只读）** | 51820/udp、51821/tcp 均未放行；Docker 发布端口会绕过 public zone |

## 1. 经隧道访问外网/转发（PASS）

测试拓扑：默认 bridge 上 `wgv-server`（wg-easy，NET_ADMIN，宿主已 `modprobe wireguard`）+ `wgv-client`（同镜像，NET_ADMIN，`wg-quick` 客户端）；HTTP 后端为同 bridge 的独立容器。

- 握手：服务端 `wg show` 显示 `latest handshake: 2 seconds ago`，`transfer: 884 B received, 860 B sent`；客户端对称。
- 隧道内 HTTP：`curl http://10.8.0.1:8080/` → `HELLO-WG-SERVER-8080`（服务端 wg0=10.8.0.1/24，客户端 10.8.0.2/32）。
- 转发+NAT（关键证据）：客户端与后端同在 172.17.0.0/16，原本会走直连；测试中在客户端加 `ip route add 172.17.0.7/32 dev wg0` 强制走隧道。后端看到的源地址为 **172.17.0.4（服务端 eth0）**，而非 10.8.0.2，证明经历了转发与 wg-easy 的 MASQUERADE；`iptables -t nat -L POSTROUTING -nv` 中 `-s 10.8.0.0/24 -o eth0 MASQUERADE` 计数 3→5；HTTP 返回 `HELLO-VIA-WG-NAT`。
- 外网：客户端 `curl http://1.1.1.1` → 301，`https://example.com` → 200（DNS 走隧道到 192.168.8.1），eth0 MASQUERADE 计数同步增长。结论：宿主 IPv4 NAT 与 Docker 出站策略允许，外网访问可用。
- 生产注意：wg-easy 的 MASQUERADE 只针对默认路由接口；若服务端再接额外 bridge（测试中的 eth1/eth2），需自行补对应 `-o ethX MASQUERADE`。常规单网络部署不涉及。
- 测试细节：`INIT_HOST` 启动时填的是预估值，实际容器 IP 为 172.17.0.4，随后通过 `/api/admin/userconfig` 改为真实 IP；生产应填公网域名/固定地址。客户端容器内 `wg-quick` 写 `net.ipv4.conf.all.src_valid_mark` 被内核拒绝（值已由 Docker `--sysctl` 设为 1），测试用去掉该行的副本启动；真实手机/PC 客户端不受此限制。

## 2. IPv6（内部 PASS，外网 BLOCKED）

- Docker 默认 bridge 禁用 IPv6，必须新建 `--ipv6` 用户网络。测试网络：`172.31.0.0/24` + `fd00:6::/64`，服务端 `fd00:6::2`，客户端 `fd00:6::3`。
- 首次以 `DISABLE_IPV6=false` 启动**直接失败**：`wg-quick up wg0` 在 PostUp 执行 `ip6tables -t nat ...` 时报 `can't initialize ip6tables table 'nat': Table does not exist`，wg-easy 抛 `unhandledRejection` 且 wg0 未建立。宿主模块存在但未加载；`modprobe ip6table_nat` 后重启即正常。**镜像默认 `DISABLE_IPV6=false`，这是生产启动硬门槛。**
- 正常后：wg0 获得 `10.9.0.1/24, fdcc:ad94:bacf:61a5::1/112`；客户端获得 `::2/128`；`curl http://[fdcc:ad94:bacf:61a5::1]:8081/` → `HELLO-IPV6-WG`，握手 2 s 前。
- 转发：容器 netns 默认 `net.ipv6.conf.all.forwarding=0`，容器内 `sysctl -w` 被拒绝；需 Docker `--sysctl net.ipv6.conf.all.forwarding=1`。加上后客户端经隧道访问另一容器 `[fd00:6::4]:8087` → `HELLO-IPV6-FORWARD-NAT`，`ip6tables -t nat POSTROUTING` 的 `fdcc:...::/112 → ::/0 MASQUERADE` 计数 2 packets/160 B，后端看到源为服务端 `fd00:6::2`。
- 限制：Docker 只分配 ULA（fd00::/8），无全局 IPv6 前缀，也没有可用的 IPv6 出站 NAT；**经隧道访问公网 IPv6 未验证/不可用**。宿主虽有 2409:.../64，但未做前缀委派，不在本次范围内。
- 另：`net.ipv4.conf.all.src_valid_mark`、`net.ipv6.conf.all.forwarding` 在容器内 `sysctl -w` 均返回 permission denied；Docker `--sysctl` 可设置，compose 必须显式声明。

## 3. AmneziaWG（用户态路线 PASS，PoC）

- 内核：`modinfo amneziawg` → `Module amneziawg not found`；镜像内无 `awg/awg-quick/amneziawg-go`。
- 构建（均在 A 机，非镜像内）：
  - `amneziawg-go` master（`0.0.20250522`），`go.mod` 要求 **go 1.25.0**；宿主 Go 1.24.4 通过 `GOTOOLCHAIN=auto` 自动下载 go1.25.0，`CGO_ENABLED=0 go build` 得静态 3.4 MB 二进制，**27 s**。
  - `amneziawg-tools`（`v3.1.20260812`）`make` **4 s**，产物 `wg` 安装名 `awg`，`wg-quick/linux.bash` 安装名 `awg-quick`。两者在 loong64 镜像内均可执行。
- wg-easy 集成：`EXPERIMENTAL_AWG=true OVERRIDE_AUTO_AWG=awg`，挂载三个二进制，`--device /dev/net/tun`、`NET_ADMIN`、`DISABLE_IPV6=true`。启动仍失败于 `awg-quick: '/etc/amnezia/amneziawg/wg0.conf' does not exist`，因为 awg-quick 默认配置目录是 `/etc/amnezia/amneziawg/`，而 wg-easy 写 `/etc/wireguard/wg0.conf`；容器内建软链后正常。
- 结果：服务端 `awg show` 显示 `Jc=7 Jmin=10 Jmax=1000 S1=128 S2=56 H1..H4`，`awg-quick` 正确回退用户态 `amneziawg-go`；客户端 AWG 配置含同样参数并握手成功；`curl http://10.8.0.1:8080/` → `HELLO-AMNEZIAWG-USERSAPCE`；外网 `http://1.1.1.1` → 301。
- 待修问题：本次 PASS 仅证明用户态路线可行，不改变首发范围；打包与性能评估完成前仍不建议随首发提供 AWG。镜像健康检查固定为 `wg show | grep -q interface`，用户态 TUN 下标准 `wg show` 看不到接口，容器会变为 unhealthy（实测 FailingStreak=1）；应改为 `awg show` 或按 `WG_EXECUTABLE` 选择。另 `awg-quick` 客户端同样触发 `src_valid_mark` 写入，测试中用 Docker `--sysctl` + 去 sysctl 行副本解决。用户态性能明显低于内核模块，未做吞吐压测。

## 4. 重启与数据保留（PASS）

- 重启前：`/etc/wireguard/wg-easy.db` SHA-256 `032b42c4…279eb`，`wg0.conf` `16f77344…dedaa`；客户端配置与 `c1`（10.8.0.2）已生成。
- `docker restart wgv-server` 后：两项 SHA-256 **完全一致**，卷 `wgv-data1` 保留（`/var/lib/docker/volumes/wgv-data1/_data`）；重新登录 API 后客户端列表仍有 `c1`；重新下载的客户端配置与重启前 `diff` 完全一致。
- 重连：客户端设置 `persistent-keepalive 25`，但服务端重启后前 40 s 无新握手（仅靠 keepalive 不足以让对端发现会话失效）；客户端首次发送数据后约 15–25 s 自动重新握手（18:22:44 完成，距重启约 70 s），随后 `curl http://10.8.0.1:8080/` → `HELLO-AFTER-RESTART`，服务端 `wg show` 恢复握手与计数，健康状态 healthy。
- 说明：生成的客户端配置默认 `PersistentKeepalive = 0`；建议生产默认 25 s。WireGuard 服务端重启不会主动推送重连，需客户端数据/重协商触发。

## 5. 宿主 firewalld/NAT（只读检查，PASS）

- `firewall-cmd --state`：running；默认 zone `public`，接口 `enp0s3f0`（192.168.8.8/24）。
- `public`：services `dhcpv6-client ssh`；ports `80,443,2222,3001,3389,4533,8096,8443/tcp`；`forward: yes`，`masquerade: no`。
- `docker` zone：active，`target: ACCEPT`，接口 `docker0` + 所有 `br-*`，`forward: yes`，`masquerade: no`。
- **51820/udp、51821/tcp 在 public 与 docker zone 均未放行**（`--query-port` 全部 no）。
- 发布端口实测：容器 `-p 14204:8080`，从局域网 Windows 客户端访问 `http://192.168.8.8:14204/` → `PUBLISHED-OK`。说明 Docker 的 DNAT 规则会绕过 firewalld public zone；这既解释了“未放行也能通”，也是安全风险（UI 端口会直接暴露）。
- 生产建议：
  - 内核模块模式：放行 `51820/udp`；`51821/tcp` 仅内网/反代并上 HTTPS，或改绑 127.0.0.1 由反代转发。
  - 宿主要先 `modprobe wireguard`（容器内带 `SYS_MODULE + /lib/modules:ro` 时也可由容器加载）；IPv6 需 `modprobe ip6table_nat`。
  - 若用 host 网络模式，还需 `firewall-cmd --add-masquerade` 与 IPv4/IPv6 forward；bridge 模式由容器内 iptables 完成 NAT，无需宿主 masquerade。
  - 不要假设“firewalld 没放行就不通”；以实际端口探测为准。

## 剩余风险与建议

1. **IPv6 启动硬失败**：镜像默认 `DISABLE_IPV6=false`，宿主未加载 `ip6table_nat` 时 wg-easy 无法启动。发布前应预加载模块、在 entrypoint 内 `modprobe`（镜像需装 kmod），或默认 `DISABLE_IPV6=true` 并文档说明。
2. **IPv6 转发未自动开启**：必须显式 `--sysctl net.ipv6.conf.all.forwarding=1`；否则只能访问服务端 wg IPv6 地址，不能转发到其他容器/网段。
3. **AmneziaWG 未打包**：需把 `awg`、`awg-quick`、`amneziawg-go`（静态）放进镜像，并在 entrypoint 建 `/etc/amnezia/amneziawg/wg0.conf` 软链；健康检查改为 `awg show`；确认 /dev/net/tun 与 NET_ADMIN。用户态性能需另做压测。
4. **健康检查误判**：AWG 用户态模式下 `wg show` 恒空，容器会被标 unhealthy。
5. **Docker/firewalld 绕过**：发布端口绕过 public zone，必须显式做访问控制；UI 端口不要直接暴露公网。
6. **端点地址**：`INIT_HOST` 必须是客户端可达的固定域名/IP，容器 IP 会变化；本次因预估 IP 不符通过 API 修正。
7. **外网 IPv6**：Docker ULA 网络无全局前缀，公网 IPv6 over WG 未验证；如需要应使用 macvlan/前缀委派或 NAT66，另行评估。
8. **测试客户端 sysctl**：容器内 `wg-quick` 写 `src_valid_mark` 被拒，需 Docker `--sysctl` 或补丁；真实终端不受影响，但自动化测试需注意。

## 清理状态

测试容器、网络、卷已删除；`ip6table_nat/ip6_tables` 已卸载；firewalld 未改动；宿主端口 14200–14204 已释放。镜像、README 及其他文档未改动。
