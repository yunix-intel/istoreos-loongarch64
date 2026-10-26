# OMV Gate 0：O-01~O-03 基线审计、依赖闭包与 QEMU TCG Spike

日期：2026-10-26（CST）  
状态：O-01/O-02 只读审计完成；O-03 未执行，标记 **BLOCKED**  
范围：仅 O-01~O-03；O-04~O-09 不在本文件内  
关联：[NEXT-PLAN](../../NEXT-PLAN.md)、[GAPS](../../GAPS.md)、[ROADMAP](../../ROADMAP.md)、
[PHASE-2-FULL-VERIFICATION](../PHASE-2-FULL-VERIFICATION.md)

> `docs/OMV-FEASIBILITY.md` 当前不存在。本文件暂代 O-01~O-03 的交付，
> 待 O-09 再汇总进 OMV-FEASIBILITY。  
> 本次审计未修改 Host A 的 apt 源、未安装/卸载包、未写任何磁盘、未启动完整 QEMU 安装。
> 仅执行了一次 15 秒、512MiB/1vCPU、无磁盘的 edk2 固件冒烟。

## 0. 结论摘要

| 项 | 结论（仅限三档） | 一句话依据 |
|---|---|---|
| **O-01** 目标版本与基线 | **证据不足** | OMV 7 明确不可行；OMV 8 是唯一候选，但上游、Debian、OMV 仓库均无 loong64 交付物，无法证明可安装 |
| **O-02** 依赖闭包 | **不可行** | OMV 8 as-is 有 3 个硬阻塞：`php-pam`、`openmediavault-salt`+Salt 3008、`netplan.io`；OMV 7 另有 `cpufrequtils` 且已 EOL |
| **O-03** QEMU TCG spike | **证据不足** | QEMU、edk2、Loongnix 25 ISO 均在位；缺 ≥16GiB 可写 scratch，且 O-02 已判定 OMV 安装会在依赖处失败；未运行完整 spike，状态 BLOCKED |

**Gate 0 当前建议**：只保留 OMV 8（Synchrony）作为唯一候选；在补齐 loong64 的
`php-pam`、Salt 3008 栈、`netplan.io`/`libnetplan1` 之前，不进入 O-04 highstate，
也不要把 OMV 7 作为回退路线。

---

## 1. 审计方法与红线

### 1.1 只读边界

| 约束 | 执行情况 |
|---|---|
| 不改仓库其它文件 | 仅新增本文件 |
| 不碰 Host A 内部数据盘 | 未读未写 `/dev/sda`、`/mnt/Data`、`/data`；未碰 `/opt/casaos-p3` |
| 不写 `LOONGSONISO` U 盘 | 仅 `blkid`/`isoinfo`/`tar` 只读读取 `/dev/sdb` |
| 不直接加 bookworm 源 | 未改 `/etc/apt/sources.list*`；仅使用 Loongnix 25 现有缓存与 OMV 仓库元数据 |
| 不下载大文件 | 未下载 OMV ISO、Loongnix ISO、任何 rootfs；只抓取 Release/Packages/InRelease/key 等小元数据 |
| 不伪造运行 | 未运行完整 QEMU 安装；固件冒烟结果单独标注为“仅到 PEI 阶段” |

> 备注：为核对 maintainer script，曾尝试下载 8.5MB 的 `openmediavault_8.5.12-1_all.deb`，
> 在 1.6MB 处超时；该半成品未使用、未安装、未进入结论。其余下载均为
> Release/Packages/InRelease/key 等小元数据。

### 1.2 Host A 基线采集命令（只读）

```bash
ssh loongson-lab 'cat /etc/os-release; uname -a; getconf PAGE_SIZE; getconf LONG_BIT'
ssh loongson-lab 'ldd --version | head -1; systemctl --version | head -1'
ssh loongson-lab 'dpkg --print-architecture; apt-cache policy; cat /etc/apt/sources.list'
ssh loongson-lab 'efibootmgr; ls /boot; dpkg -l | grep -E "grub-efi|systemd|php|qemu"'
ssh loongson-lab 'free -h; nproc; uptime; df -h / /build /tmp; lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT'
```

### 1.3 证据锚点

| 证据 | 位置/URL | SHA256（抓取时） |
|---|---|---|
| OMV 7 Release | `https://openmediavault.github.io/packages/dists/sandworm/Release` | `fe35e6fcc0deef3965ef59181e8a589070f5b15601a5d54a414ff0577bfcbc48` |
| OMV 8 Release | `https://openmediavault.github.io/packages/dists/synchrony/Release` | `fad151f57b7ac19a1880d9095a754cc176735cd66f6a27dd547bce0f03e4790d` |
| OMV 7 Packages (amd64 索引) | `.../dists/sandworm/main/binary-amd64/Packages.gz` | `cd806ea6e0829dc33de69a7275e7df27a12ab6a7a7feecb6454228652647b85e` |
| OMV 8 Packages (amd64 索引) | `.../dists/synchrony/main/binary-amd64/Packages.gz` | `83dd43470735e8137bb65bca2edb30a8f17ad0a6fae2800d4948c4bf3b2e35b9` |
| OMV 8 InRelease | `https://packages.openmediavault.io/dists/synchrony/InRelease` | `05faa802a4360c2f061bc4fa0406fe24898005e29cf6d382ff75664816777545` |
| OMV archive key | `https://packages.openmediavault.io/archive.key` | `ffa18c6c27dccd41656b6a71ca2ba042c3028077cb099dbca05fd1fd245906a3` |
| Debian 12 Release | `https://deb.debian.org/debian/dists/bookworm/Release` | `abcf5882746e0f68171f41adbb4ac01b74b49d62d203379befb9265804311a4f` |
| Debian 13 Release | `https://deb.debian.org/debian/dists/trixie/Release` | `ed56aac47e7911e65ee63aae8d67e29f20e023f840e49f8ed037043a33de138a` |
| edk2 loongarch64 code | `/opt/qemu9/share/qemu/edk2-loongarch64-code.fd` | `edd5a67fe50f7597faecb2fe67c5733b9a31b0b345a2127c3c358a5737446ef7` |
| QEMU 9.2 二进制 | `/opt/qemu9/bin/qemu-system-loongarch64` | `65a439f99965474e7b7b6b698b3c7f1c7a29600f3e8d256d48afc428b9bd68e2` |

OMV archive key 指纹（`gpg --show-keys`）：

```text
pub   rsa4096 2016-07-12 [SC]
      D675 06C8 78E0 8A94 FD7E  0094 2486 3F0C 716B 980B
uid   OpenMediaVault.org (OpenMediaVault packages archive) <packages@openmediavault.org>
```

`InRelease` 的 RSA 签名由该密钥验证为 Good signature（另一个 DSA 签名未导入对应公钥，
不影响 apt 使用已导入的 archive key）。

---

## 2. O-01：目标版本与基线审计

### 2.1 Host A 实测基线

| 项 | 实测值 | 采集方式 |
|---|---|---|
| 发行版 | Loongnix GNU/Linux 25，`VERSION_ID=25`，`VERSION_CODENAME=loongnix-stable`，BUILD_ID `20260803T191323` | `/etc/os-release` |
| 架构 | `loongarch64`，`dpkg --print-architecture = loong64` | `uname -m`、`dpkg` |
| CPU | Loongson-3A6000-HV，8 线程（4 核 × 2），2.5GHz，LSX/LASX | `lscpu` |
| 内存 | 31GiB RAM + 8.8GiB swap | `free -h` |
| 内核 | `6.6.52-loong64`（Loongnix 6.6.52-1.11，2026-07-23） | `uname -a` |
| glibc | `2.41-13.lnd.1` | `ldd --version` |
| systemd | `257.7-1.lnd.1` | `systemctl --version` |
| 页大小 | **16384**（16KiB） | `getconf PAGE_SIZE` |
| PHP | 未安装；仓库候选 `php-fpm 2:8.4+96`（`8.4.16-1~deb13u1`） | `apt-cache policy` |
| apt | Loongnix 25 仓库（`pkg.loongnix.cn/loongnix/25`）+ `app.loongapps.cn`；**无 Debian suite** | `/etc/apt/sources.list*` |
| 启动 | UEFI（`/sys/firmware/efi` 存在）+ GRUB 2.12 loong64；`Boot0005* Loongnix-25 ... \EFI\Loongnix-25\grubloongarch64.efi` | `efibootmgr` |
| Secure Boot | 未采集（`mokutil` 未安装）；OMV 文档建议关闭 Secure Boot | `efibootmgr`/`mokutil` |
| 磁盘 | `nvme0n1` 238.5G；`/` 37G（13G 可用）；`/build` 37G（4.8G 可用）；`/tmp` 16G tmpfs；`/dev/sda` 1.9T 为用户数据盘，禁止触碰 | `df`/`lsblk` |

### 2.2 OMV 7 vs OMV 8 仓库事实

| 项 | OMV 7（Sandworm） | OMV 8（Synchrony） |
|---|---|---|
| OMV 核心包 | `openmediavault 7.7.24-7`，`Architecture: all` | `openmediavault 8.5.12-1`，`Architecture: all` |
| 仓库 `Architectures:` | `i386 amd64 armel armhf arm64` | `amd64 arm64` |
| 仓库中的 loong64 索引 | **无**（`binary-loong64/Packages.gz` 返回 404） | **无**（同上） |
| 仓库包组成 | 29 个 `all` + 2 个 `amd64`（`onedrive`、`php-pam`） | 29 个 `all` + 5 个 `amd64`（`onedrive`、`php-pam`、`openmediavault-salt`、`salt-common`、`salt-minion`） |
| 核心 Salt 依赖 | `salt-minion (>= 3006.0)`；OMV 仓库为 `3006.0+ds-1+240.1`，`all` | `openmediavault-salt (>= 8.1.0)`；该包 `amd64`，依赖 `salt-minion (>= 3008.1)`；Salt `3008.1` 为 `amd64` |
| 核心 PAM 依赖 | `php-pam 2.2.4-1+deb12u1`，`amd64` | `php-pam 2.2.5-1+deb13u1`，`amd64` |
| 生命周期 | Debian 12；**EOL Jun 2026**（发布 Mar 2024） | Debian 13；**Stable Dec 2025** |
| 官方支持架构 | 文档列 AMD64/i386/ARMv7/ARMv8 | 文档列 AMD64/i386/ARMv7/ARMv8；**无 LoongArch** |

证据：OMV 仓库 [sandworm Release](https://openmediavault.github.io/packages/dists/sandworm/Release)、
[synchrony Release](https://openmediavault.github.io/packages/dists/synchrony/Release)、
两个 `Packages.gz`；OMV 文档
[Releases](https://docs.openmediavault.org/en/latest/releases.html)、
[Prerequisites](https://docs.openmediavault.org/en/latest/prerequisites.html)。

> 说明：OMV 仓库 `Architectures:` 只列二进制架构，`arch:all` 包会出现在
> `binary-amd64/Packages` 索引中；没有 `binary-all` 索引不代表没有 `all` 包。
> 关键是：**OMV 仓库没有 `binary-loong64` 索引，也没有任何 loong64 二进制包。**
>
> 更严格地说：纯 loong64 apt 默认只请求 `binary-loong64/Packages`；该索引 404，
> 仓库 Release 又不声明 loong64，因此连 `openmediavault` 这个 `arch:all` 包也可能
> 在 `apt-get update` 阶段被跳过。**不得**用 `dpkg --add-architecture amd64` 或
> `[arch=amd64]` 把 amd64 包“伪装”成可用——那会拉入无法在 loong64 上执行的二进制。

### 2.3 Debian 侧基线

| 项 | Debian 12 Bookworm（OMV 7 目标） | Debian 13 Trixie（OMV 8 目标） | Host A（Loongnix 25） |
|---|---|---|---|
| 官方架构列表 | `all amd64 arm64 armel armhf i386 mips64el mipsel ppc64el s390x`，**无 loong64** | `all amd64 arm64 armel armhf i386 ppc64el riscv64 s390x`，**无 loong64** | `loong64` |
| glibc | `2.36-9+deb12u14` | `2.41-12+deb13u4` | `2.41-13.lnd.1` |
| systemd | `252.39-1~deb12u2` | `257.13-1~deb13u1` | `257.7-1.lnd.1` |
| PHP | `php-fpm 2:8.2+93` | `php-fpm 2:8.4+96` | `php-fpm 2:8.4+96`（仓库） |
| 内核 | Debian 6.1 系列（OMV 核心不 pin 内核包） | Debian 6.12 系列（OMV 核心不 pin 内核包） | `6.6.52-loong64` |
| 启动 | BIOS/UEFI + GPT；OMV 官方 ISO 仅 AMD64/BIOS | 同左；官方 ISO 仍仅 AMD64/BIOS | UEFI + GRUB 2.12 loong64 |

补充证据：

- Debian 12/13 Release 的 `Architectures:` 字段均不含 `loong64`；
  Debian ports `sid` 的 Release 也只列 `all alpha hppa hurd-amd64 hurd-i386 m68k
  powerpc ppc64 sh4 sparc64 x32`，同样没有 `loong64`。
- OMV 文档明确写“install openmediavault on an existing **Debian 13** installation”；
  `Prerequisites` 写支持 `AMD64 / i386 / ARMv7+ARMv8`，并写“official ISO image ...
  only supports AMD64 with BIOS mode boot at the moment”。
- Host A 的 Loongnix 25 是 loong64 用户态重建，包版本普遍带 `+deb13u2` 等
  Debian 13 痕迹（如 `nginx 1.26.3-3+deb13u2`、`samba 2:4.22.3+dfsg-4`），
  但它**不是** Debian 官方 suite，不能把“Loongnix 有包”等同于“Debian trixie 有 loong64 包”。

### 2.4 需求矩阵

| 需求 | OMV 7 / Bookworm | OMV 8 / Trixie | Host A 是否满足 | 结论 |
|---|---|---|---|---|
| **LoongArch** | 上游不支持；Debian 12 无 loong64；OMV 仓库无 loong64 | 上游不支持；Debian 13 无 loong64；OMV 仓库无 loong64 | Host 是 loong64 | 两边都缺官方交付物 |
| **glibc** | 2.36 | 2.41 | 2.41 | OMV 8 对齐；OMV 7 目标版本过旧 |
| **systemd** | 252 | 257 | 257 | OMV 8 对齐 |
| **PHP** | 8.2 | 8.4 | 8.4 | OMV 8 对齐；OMV 7 需要 8.2，Loongnix 只有 8.4 |
| **apt** | Debian bookworm 源 | Debian trixie 源 | 仅 Loongnix 源 | 禁止加 bookworm；trixie 包需 Loongnix 提供 |
| **kernel** | Debian 6.1（OMV 不 pin） | Debian 6.12（OMV 不 pin） | 6.6.52-loong64 | 核心包不阻止；模块链留给 O-04/O-05 |
| **bootloader** | BIOS/UEFI；官方 ISO AMD64/BIOS | 同左 | UEFI + GRUB 2.12 | 不能使用 OMV ISO；必须用基础系统安装器 |
| **页大小** | 未在核心依赖中限制 | 未在核心依赖中限制 | 16384 | O-01 记录；ZFS 插件在 O-05 单独判断 |

### 2.5 O-01 结论

| 候选 | 结论 | 证据 |
|---|---|---|
| **OMV 7（bookworm）** | **不可行** | Debian 12 无 loong64；OMV sandworm 仓库无 loong64；核心 `php-pam` 仅 amd64；EOL Jun 2026；PHP 8.2 与 Host 8.4 不匹配 |
| **OMV 8（trixie）** | **证据不足** | glibc/systemd/PHP/页大小与 Host 对齐，但 OMV 文档支持架构不含 LoongArch、OMV synchrony 仓库无 loong64、Debian 13 无 loong64；没有可安装证据 |
| **选定基线** | **OMV 8** | 只保留 OMV 8 作为 Gate 0 候选；不得回退 OMV 7 |

**O-01 总体结论：证据不足。** 版本选择是明确的（OMV 8），但“OMV 8 能在 loong64
上安装”的证据缺失，不能写成“可行”。

---

## 3. O-02：依赖闭包分析

### 3.1 方法

1. 从 OMV 仓库 `Packages.gz` 取 `openmediavault` 的 `Depends` 作为种子。
2. 在 Host A 上用 `python3-apt` 对 **Depends + PreDepends + Recommends** 做 BFS：
   - 每个依赖组按 OR 选项检查，任一项有候选即满足；
   - 记录候选的 `Architecture`（`all` vs `loong64`）；
   - 虚拟包用 `apt-cache depends`/`Provides` 人工核对。
3. 闭包只代表 **Loongnix 25 能提供的 loong64 依赖**，不是“Debian trixie 的 loong64 闭包”
   （因为 Debian 13 根本没有 loong64 官方归档）。同样，闭包基于 OMV 仓库的
   `Packages` 元数据，**不**代表纯 loong64 apt 能直接解析该仓库；后者在
   `apt-get update` 阶段就可能因缺 `binary-loong64` 索引而跳过。
4. 未执行 `apt install`，未添加任何源；纯 `apt-cache` 读取。

### 3.2 闭包规模

| 目标 | 访问节点 | 已解析 `arch:all` | 已解析 `binary-loong64` | 未解析种子 | 硬阻塞（人工核对后） |
|---|---:|---:|---:|---:|---:|
| **OMV 8**（`openmediavault 8.5.12-1`） | 374 | 63 | 306 | 5 | **3** |
| **OMV 7**（`openmediavault 7.7.24-7`） | 366 | 63 | 297 | 6 | **3** |

说明：

- “未解析种子”是 OMV 核心直接依赖但 Loongnix 缓存中无候选的包；其中
  `openmediavault-keyring`、`wsdd-server`（OMV 7 还有 `salt-minion`）在 OMV 仓库中
  有 `arch:all` 包（可手工取 .deb），不算硬阻塞；但纯 loong64 apt 仍可能因仓库
  不声明 loong64 而跳过它们。
- 缺失项全部来自 `Depends`/`PreDepends` 链；**没有发现 Recommends 缺失**。
- 闭包不含 OMV 插件（`openmediavault-*` 插件），插件留 O-05；`onedrive` 是插件依赖，
  不进核心结论。

### 3.3 OMV 8 硬阻塞包

| 包 | 版本 | 被谁需要 | OMV 仓库架构 | Loongnix 25 | Debian 13 | 判定 |
|---|---|---|---|---|---|---|
| `php-pam` | `2.2.5-1+deb13u1` | `openmediavault` 核心 `Depends` | **amd64** | 无 | Debian 无此包 | **硬阻塞**；需按 PHP 8.4 源码重建 |
| `openmediavault-salt` | `8.1.0` | `openmediavault` 核心 `Depends` | **amd64** | 无 | 不适用 | **硬阻塞**；包本身可能可改 all，但依赖 Salt 3008 |
| `salt-minion` / `salt-common` | `3008.1` | `openmediavault-salt` | **amd64** | 无 | Debian 13 无 `salt-minion` | **硬阻塞**；Salt 3008 栈无 loong64 |
| `netplan.io` / `libnetplan1` | `1.1.2-7`（Debian 13） | `openmediavault` 核心 `Depends` | 不在 OMV 仓库 | **无** | 仅 amd64/arm64/armel/armhf/i386/ppc64el/riscv64/s390x | **硬阻塞**；需重建 `libnetplan1` + `netplan.io` |
| `openmediavault-keyring` | `1.0.2-2` | `openmediavault` 核心 | `all` | 无 | 不适用 | OMV 仓库有 all 包（可手工取 .deb），**非阻塞** |
| `wsdd-server` | `2:0.8-5` | `openmediavault` 核心 | `all` | 无 | 不适用 | OMV 仓库有 all 包（可手工取 .deb），**非阻塞** |
| `onedrive` | `2.5.11-1+np1+1.2` | `openmediavault-onedrive` 插件 | amd64 | 无 | 不适用 | 插件非核心；O-05 再判 |

`php-pam` / `openmediavault-salt` / Salt 3008 的仓库元数据：

```text
php-pam 2.2.5-1+deb13u1  Architecture: amd64  Depends: phpapi-20240924
openmediavault-salt 8.1.0 Architecture: amd64 Depends: salt-minion (>= 3008.1)
salt-common 3008.1        Architecture: amd64
salt-minion 3008.1        Architecture: amd64  Depends: salt-common (= 3008.1)
```

> 注：`openmediavault-keyring`、`wsdd-server` 这类 `all` 包即使能从 OMV 仓库
> 手工下载 .deb，也仍要在 loong64 上解析其 Depends；它们不是硬阻塞，但**不能**
> 据此认为 OMV 仓库在纯 loong64 apt 下可用。

### 3.4 OMV 7 硬阻塞包

| 包 | 版本 | 被谁需要 | OMV 仓库架构 | Loongnix 25 | 判定 |
|---|---|---|---|---|---|
| `php-pam` | `2.2.4-1+deb12u1` | `openmediavault` 核心 | **amd64** | 无 | **硬阻塞**；且需 PHP 8.2 头文件，Host 只有 8.4 |
| `cpufrequtils` | `008-2` | `openmediavault` 核心 | 不在 OMV 仓库 | 无（只有 `linux-cpupower 6.6.52-1.11-lnd.15`） | **硬阻塞**；Debian 12 仅有非 loong64 二进制 |
| `netplan.io` | `0.106-2+deb12u1` | `openmediavault` 核心 | 不在 OMV 仓库 | 无 | **硬阻塞**；Debian 12 无 loong64 构建 |
| `salt-minion` / `salt-common` | `3006.0+ds-1+240.1` | `openmediavault` 核心 | `all` | 无 | 可由 OMV 仓库安装；但 Salt 3006 在 Python 3.13 上**未验证**，是风险项 |
| `openmediavault-keyring` / `wsdd-server` | `1.0.2-2` / `2:0.8-5` | 核心 | `all` | 无 | OMV 仓库有 all 包（可手工取 .deb），**非阻塞** |

OMV 7 Salt 的 Python 依赖（`python3-apt`、`python3-dateutil`、`python3-looseversion`、
`python3-jinja2`、`python3-msgpack`、`python3-requests`、`python3-yaml`、`python3-systemd`、
`python3-psutil`、`python3-pycryptodome`、`python3-gnupg`、`python3-zmq`、`python3-distro`、
`python3-jmespath`、`python3-markupsafe`、`python3-packaging`）在 Loongnix 25 均有候选；
但 OMV 7 的目标是 Debian 12 + Python 3.11，Host 是 Python 3.13，兼容性没有证据。
叠加 EOL 与 PHP 8.2 缺口，OMV 7 不作为回退路线。

### 3.5 虚拟包/误报核对

闭包原始输出中的以下“缺失”经 `Provides`/虚拟包核对后**不是**真实缺失：

| 原始缺失 | 实际提供者 |
|---|---|
| `awk` | `mawk` |
| `default-dbus-system-bus` | `dbus` |
| `default-mta` / `mail-transport-agent` | `postfix` |
| `libndr6`、`libsmbldap2` | `samba-libs`（`Provides:`） |
| `perlapi-5.40.1` | `perl-base`（`Provides:`） |
| `php8.4-json` | `php8.4-fpm` / `php8.4-cli` / `php8.4-cgi` |
| `phpapi-20240924` | `php8.4-fpm` / `php8.4-cli` |
| `python3-cffi-backend-api-min` / `-max` | `python3-cffi-backend`（`Provides:`） |

因此 OMV 8 的真实硬阻塞是 3 组：`php-pam`、Salt 3008 栈（`openmediavault-salt` +
`salt-minion`/`salt-common`）、`netplan.io`/`libnetplan1`。

### 3.6 禁止直接加 bookworm 源

**红线：不得在 Host A 或 OMV VM 中添加任何 `bookworm`、`bookworm-backports`、
`bookworm-security` 源。**

原因：

1. Debian 12 官方架构列表**没有 loong64**；bookworm 源里没有可用的 loong64 二进制。
2. 即使强行拉 `arch:all` 包，会引入 glibc 2.36 / systemd 252 / PHP 8.2 的依赖假设，
   与 Host 的 glibc 2.41 / systemd 257 / PHP 8.4 冲突，可能降级 libc 并破坏宿主。
3. OMV 7 已 EOL，不能作为回退；用 bookworm 源只会把“版本错配”变成“系统不可恢复”。
4. 也不得用 `dpkg --add-architecture amd64`、`APT::Architectures` 加 amd64 或
   `[arch=amd64]` 来安装 OMV 仓库的 amd64 包；loong64 内核不能执行 amd64 ELF，
   且会引入一整套 amd64 依赖，结果不可交付。
5. 缺失包的正确处理是：从源码为 loong64 重建（`php-pam`、`netplan.io`/`libnetplan1`、
   Salt 3008 栈），或判定 no-go，而不是混源。

### 3.7 O-02 结论

| 目标 | 结论 | 依据 |
|---|---|---|
| **OMV 8 as-is** | **不可行** | 3 组硬阻塞：`php-pam`、`openmediavault-salt`+Salt 3008、`netplan.io`/`libnetplan1`；OMV 仓库无 loong64 |
| **OMV 7 as-is** | **不可行** | `php-pam`、`cpufrequtils`、`netplan.io` 三个硬阻塞 + EOL + PHP 8.2 不匹配 |
| **可修补性** | **未验证** | `php8.4-dev` 在 Loongnix 可用；`netplan` 的 glib/glib2/yaml/uuid build-deps 部分可用；Salt 3008 无 loong64 包，源码/打包未验证。留给 O-06 |

**O-02 总体结论：不可行（as-is）。** 若继续 Gate 0，只能以“先补齐 loong64 依赖集”
为前提重开 O-02，不能直接进 O-04。

---

## 4. O-03：QEMU TCG spike 方案

### 4.1 现有资产（只读核实）

| 资产 | 位置/版本 | 状态 |
|---|---|---|
| QEMU（推荐） | `/opt/qemu9/bin/qemu-system-loongarch64`，QEMU 9.2.0 | 可用；支持 `virt`、`la132/la464/max`、`virtio-scsi`、`virtio-net-pci`、`virtio-rng-pci` |
| QEMU（系统包） | `/usr/bin/qemu-system-loongarch64`，QEMU 10.0.2 | 可用，但固件目录不完整；优先用 `/opt/qemu9` |
| UEFI 固件 | `/opt/qemu9/share/qemu/edk2-loongarch64-code.fd`（16MiB） | 可用；15s 冒烟已进入 PEI 阶段 |
| UEFI 变量模板 | `/opt/qemu9/share/qemu/edk2-loongarch64-vars.fd`（16MiB） | 可用（可选，持久化启动项时复制） |
| 基础 OS 安装介质 | `/mnt/Data/firmware/loongnix25-20260820.iso`（5.5GB，sha256 `6f607035…83b9`），源自 `/dev/sdb1` | **在位，只读**；Loongnix 25 安装 CD，含 `live/filesystem.squashfs` |
| OMV 官方 ISO | 无 | **不适用**；OMV 文档明确官方 ISO 仅 AMD64/BIOS，不能用于 loong64 |
| 现成 loong64 rootfs | `/build/archive/personal-rootfs-new.tar.gz`、`/build/archive/istoreos-loongarch64-generic-generic-rootfs.tar.gz` | **不可用**；两者都是 iStoreOS/OpenWrt（busybox、`etc/openwrt_release`，personal 为 iStoreOS 24.10.8），无 systemd/apt |
| 可写 scratch | `/build` 仅 4.8GiB 可用；`/tmp` 16GiB tmpfs（内存盘） | **不足/不安全**；完整安装需要 ≥16GiB qcow2 + 日志，建议 ≥20GiB 非数据盘空间 |

### 4.2 缺失与 BLOCKED 判定

| 缺失项 | 影响 | 处理 |
|---|---|---|
| ≥16GiB 可写 scratch（非 `/dev/sda`、`/mnt/Data`、`/data`、`/opt/casaos-p3`） | 无法创建 16GiB qcow2、无法安装 Loongnix 25 | **BLOCKED**；等用户提供/授权 scratch |
| loong64 的 `php-pam`、Salt 3008、`netplan.io`/`libnetplan1` | OMV 8 安装会在依赖处失败 | O-02 已判；O-03 只能记录失败，不能绕过加 bookworm |
| 完整 QEMU 运行窗口 | 未确认 Host A 空闲；审计期间还发生一次重启 | **未执行**；先按第 5 节重新 preflight |
| OMV 官方 loong64 ISO/镜像 | 不存在 | **不下载**；不要用 AMD64 ISO 冒充 |

> 因此 O-03 **不是“介质完全缺失”**，而是“基础 OS 介质在位、但 scratch 与 loong64
> OMV 依赖缺失”。按任务要求标记 **BLOCKED**，不下载大文件、不伪造运行。

### 4.3 可执行 QEMU 命令（待 scratch/窗口批准后运行）

```bash
Q=/opt/qemu9/bin/qemu-system-loongarch64
FW=/opt/qemu9/share/qemu
SCRATCH=/path/to/approved-scratch     # 必须 >=20GiB 可用，且不是 /dev/sda、/mnt/Data、/data、/opt/casaos-p3
mkdir -p "$SCRATCH/omv-spike"

# 16GiB 稀疏 qcow2；实际占用随安装增长
qemu-img create -f qcow2 -o preallocation=off "$SCRATCH/omv-spike/omv-root.qcow2" 16G

# 可选：持久化 UEFI 变量；若不复制，直接用 -bios 也可以完成一次性安装
cp "$FW/edk2-loongarch64-vars.fd" "$SCRATCH/omv-spike/edk2-vars.fd"

# 资源上限：4 vCPU / 4GiB guest / cgroup 6GiB / 2.5 核；nice 19
systemd-run --scope --unit=omv-spike \
  -p CPUQuota=250% -p MemoryMax=6G -p IOWeight=10 \
  nice -n 19 "$Q" \
  -M virt -accel tcg,thread=multi -cpu max \
  -smp 4,sockets=1,cores=4,threads=1 -m 4096 \
  -bios "$FW/edk2-loongarch64-code.fd" \
  -device virtio-scsi-pci,id=scsi0 \
  -drive if=none,id=hd0,format=qcow2,file="$SCRATCH/omv-spike/omv-root.qcow2" \
  -device scsi-hd,drive=hd0,bus=scsi0.0 \
  -drive if=none,id=cd0,format=raw,readonly=on,media=cdrom,file=/mnt/Data/firmware/loongnix25-20260820.iso \
  -device scsi-cd,drive=cd0,bus=scsi0.0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8080-:80,hostfwd=tcp:127.0.0.1:8443-:443 \
  -device virtio-net-pci,netdev=net0 \
  -device virtio-rng-pci \
  -display none -vnc 127.0.0.1:1 \
  -serial file:"$SCRATCH/omv-spike/serial.log" \
  -monitor unix:"$SCRATCH/omv-spike/monitor.sock",server,nowait \
  -boot order=d
```

要点：

- 显式 `-accel tcg,thread=multi`，**不要用 KVM**；Host 虽有 `/dev/kvm`，但本 spike 要求 TCG。
- `-bios` 已用 512MiB/1vCPU 冒烟验证能启动 edk2；完整 ISO 启动未执行。
- `-drive file=/mnt/Data/firmware/loongnix25-20260820.iso,readonly=on` 使用已保存的 ISO，不再依赖 U 盘；不要改成可写。
- 安装完成后可改为 `-boot order=c`，并移除/保留 CD 均可；若 UEFI 启动项不持久，
  用 `-bios` + `-boot order=c` 或复制 `edk2-vars.fd` 走 pflash。
- 若 `-bios` 与 ISO 的 UEFI 启动不兼容，回退方案是：用 `isoinfo` 从 ISO 只读提取
  `/LIVE/VMLINUZ_6_6.52_LOONG64` 与 `/LIVE/INITRD_IMG_6_6.52_LOONG64`，改用
  `-kernel/-initrd -append "boot=live installer ... console=ttyS0,115200"`；
  该路径未验证，不能写成已通过。

### 4.4 网络、串口、VNC

| 通道 | 配置 | 用途 |
|---|---|---|
| 用户态 NAT | `-netdev user,id=net0,hostfwd=...`；guest 典型地址 `10.0.2.15`，DNS `10.0.2.3` | OMV 仓库、apt、SSH |
| SSH | Host `127.0.0.1:2222` → guest `:22` | 安装后远程操作 |
| HTTP/HTTPS | Host `127.0.0.1:8080` → guest `:80`；`8443` → `:443` | OMV WebGUI |
| VNC | `-vnc 127.0.0.1:1` = 5901 | GRUB/文本安装界面；从 Windows 经 SSH 隧道访问 |
| 串口 | `-serial file:$SCRATCH/omv-spike/serial.log` | 固件/内核日志；需在 GRUB 内核行加 `console=ttyS0,115200` |
| QEMU monitor | `unix:$SCRATCH/omv-spike/monitor.sock` | `quit`/状态查询，避免 Ctrl-C 硬杀 |

Windows 侧隧道：

```bash
ssh -L 5901:127.0.0.1:5901 -L 2222:127.0.0.1:2222 -L 8080:127.0.0.1:8080 loongson-lab
```

然后 VNC 连 `localhost:5901`，SSH 用 `ssh -p 2222 root@127.0.0.1`。

### 4.5 安装步骤（在 VM 内）

1. **Preflight**（Host A）：确认空闲窗口、scratch ≥20GiB、`/dev/sdb` 只读、QEMU/固件路径存在；
   记录 `uptime`、`free -h`、`df -h`、`docker ps`、Runner 状态。
2. 启动 QEMU，VNC 进入 GRUB；选 “Install Loongnix25 English System”（或文本安装）。
   - 若需串口日志：在 GRUB 按 `e`，在 `linux` 行末加 `console=ttyS0,115200`，再启动。
3. 目标盘只选 VM 内的 virtio 磁盘（`lsblk` 确认只有一块 16G 盘）；GPT + EFI 分区；
   根分区使用剩余空间；不添加第二块数据盘。**绝不选 Host 的 `/dev/sda`。**
4. 设置 root 密码；启用 SSH；尽量不装桌面。若安装器默认装了桌面/显示管理器，
   在首次启动后 `systemctl set-default multi-user.target` 并卸载桌面/显示管理器
   （OMV 文档：检测到图形桌面会拒绝安装）。
5. 首次从磁盘启动（`-boot order=c`），验证：
   ```bash
   uname -m                     # loongarch64
   getconf PAGE_SIZE            # 16384
   cat /etc/os-release          # Loongnix 25
   ip -4 a; ping -c1 10.0.2.2   # NAT 网关
   apt-get update               # Loongnix 源可用
   ```
6. 安装 OMV 前置与 keyring（**只加 synchrony，不加 bookworm**）：
   ```bash
   apt-get install -y systemd-resolved psmisc
   systemctl enable --now systemd-resolved.service
   systemctl restart systemd-resolved.service
   wget -O- https://packages.openmediavault.io/archive.key \
     | gpg --dearmor -o /usr/share/keyrings/openmediavault-archive-keyring.gpg
   cat >/etc/apt/sources.list.d/openmediavault.list <<'EOF'
   deb [signed-by=/usr/share/keyrings/openmediavault-archive-keyring.gpg] https://packages.openmediavault.io/ synchrony main
   EOF
   apt-get update
   ```

   预期可能看到 apt 提示 `Skipping acquire of configured file 'main/binary-loong64/Packages'
   as repository ... doesn't support architecture 'loong64'`；这是 O-02 的仓库层证据，
   不要用 `dpkg --add-architecture amd64` 绕过。若 `openmediavault` 包在
   `apt-cache policy` 中不可见，先记录该事实，再手工下载 `arch:all` .deb 仅用于
   依赖闭包核对（不要安装 amd64 依赖）。
7. **先 dry-run**，记录精确缺失：
   ```bash
   apt-get -s install --no-install-recommends openmediavault 2>&1 | tee /root/omv-dryrun.log
   ```
8. 再真实安装（预期会在 `php-pam`/`openmediavault-salt`/`netplan.io` 处失败）：
   ```bash
   export LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive APT_LISTCHANGES_FRONTEND=none
   apt-get --yes --no-install-recommends install openmediavault 2>&1 | tee /root/omv-install.log
   ```
9. 若安装成功：`systemctl is-active openmediavault-engined`，
   `curl -sI http://127.0.0.1/`，从 Host 访问 `http://127.0.0.1:8080/`；
   记录 OMV WebGUI 登录页。不要在本阶段跑 O-04 highstate。
   OMV postinst 可能通过 netplan/systemd-networkd 重配网络，SSH/NAT 可能断；
   保留 VNC/串口作为救援通道，必要时在控制台运行 `omv-firstaid`。
10. 关闭：通过 monitor `quit` 或 `systemctl poweroff`；保留 `serial.log`、`omv-dryrun.log`、
    `omv-install.log`、`apt-cache` 输出；把哈希和结论写回本文件/O-03 记录。

### 4.6 判定标准

| 门 | 通过条件 | 失败/阻塞处理 |
|---|---|---|
| **G0 Preflight** | 空闲窗口确认；scratch ≥20GiB；`/dev/sdb` 只读；QEMU/固件存在 | 不满足即 **BLOCKED**，不启动 |
| **G1 固件** | serial/VNC 出现 edk2 启动信息，进入 UEFI boot manager | 15s 冒烟只到 PEI，不能算 G1 通过 |
| **G2 ISO 启动** | 出现 Loongnix GRUB/安装器或 live shell | 失败则记录串口/VNC 证据，停止 |
| **G3 基础 OS** | 从 virtio 盘重启；SSH 可用；`uname -m=loongarch64`；`getconf PAGE_SIZE=16384`；`apt-get update` 成功 | 失败即 **BLOCKED**；不得改用 Host 数据盘 |
| **G4 OMV 安装** | `apt-get install openmediavault` 退出 0，无缺失依赖 | 非 0 即 **FAIL**；记录完整缺失列表 |
| **G5 OMV 服务** | `openmediavault-engined` active；WebGUI 返回 200/302 | 失败即 **FAIL** |
| **PASS** | G3 + G4 + G5 全部通过 | 缺一不可 |
| **PARTIAL** | G3 通过，G4 在已枚举依赖处失败 | 这是 O-02 预期的结果，可作为 O-06 证据 |
| **BLOCKED** | G0/G1/G2/G3 无法完成 | 不得伪造 PASS |

### 4.7 O-03 结论

| 子项 | 结论 | 依据 |
|---|---|---|
| QEMU/固件/基础介质 | **可行** | QEMU 9.2 + edk2 16MiB + Loongnix 25 ISO `/dev/sdb` 均在位；15s 固件冒烟到 PEI |
| 端到端 OMV 安装 spike | **证据不足** | 缺 ≥16GiB scratch；O-02 已判 3 组硬阻塞；未运行完整安装；官方 OMV ISO 仅 AMD64；状态 BLOCKED |
| 总体 O-03 | **证据不足** | 环境组件在位，但“能装出 OMV”没有证据；不得写成可行；状态 BLOCKED |

---

## 5. 与 CasaOS/iStore 测试的资源错峰

### 5.1 当前 Host A 状态（审计时）

| 项 | 值 |
|---|---|
| CPU / RAM | 8 线程 / 31GiB；审计时 load 约 0.1~1.3 |
| 可用内存 | 约 22~28GiB（随 CasaOS/容器波动） |
| `/build` | 4.8GiB 可用（87% 已用） |
| `/tmp` | 16GiB tmpfs（重启后为空；内存盘，不适合放 qcow2） |
| 常驻负载 | CasaOS P3、Docker（mihomo）、GitHub Actions Runner（listener 常驻） |
| 重启事件 | 审计期间 22:19:10 的一次干净 shutdown 是主会话执行 C-04 systemd 自启验证的协调重启，22:19:46 恢复；不是异常，也不是 OMV 子代理触发 |

### 5.2 QEMU 运行窗口规则

**只有同时满足以下条件才允许启动 QEMU：**

1. `uptime` 的 1 分钟 load < 2.0，且持续 10 分钟无上升趋势。
2. `free -h` 的 `available` ≥ 12GiB。
3. 没有正在运行的 GitHub Actions `Runner.Worker` 构建任务（仅有 listener 不算）。
4. 没有 CasaOS 24h soak、iStore 真机测试、镜像构建/推送、Phase 2 全量矩阵在跑。
5. 用户明确批准的时间窗；单次不超过 90 分钟。
6. scratch 已就绪（≥20GiB，非数据盘）。

### 5.3 资源上限

| 资源 | 上限 | 手段 |
|---|---|---|
| vCPU | 4（TCG 线程） | `-smp 4` |
| 主机 CPU 配额 | 250%（约 2.5 核） | `systemd-run -p CPUQuota=250%` |
| guest RAM | 4GiB | `-m 4096` |
| cgroup 内存 | 6GiB（含 QEMU 开销） | `-p MemoryMax=6G` |
| IO 权重 | 10（低） | `-p IOWeight=10` |
| 进程优先级 | nice 19 | `nice -n 19` |
| 运行时长 | ≤90 分钟/次 | monitor/超时；超时先保存日志再 quit |

**中止条件**：Host load > 6、available < 6GiB、CasaOS/iStore 测试开始、磁盘可用 < 2GiB、
QEMU 无输出超过 20 分钟。命中任一项立即 `quit`，保留日志，不强行写盘。

### 5.4 禁止事项

- 不使用 `/dev/sda`、`/mnt/Data`、`/data`、`/opt/casaos-p3` 作为 QEMU 磁盘/日志/缓存路径。
- 不写 `/dev/sdb`（LOONGSONISO U 盘）；只读挂载/只读 `-drive`。
- 不在 CasaOS/iStore 测试或 GitHub Actions 构建期间启动 QEMU。
- 不用 NBD 作为 OMV 管理根盘（NEXT-PLAN 安全红线）。
- 不把 QEMU 大日志/镜像提交到仓库；只在本文件记录哈希、路径和结论。

---

## 6. 证据复现命令

### 6.1 OMV 仓库元数据

```bash
curl -sSL https://openmediavault.github.io/packages/dists/synchrony/Release
curl -sSL https://openmediavault.github.io/packages/dists/sandworm/Release
curl -sSL -o synchrony-Packages.gz \
  https://openmediavault.github.io/packages/dists/synchrony/main/binary-amd64/Packages.gz
gzip -dc synchrony-Packages.gz | awk 'BEGIN{RS="\n\n"} /^Package: openmediavault\n/{print}'
gzip -dc synchrony-Packages.gz | awk 'BEGIN{RS="\n\n"} {p="";a="";
  if (match($0,/Package: ([^\n]+)/,m)) p=m[1];
  if (match($0,/Architecture: ([^\n]+)/,m)) a=m[1];
  if (a!="all") print p" ["a"]"}'
```

### 6.2 Debian 架构列表

```bash
curl -sSL https://deb.debian.org/debian/dists/bookworm/Release | grep -E '^(Suite|Architectures):'
curl -sSL https://deb.debian.org/debian/dists/trixie/Release  | grep -E '^(Suite|Architectures):'
curl -sSL https://packages.debian.org/trixie/netplan.io | sed -e 's/<[^>]*>/ /g' | tr -s '[:space:]' ' '
```

### 6.3 Host A 依赖候选

```bash
ssh loongson-lab 'dpkg --print-architecture; getconf PAGE_SIZE'
ssh loongson-lab 'for p in php-fpm php-pam salt-minion openmediavault-salt netplan.io \
  wsdd-server openmediavault-keyring cpufrequtils linux-cpupower; do
  printf "%-24s " "$p"; apt-cache policy "$p" 2>/dev/null | awk "/候选：|Candidate:/{print \$2; exit}";
done'
```

### 6.4 闭包脚本（Host A 临时脚本，不在仓库）

`/tmp/omv-closure.py` 的逻辑：

- `apt.Cache()` 加载 Loongnix 25 缓存；
- 从 OMV 核心 `Depends` 种子出发；
- 对 `Depends`/`PreDepends`/`Recommends` 做 BFS；
- 每个 OR 组取第一个有候选的包；
- 记录候选 `architecture`；
- 输出 `VISITED`、`ARCH all=... loong64=...`、`MISSING`。

本次输出：

```text
OMV 8: VISITED 374; ARCH all=63, loong64=306; MISSING 15（人工核对后 3 组硬阻塞）
OMV 7: VISITED 366; ARCH all=63, loong64=297; MISSING 14（人工核对后 3 组硬阻塞）
```

---

## 7. 交接给 O-04/O-05/O-06

| 后续项 | 本报告给出的前提 |
|---|---|
| **O-04 SaltStack highstate** | 当前不能开工：OMV 8 安装尚未成立；`openmediavault-salt`/Salt 3008 无 loong64。先解决 O-02 的 3 组阻塞，再在隔离 VM 里 `test=True` |
| **O-05 插件评估** | `openmediavault-compose` 是 `arch:all`，可优先评估；ZFS 插件需引用 OpenZFS 2.4.4 + 16K 页证据；KVM 已封存，移出；sharerootfs/sftp/rsync 随 OMV 包 |
| **O-06 Go/No-Go** | 输入：OMV 8 是唯一候选；as-is 不可行；若无法在合理工期内交付 loong64 的 `php-pam`、Salt 3008、`netplan.io`/`libnetplan1`，路线 B（只做 compose 集成）或 C（no-go，保留 ksmbd）更现实 |
| **O-09 状态同步** | 把本文件结论写入 GAPS/ROADMAP/OMV-FEASIBILITY；当前 GAPS/ROADMAP 的“已排期 Gate 0”应改为“O-01/O-02 完成，O-03 BLOCKED，待依赖补齐” |

---

## 附录 A：O-01/O-02 关键数字速查

| 项 | 值 |
|---|---|
| Host 架构 / 页大小 | `loong64` / `16384` |
| Host glibc / systemd / PHP | `2.41-13.lnd.1` / `257.7-1.lnd.1` / `8.4.16-1~deb13u1`（仓库） |
| Host 内核 / 启动 | `6.6.52-loong64` / UEFI + GRUB 2.12 |
| OMV 7 核心包 | `7.7.24-7`（all） |
| OMV 8 核心包 | `8.5.12-1`（all） |
| OMV 7 仓库架构 | `i386 amd64 armel armhf arm64`（无 loong64） |
| OMV 8 仓库架构 | `amd64 arm64`（无 loong64） |
| OMV 7 包组成 | 29 all + 2 amd64 |
| OMV 8 包组成 | 29 all + 5 amd64 |
| OMV 8 闭包 | 374 节点；63 all + 306 loong64；3 组硬阻塞 |
| OMV 7 闭包 | 366 节点；63 all + 297 loong64；3 组硬阻塞 |
| QEMU / 固件 | `/opt/qemu9/bin/qemu-system-loongarch64` 9.2.0；`edk2-loongarch64-code.fd` 16MiB |
| 基础 OS 介质 | `/mnt/Data/firmware/loongnix25-20260820.iso`（5.5GB，sha256 `6f607035…83b9`），只读 |
| 可写 scratch | `/build` 4.8GiB；`/tmp` 16GiB tmpfs；**不足** |
| O-03 判定 | **BLOCKED**（未运行完整 spike） |
