# 龙芯 3A6000 KVM 翻盘计划

## 1. 根因一句话

qemu 10.0.2 的 EIOINTC/MSI-X 中断投递与 6.6 客户机 virtio 驱动不兼容：中断已置位但 vCPU 收不到或清不掉，驱动等 ctrl 回复等到 rcu stall。

证据链：① `disable-legacy=on` 才出 eth0、60 秒后 PC 定在 `eiointc_irq_dispatch`，说明切到 MSI-X 后投递已死；② `kernel-irqchip=off` 仍 stall，说明不是 KVM irqchip 加速问题，是用户态 EIOINTC 模型本身缺陷；③ `pci=nomsi` 盘网全死，说明 6.6 客户机在 virt 平台上无可用中断回退路径。

## 2. 翻盘路线（按性价比排序）

A. 网卡降级 INTx 三件套：改 qemu 网卡参数，`msix=off`＋`mq=off`＋`vectors=2`＋`acpi=off`逐位二进制组合验证，客户机不动。验证标准：eth0 出现且 ping 网关 10 分钟无 stall。预计耗时：0.5 天。

B. 宿主 qemu 降级到 8.x/9.x：Debian snapshot 取旧包或自编，客户机/cmdline 不动。验证标准：同一镜像＋`disable-legacy=on` 跑 30 分钟无 stall。预计耗时：1–2 天。

C. 客户机升 6.12：OpenWrt 跟 main 切 6.12，或把子代理定位的 irqchip/KVM 那几个 commit backport 到 6.6。验证标准：同 qemu 10 下 stall 消失。预计耗时：3–5 天。

D. 维持现状：KVM 封存，容器验机为主（nspawn 路已走通）。验证标准：全部待验用例在容器里跑通。预计耗时：0 天。

## 3. 每条第一条可执行命令

A. `qemu-system-loongarch64 -M virt -cpu la464 -accel kvm -device virtio-net-pci,netdev=n0,disable-legacy=off,msix=off,mq=off,vectors=2 -netdev user,id=n0 -drive file=openwrt-root.img,if=virtio -nographic`

B. `apt source qemu=1:8.2.* && cd qemu-* && dpkg-buildpackage -b -uc -us`（或 snapshot.debian.org 取 `qemu-system-misc` 旧包直接装测试机）

C. `git -C openwrt cherry-pick <irqchip/KVM commits> && make target/linux/clean && make target/linux/compile -j$(nproc)`

D. `systemd-nspawn -D openwrt-rootfs -- /sbin/init`（容器验机，不经过 KVM）

## 4. 先干哪个

先干 A，半天见分晓；A 不通转 B，2 天内定去留；B 症状一字不差复现则直接落到 D，不再纠缠；C 仅当 A/B 把问题定位到纯客户机驱动侧时再投。

失败判据：A 任一组合仍 60 秒级 stall 或 probe -22；B 换 8.x/9.x 现象完全复现；触发任一即宣布此路不通，止损转下一条。全程只用测试镜像，不起生产虚机、不改宿主配置。

## 2026-10-18 路线 A 实测结果（四组合全败，附新证据）

实测（qemu 10.0.2 + 自编 6.6.144 客户机）：

| 组合 | 结果 |
|---|---|
| `disable-legacy=on,msix=off,mq=off` | qemu 报 `Property 'virtio-net-pci.msix' not found`（无此属性） |
| `disable-legacy=on,mq=off,vectors=2` | eth0 起，**62s rcu stall** |
| 上一行 + `modern-pio-notify=on` | eth0 起，**62s stall** |
| `-M virt,acpi=off` + 同网卡参数 | eth0 起，**62s stall** |
| **纯磁盘（无网卡）** | 100s **零 stall** ← 证明网卡是触发源 |
| `vectors=1` | 网卡 probe **-28 (ENOSPC)**，无 eth0，无 stall |

新证据：客人日志两行 `virtio-pci 0000:00:01.0: of_irq_parse_pci: failed with rc=-22`（磁盘与网卡都报）——PCI 中断映射在同一 DT 下解析失败。磁盘仍能用（走 MSI-X 轮询队列），网卡一启用 MSI-X 就把 EIOINTC 带进坏状态，定时器中断停发。

结论：A 路线（网卡侧降级）**判死**，原因是 PCI 中断映射/投递链在 qemu 10 + 6.6 组合下本身有问题，不是向量数量能绕过的。

下一步按计划转 **B：宿主 qemu 降级到 8.x/9.x**（需 1–2 天，未启动）。若 B 复现同症状，直接落 D（KVM 封存，容器验机为主）。

## 2026-10-18 路线 B 实测结果（qemu 9.2 自编，同样复现 → 落 D）

- 本机无现成旧 qemu 包（Loongnix multiversion 空、20 仓库太老），改为**自编 qemu 9.2.0**（`--target-list=loongarch64-softmmu`，装 `/opt/qemu9`，系统 qemu 不动，可回退）。
- 结果一：`disable-legacy=on` 现代网卡 —— eth0 起，**63 秒 rcu stall**（与 qemu 10 一字不差）。
- 结果二：过渡版网卡 —— **不再报 probe −22**（这点比 qemu 10 好），eth0 起，**同样 63 秒 stall**。
- 结论：stall 与 qemu 版本无关，指向客人侧 EIOINTC/MSI-X 驱动与 timer 中断的交互缺陷。按判据 **B 判死**，**落到 D：KVM 封存，容器验机为主**。
- 唯一未试路径是 C（客人升 6.12 / backport irqchip 修复），成本 3–5 天且不确定；暂不投。
- `/opt/qemu9` 可留作以后排查（不占系统路径）；测试镜像与 vmlinux 仍在 `/var/tmp`。
