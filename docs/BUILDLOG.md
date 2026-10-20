# 构建日志

## 2026-10-11 首次构建（toolchain→内核→包→组装，一次通过，除两个环境坑）

- 环境：WSL2 Ubuntu（x86_64），32 核 / 60GB，`wsl -u root` 装依赖（`build-essential libncurses-dev gawk unzip flex gettext` 等），构建本身用普通用户跑。
- 源码：`git clone --depth 1 https://github.com/istoreos/istoreos.git`（分支 istoreos-24.10，commit 见构建机 `~/istore-la-build/src-version.txt`）。
- 配置：`config/loongarch64-generic.config` → `make defconfig`（TARGET=loongarch64/generic，内核 6.6，LuCI 中文 + kmod-tun）。
- 结果：157 个包零编译错误；toolchain + 内核 6.6 + LuCI 全绿。

## 排障 1：kernel.org 下载卡死

- 现象：构建 1.5h 无进展，负载~0，卡在 `toolchain/kernel-headers`，`dl/linux-6.6.144.tar.xz.dl` 在 cdn.kernel.org 上以 ~17KB/s 蠕动。
- 处理：清华镜像（`mirrors.tuna.tsinghua.edu.cn/kernel/`，实测 5.3MB/s）12 秒下完 140MB 整包放到 `dl/`；kill 残留 curl 后 download.pl 验 hash 通过，构建继续。
- 教训：开编前先把 `dl/` 大包用国内镜像预下好；`pkill` 匹配串用 `[c]dn...` 写法，否则杀掉自己的 `bash -lc`（已踩）。

## 排障 2：package/install 挂（WSL PATH 污染）

- 现象：`make[2] package/install Error 1`，定格 rootfs 打包后处理。
- 病因：`find ... -execdir touch` 拒绝执行——WSL 继承的 Windows PATH 含 `Files/Git/mingw64/bin`（相对路径残留），GNU find 认为不安全。跟龙芯、代码无关。
- 处理：构建 shell 首行 `export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`，断点续跑即过。

## 2026-10-11 第二轮：加商店件（已完成，发版 v1）

- 首版 img（48M）已出，LuCI 中文齐，110 个 ipk，**缺商店**。
- 商店源定位：`luci-app-store`（v0.2.1）+ `taskd`（纯 shell，无编译）+ `luci-lib-taskd` 在 **linkease/istore** 仓库 `luci/` 下；`luci-app-quickstart` + `luci-app-istorex` 在 nas-packages-luci feed。老 `is-opkg` 已被 `taskd` 取代，不用找了。
- 动作：feeds.conf 加 `store`、`nasluci` 两行 → install 五个包 → config 打开 → `make -j32` 增量编。
- 插曲：增量后顶层 `make` 认不出 config 变了（"没活干"退出），显式 `make package/install` + `make target/install` 点名两阶段即过（先删 `.target_install` 戳）。
- 结果：**完整版 img（50M）+ 商店全进**（rootfs 里 `store.lua`/`istore_backend.lua`/`taskd` + opkg status `luci-app-store 0.2.1-r1`，共 197 个包）。`.manifest` 生成了 0 字节空文件（已知小毛病，以 opkg status 为准）。
- 发版：`v1-loongarch64`，5 个附件（img/rootfs/opkg-feed/sha256sums/version），Release 注明**未在真机验证、求测试**。

## 2026-10-11 Full check（解开 img 逐项验）

- 分区：GPT + BIOS boot + 16M EFI + 232M rootfs + 2G overlay，标准。
- EFI：`bootloongarch64.efi`。商店：rootfs 含 `store.lua`/`istore_backend.lua`/`taskd`，opkg 登记 197 包。
- **bug：rootfs 无 `/etc/config/`，loongarch64 base-files 缺 x86 的 `board.d/99-default_network`，首启无网。**
- 修：x86 原文件拷入 `target/linux/loongarch64/base-files/etc/board.d/`（见 `patches/99-default_network.loongarch64`），删戳后 `make target/install` 重打，复验 rootfs 含该文件。
- Release 已更新 img + sha256sums（17:33 版）。rootfs.tar.gz（LXC 用，走宿主网络）不受影响，未更新。

## 2026-10-11 发版校验乌龙：sha256sums 对不上

- 现象：从 GitHub 下载 img.gz 一验，FAILED。
- 病因：上传的 `sha256sums` 还是首版（17:05）的，没跟着 img 一起更新——发版流程漏了同步校验这步。
- 处理：改发**发版专用干净版**（只含 5 个附件），重新上传后下载全量复核通过。
- 教训：发版 checklist 加一条——**sums 必须在所有附件定稿后最后生成**，且只覆盖上传的文件。

## 2026-10-11 发版全量复核通过

- 从 GitHub 把 5 个附件全下回来逐字节验：img.gz / rootfs.tar.gz / opkg-feed / version.buildinfo **全部 OK**。
- 备注：Release 大文件 CDN 到本机约 130KB/s，135M 下了约 20 分钟；以后传包按此规划。

## 2026-10-12 第三轮：三件套（Tailscale / EasyTier / OpenClash）

- Tailscale：feed 版 Go staging 在 LA 上坏掉（`no Go files`）→ 宿主 Go 1.26 `GOARCH=loong64` 直编（`tailscaled` 33M + CLI 20M，`file` 实锤 ELF LoongArch 静态链接）→ 本地 bin 包。坑：goproxy 官方走不动切国内源；`/tmp` 会被清，二进制放持久目录；tarball 打完当场 `tar tz` 验（吃过 20 字节空包的亏）。
- EasyTier：官方 loongarch64 包直装，三个入门税——空 `Build/Compile`、unzip 残留预清理、zip 顶层目录落点（`PKG_BINDIR`）。`--config-file` 经 strings 实锤支持，init 优先 TOML。
- OpenClash：feed 直装（`luci-app-openclash_0.47.156`），纯 Lua/shell；mihomo 内核运行时替换（官方 loong64 abi2，静态链接已验）。
- 通病记录：feeds 增删包后必 `grep .config` 确认符号、清 `tmp/info` 残留元数据；`make -j32` 认不出变更就点名阶段（`package/install` + `make target/install`，先删戳）。

## 2026-10-12 v2 双版与 24.10-la1 发版

- 三件套全进（tailscale/easytier/openclash + store），另修：dnsmasq 二选一（留 -full）、rootfs 分区提到 512M、quickstart/istorex 因 DEPENDS 写死 x86/ARM 拿掉。
- v2-personal（本机，109M）：EasyTier 整网 TOML + verge 配置（Meta/1500/双 mesh DIRECT 置顶）+ mihomo 内核 + 中文默认 + 三件套自启，解包复验全在。永不上传。
- v2-public（`24.10-la1`）：同底、无预置、英文默认。发版前审计：解包 grep 密钥/域名/IP 全空；rootfs.tar.gz 与 opkg-feed 同查，v2preset ipk 已剔除。5 附件已传。

## 2026-10-12 三版复查全绿

- v1-loongarch64：此前已全量验过。
- 24.10-la1：5 个附件全下回逐字节验，img/rootfs/opkg-feed/version **全部 OK**。
- v2-personal（本机）：解包验过预置三件 + hostname；确认未进库、未进任何 Release。
- CI：修了两次（冒烟缺 feed→断言挂；feed 重名→9 秒挂），待下次 push 变绿。

## 2026-10-12 v3 batch 2：八个应用 ipk 全齐

- alist / baidupcs-go / homebox / sunpanel / lucky / vlmcsd / rtp2httpd / openlist，8 个 ipk 全落地。
- openlist 插曲：feed 版与本地版重名打架三回合（feed Go staging 坏 → 切本地 → 本地 init 文件在 feed 切换中丢失 → 重写恢复）。以后切 feed/本地路线时，`git status` 先确认文件齐。

## 2026-10-12 v3 首批进源，发 24.10-la2

- 自建源 21 个包（17 自编/直装 + tailscale/easytier/openclash/store），`ipkg-make-index.sh` 需显式 `MKHASH=` 否则出空索引（已踩）。
- 发版 `24.10-la2`：opkg-feed tarball（195M）+ sha256sums。LuCI 批量同步、app-meta JSON、Podman 本体、Rust/samba 判定后续跟进。

## 出网走本机 Verge 代理（2026-10-13 起）

- 本机 Verge (verge-mihomo) 实际监听 `127.0.0.1:7897`（非 Downloads 那份 config 的 17890，以 `netstat` 实测为准）。
- Git Bash 侧：`export http_proxy=http://127.0.0.1:7897 https_proxy=... no_proxy=localhost,127.0.0.1`，被墙站走代理、其余由 Verge 规则分流。
- WSL 侧暂直连（代理只绑 127.0.0.1，WSL 够不着；要通需 Verge 开允许局域网）。

## 2026-10-13 CI 门禁第三版：不再断言 defconfig 留存

- 现象：同输入（最小 config + 全 feeds）在两台 WSL 上 defconfig 留 `luci-app-store`，在 CI runner 上静默丢掉。feeds clone、install、元数据三处全绿，store 上游 9-25 后未动。
- 未解之谜：同源 Kconfig 在不同环境的求值差异（候选：make 版本、locale 排序、runner 镜像差异），本地复现三次全是"留"，CI 三次全是"丢"。
- 对策：门禁改断言 feeds 目录 + 包索引 + defconfig 退出码（全确定性项）；defconfig 留存问题降级为观察项，真验证交给整编 job。教训：**永远别断言 Kconfig 的静默行为**。

## 2026-10-17 真机首验（3A6000）：四个二进制全跑起来

- tailscaled 1.80.3 / easytier-core 2.6.4 / mihomo v1.19.32-loong64 / rclone v1.75.2，`--version`/`-v` 全过。
- 教训：scp 必须走 Windows 原生（WSL 到不了 192.168.8.x，还缺 key）；文件中转经 outputs/xfer-out/。
- 机器：3A6000 4C8T/16G/37G盘/6.6.52，有/dev/kvm，有线+无线，无S80卡（Loongson集成显示），禁休眠已做（mask四件套+IdleAction=ignore）。

## 2026-10-17 v2-personal-full：全量个人版一次成

- 去掉 quickstart/istorex（x86 闭源死刑）后 world 一次过；rootfs 1G 分区，245 个包。
- personal img（257M）含全部预置（network.toml/mihomo 核/99 中文自启）+ 全量应用，只存本机。

## 2026-10-18 真机容器验证（3A6000，docker.io 26.1.5，全系统容器）

- personal rootfs.tar.gz → `docker import istore:personal` → `--privileged --network=host -v istore_etc:/etc/config /sbin/init`，一次点亮。
- procd/ubus/uhttpd(LuCI :80→200)/netifd/中文(zh_cn)/ddns-go 全绿；KVM 旧路封存（qemu10+eiointc 中断投递死，见三子代理结论）。
- G2：EasyTier 进网（私人网段内，ping hg2t .63 零丢包 22ms）；mihomo 转发通、节点 alive；tailscale 待用户登录。
- 抓到 4 个固件 bug（公版 la3 同病，la4 修）：
  1. easytier instance_id 非法 UUID（`...router000001`）→ 已改 `...000000000072`（私人预置）。
  2. mihomo loong64 版拒所有 mmdb（GeoIP2/GeoLite2/Meta-geoip 全报 invalid，疑 maxminddb 在 LA 的对齐/解码问题）→ GEOIP,CN 单规则改 RULE-SET 本地 cn-ip.yaml（8796 条，mayaxcn 源，私人预置已换，逐字节验过 -t 成功）。
  3. /etc/opkg.conf 缺 arch 行 → 运行时 opkg 装啥都 incompatible → 新包 feeds-pkg/opkg-archconf（/etc/opkg/10-arch.conf），公版 config 已加。
  4. 缺 iptables-nft → tailscaled 起不来（router.Up 找不到 iptables）→ 公版 config 已加 CONFIG_PACKAGE_iptables-nft=y。
- 附带：镜像自带 205K Country.mmdb 占位 stub（openclash 数据，2026-08-27 打包）；la4 打包时换正版 DB 或删掉走在线更新。

## 2026-10-18 la4 整编（public，248M img，一次通过，三道坎）

- 坎1 xray-core：平铺 zip 残留触发 unzip 交互式询问。教训升级：只清 BUILD_DIR 根残留，不动 PKG_BUILD_DIR；且 5 个文件要列全（漏了 LICENSE/README 照挂）。修法已进 feeds-pkg/xray-core/Makefile（qbittorrent 同款）。
- 坎2 dnsmasq/dnsmasq-full 二选一：repo config 没写，默认 profile 把 plain 版带回来，package/install 报 file clash，连带 openclash 装不上。修法：config 显式关 plain 开 -full（以后加包先想 clash）。
- 坎3 rootfs 512M 撑爆（iptables/luci-compat 进来之后）：按惯例翻倍到 1024M。
- 附带发现：core target 包（iptables-nft 等）的 .ipk 在 bin/targets/.../packages/，不在 bin/packages/*/feed 目录，找包先想这一层。
- 发版 24.10-la4：img.gz + rootfs.tar.gz + opkg-feed(264M) + sums(最后生成、全量复核 OK)+buildinfo，draft 传完转正。

## 2026-10-18 podman-in-OpenWrt 结论（容器真机验证）

- podman 5.8.8 静态版在 musl 下跑不起来：`go-sqlite3 requires cgo`。根因是上游 5.5 删了 boltdb 后端，`[database] backend="boltdb"` 配了也被静默忽略（配错值也不报错，已用 nonsense 验证），sqlite 成为唯一后端而静态版无 cgo。出路：降 podman 4.x，或 CGO_ENABLED=1 用 musl-gcc 重编（la5）。
- dockermanager 点绿改走宿主 socket：全系统容器加挂 `-v /var/run/docker.sock:/root/docker.sock`（注意 /var/run 在 OpenWrt 里是 tmpfs，挂 /var/run 下会被启动清空，必须挂持久路径），容器内 docker CLI 已验证能列出宿主容器。luci-app-dockerman 本体缺失（纯 Lua，排 la5 打包），socket 通路已通，UI 装上即绿。

## 2026-10-18 dockerman 上架 + podman musl 链打通（容器真机）

- luci-app-dockerman 0.5.26 + luci-lib-docker 0.3.4（lisaac 上游，纯 Lua+静态）：
  去架构锁（上游 `@(aarch64||arm||x86_64)` 无 loongarch64）；依赖精简到 luci-compat+luci-lib-docker+luci-lib-ip（docker CLI/ttyd/iptables-nft 运行时另装，不写进 DEPENDS——docker 的依赖树会拖进无 loongarch 支持的 libseccomp，feed 版 libseccomp 在 src/arch.c 直接 #error）。
  注意：feeds/luci 自带同名 luci-lib-docker（一样被架构锁），与本地包重名，tree 构建走 feed 版导致依赖解析绕路——la5 修法三选一：本地包改名 / feed 包打架构锁补丁 / 沿用手打 ipk（本次已验证手打 ipk 路线全通）。
  坑：controller 要的是 luci/model/docker.lua（不是顶层 docker.lua），装错路径报 module not found；uci dockerd.dockerman.socket_path 指到 /root/docker.sock（/var/run 在容器里是 tmpfs，挂载会被启动清空）。
- podman musl 链：CGO 重编 podman 5.8.8（musl-gcc，sqlite 静态编入，boltdb 已死）+ Alpine loong64 的 netavark/aardvark（musl 直装即用）+ conmon/runc 既有包——`podman info` 全绿。容器嵌套跑首个容器仍需 --cgroups=disabled --security-opt seccomp=unconfined（嵌套 cgroup/命名空间限制，真机固件无此问题）。
- jellyfin loong64（进行中）：.NET 9 SDK 已 CI 编出；server 直编通过；web UI 需 node 重编（sass-embedded 无 loong64，删了用纯 sass）；e_sqlite3.so 用系统 libsqlite3 顶替；Skia 缺失→NullImageEncoder 补丁先跑起来（缩略图后补）；镜像底座从 Debian（无 loong64）切 openEuler 24.03（官方有 loong64）。

## 2026-10-18 jellyfin loong64 首版镜像（容器真机验证通过）

- .NET 9 SDK loongarch64：fork driver1998/dotnet-nolsx-build 思路，自建 workflow（.github/workflows/dotnet-sdk-loong64.yml，微软官方交叉容器，x86 runner 纯交叉），~40 分钟出 tarball（SDK 9.0.201）。盒子 glibc 2.41 满足 >=2.41 要求。
- server：jellyfin v10.11.0 源码直编（`dotnet publish -c Release`，NuGet 官方源盒子直连可下）。三处龙芯坑：
  1. `e_sqlite3.so` 无 loong64 版（Microsoft.Data.Sqlite 找 runtimes/linux-loongarch64/native）→ 系统 libsqlite3.so.0.8.6 改名顶上，迁移通过。
  2. web UI 不在 publish 里：jellyfin-web v10.11.11 另 clone，用 node 20 + npm 10 编（node 9.2 装不上：要求 npm>=9.6；sass-embedded 无 loong64，删了用纯 JS sass 回退）。
  3. Skia 缺失（libSkiaSharp.so 无 loong64，NuGet 只有 x64/arm64/arm）：CoreAppHost.cs 里 IsNativeLibAvailable 的 try/catch 拦不住——SkiaEncoder 的静态字段初始化器在类型加载时先炸（TypeInitializationException）。补丁：外层再包 try/catch， fallback NullImageEncoder（缩略图/图片处理降级，播放不受影响；完整 Skia 需另编，排期）。
- 镜像：openEuler 24.03 loong64 官方底（Debian 无 loong64 镜像）+ yum 装 ffmpeg 6.1/icu/字体 + 自带 libstdc++.so.6.0.33（openEuler 自带的老，dotnet 9 要 GLIBCXX_3.4.32）+ publish 输出 + web UI。`jellyfin:loong64` 1.46G，容器内 API 10.11.0 + Web 200 验证通过（注意：验证时先停掉宿主直跑实例，防 8096 冲突误判——已踩一次）。
- 教训：docker run 参数写错会静默起不来，先看 `docker ps` 确认谁在监听；验证 API 时务必确认响应来自容器（端口冲突会误判）。

## 2026-10-18 podman 全链路打通（容器真机，嵌套）+ 应用镜像三连

- crun 1.30.1 纯静态 loong64（子代理编，--disable-seccomp/systemd/caps+json-c/argp 用 staging 现货，libtool 吞 -static 改手工终链），ipk 已进真机。
- 嵌套三坑：① boltdb 已死确认（5.8 无视配置，只能 sqlite → CGO 版是唯一解）；② e_sqlite 无 loong64？不，podman 的 sqlite 是 amalgamation 自带，CGO 版直接好；③ /run 是悬空软链接（OpenWrt 传统）→ 镜像里换成实目录；④ bridge 网要宿主内核 nft_conntrack（Loongnix 6.6.52 没有，缺省；--network=host/none 照用）。
- 成果：`podman run --network={none,host} --security-opt seccomp=unconfined --cgroups=disabled --runtime crun` 跑通 OpenWrt（PODMAN-FIRST-RUN-OK 三次确认）。dockerman 看宿主容器已绿。
- jellyfin:loong64（1.46G，API 10.11.0 + Web 200 验证）：.NET 9 SDK 自编；web 单独编（sass 纯 JS 回退）；e_sqlite3 拿系统库顶；Skia 缺失打 NullImageEncoder 补丁（缩略图后补）；底座 openEuler 24.03 loong64 官方镜像 + 自带 libstdc++。
- navidrome:loong64（Go 1.24 + taglib 1.13 自编 + DSD 补丁删减 + sass 问题同上）：302 setup 向导 + scanner 转，待填媒体验证播放。
- vaultwarden：Rust 1.88 编译通过但要 glibc 2.39（openEuler 底座只有 2.38）；1.80 不支持 edition2024；转 musl 静态编译中（musl 工具链已装好）。
- uptimekuma：子代理在打（npm 一次过，vite 一次过）。

## 2026-10-18 navidrome loong64（Go 1.24 + taglib 系统版，DSD 完整）

- 本机 Go 1.24 直接编；前端 npm ci 一次过（vite 缺失是因为忘了先 npm install，不是 bug）。
- taglib 绕路记：自带 1.13 缺 dsffile.h；先写了个 DSD 阉割补丁，后发现系统 taglib 2.0.2 自带 DSD——之前 "apeproperties.h 找不到"是误报（我的 shell 把 pkg-config 的 --define-prefix 搞坏了路径，Debian multiarch 已知坑，写了个 wrapper 脚本绕过）。
- 结论：用系统 taglib 2.0.2 全量编，零补丁（已 revert），DSD 原生支持。镜像 openEuler 底 + 系统 libtag.so.2 拷进去（10.11 节点）。
- vaultwarden 坑（进行中）：Rust 1.88 的 pidfd_getpid/spawnp 要 glibc 2.39，openEuler 底只有 2.38。试过：musl 全静态（缺 musl libgcc，死路）、Rust 1.80（edition2024 不认）、1.85/1.86 手动装（在测 1.85 能否避开 pidfd 符号）。

## 2026-10-18 vaultwarden loong64（Rust 1.86 + box glibc 移植）

- 坑链：Rust 1.88 的 pidfd_getpid/spawnp 要 glibc 2.39，openEuler 底只有 2.38；1.80 不认 edition2024；1.85/1.86 手动装（Windows 中转 tarball）；musl 全静态卡在 musl libgcc 缺失。
- 解法：显式 loader——把宿主 glibc 2.41 一套（ld/ld-linux、libc/libm/pthread/dl/gcc_s、libssl/crypto/z/zstd）COPY 进镜像 /opt/boxglibc，ENTRYPOINT 直接调 ld-linux + --library-path。宿主 Apache 占 80 端口的教训：验证时用 8443 避开（又一次被本机服务误导 curl 结果，已记）。
- Web vault：官方 v2025.7.0 静态包直拷（arch 无关）。镜像 vaultwarden:loong64，Rocket launched + Web 200。
- navidrome 补记：DSD 最终用系统 taglib 2.0.2 全量编（零补丁，wrapper 恢复原样）；之前"头文件找不到"是 pkg-config --define-prefix 在 Debian multiarch 下算错 prefix（/usr/lib/include 这种不存在的路径），写了个去 --define-prefix 的 wrapper 解决；镜像里带系统 libtag.so.2。

## 2026-10-18 podman 嵌套跑通（crun 是钥匙）+ vaultwarden glibc 攻防

- podman 完整链：CGO 版 podman + conmon/runc/兼容层 + Alpine loong64 netavark/aardvark + **crun 1.30.1 musl 静态自编**（--disable-seccomp/caps/criu/bpf/dl，json-c/argp 用 staging，终链手动 -static）。
- 关键一跃：`default_runtime="crun"` 后 `--cgroups=disabled` 直接跑通（runc 1.6 不兼容 NoCgroups，crun 可以）。嵌套三模式：none ✓ host ✓ bridge（要宿主 nftables conntrack，Loongnix 6.6 无此模块，暂缺）。
- 容器内 /run 是悬空软链（→/tmp/run），crun 建 .containerenv 失败；修法：镜像里换成实目录（已进 runfix 版 image）。
- dockerman 里缺 containerd？不缺：连的是宿主 docker socket，UI 列出全部宿主容器 ✓。
- vaultwarden 进行中：Rust 1.88 的 pidfd_getpid/spawnp 要 glibc 2.39（openEuler 底 2.38）。试过：musl 全静态（缺 musl libgcc）、1.80（edition2024 不认）、1.85/1.86 手动装（工具链混装失败）；现用 rustup 正规 1.86 重编中，若仍带 2.39，下一步是 patchelf 绑 box glibc 或等基础镜像升级。

## 2026-10-18 vaultwarden 定稿（勘误上条）

- 上条"进行中"已结案：正规 rustup 1.86 重编后仍带 GLIBC_2.39 引用——不是 1.88 独有，是 std::process::Command 触发 pidfd_getpid/pidfd_spawnp 弱符号（最小验证：空 main 无引用，加一行 Command::new 立刻 2 个引用）。所以降 Rust 版本这条路不成立。
- 定稿方案：镜像内 /opt/boxglibc 打包宿主 glibc 2.41 闭包（ld-linux、libc/libm/libgcc_s/libssl/libcrypto/libz/libzstd），ENTRYPOINT 用 `ld-linux --library-path /opt/boxglibc /vaultwarden`。Web-vault 用官方 v2025.7.0 静态包。
- 验证：Rocket launched + Web 200（8443；宿主 Apache 占 80，教训记两次了——验证前先 ss 看端口）。
- 产物 vaultwarden:loong64，容器常驻。

## 2026-10-18 应用镜像第二批（syncthing / adguardhome / memos）

- syncthing v2.1.6：官方 loong64 包直装。坑：v2 CLI 把单横线长参数当短参数簇，必须 `--home=`/`--gui-address=` 双横线。
- adguardhome v0.107.79：官方近 300 个 release 均无 loong64 资产 → 源码自编（盒子 Go）+ 官方前端包；端口 53 用映射避让宿主 dnsmasq，宿主 5353 UDP 被 avahi/kdeconnect 占用，测试改 5354。
- memos v0.31.0：官方无 loong64 → 源码编；坑一：go.mod 要 Go 1.27，用 GOTOOLCHAIN 自动拉；坑二：Vite 8 的 rolldown 无 linux-loong64 binding（npm 404），前端在 Windows x64 上编 dist（架构无关）再回传 embed；后端仍盒子本地编（纯 Go sqlite，CGO=0）。
- 三只均已上架 Docker Hub `yunixintel/*`（双 tag）。

## 2026-10-18 应用镜像第三批（gogs / filebrowser）

- gogs v0.14.3：官方无 loong64 → 源码编；go.mod 要 1.25（GOTOOLCHAIN 自动拉）；0.14 起 SQLite 已换纯 Go 驱动（glebarez/go-sqlite），CGO 只是形式；镜像带 git（2.54）；首启只有 /install 向导，app.ini 在安装提交时生成（上游行为）。
- filebrowser v2.63.23：官方无 loong64 → 源码编；前端 Vite 8/rolldown 无 loong64 binding → 私有副本降 Vite 7 + rollup（有官方 loong64 包）成功；**v2.63 默认监听 127.0.0.1**，容器里必须显式 `-a 0.0.0.0`；上游项目 2026-09-01 已归档。
- 两只已上架 Docker Hub 双 tag。本轮镜像计划剩 qbittorrent-ee。

## 2026-10-18 应用镜像第四批（qbittorrent-ee）+ 本轮收尾

- qBittorrent-EE v5.2.4.10：官方 loongarch64-musl-static 包直装（sha256 与 API digest 一致）；镜像 289MB。
- 坑：5.x 的 Host header 校验会核对 Host 端口与容器监听端口，`-p 8089:8080` 裸 curl 返回 401；把 `--webui-port` 调成与映射端口一致即 200（或带匹配 Host 头）。
- 本轮共 12 只 loong64 应用镜像全部上架 Docker Hub（jellyfin/navidrome/vaultwarden/uptimekuma/mihomo/easytier/syncthing/adguardhome/memos/gogs/filebrowser/qbittorrent-ee），双 tag（`loong64` + `24.10-la5`）。

## 2026-10-19 应用镜像第五批（it-tools）

- it-tools v2024.10.22：纯静态 Vue；Vite 4.4.9 + rollup 3 在龙芯本机原生编译成功（没踩 rolldown 坑）；nginx 1.24（openEuler 源）+ SPA 回退；镜像 408MB，HTTP 200。已上架 Docker Hub。

## 2026-10-19 应用镜像第六批（excalidraw）

- excalidraw v0.18.1：Vite 5 + rollup 4，rollup 自带 loongarch64 binding，本机编成功。
- 坑一：/opt/node22 链接的是 app-compat glibc 2.28，加载 rollup loong64 binding 报 GLIBC_2.36 缺失；改 /opt/node22-abi2（glibc 2.41）。
- 坑二：esbuild 子进程被 GC 后随机 EPIPE，Vite 构建中途死；用 NODE_OPTIONS=--require 持有子进程引用解决。
- 镜像 439MB，HTTP 200 + SPA 深路径 200。已上架 Docker Hub（第 14 只，待 kopia 后统一记数）。

## 2026-10-19 应用镜像第七批（kopia）

- kopia v0.23.1：官方无 loong64 → 源码编（Go 1.25.11 自动工具链）。
- 真移植补丁（可上游）：loong64 的 syscall.Stat_t.Dev/Rdev 是 uint64，kopia 的 localfs 用 32/64 位 build tag 区分，需给 local_fs_64bit.go 加 `|| loong64`、local_fs_32bit.go 加 `&& !loong64`。
- Web UI 强制 Basic 认证：无凭据 401、带 admin/kopia 200，属设计行为。
- 镜像 317MB，已上架 Docker Hub（第 15 只）。

## 2026-10-19 应用镜像第八批（linkding，Python 栈首次打通）

- linkding v1.47.0：Python 3.13 源码编（openEuler 源只有 3.11）；uwsgi 2.0.31 源码编（PCRE 路由）；cryptography 50 无 loong64 wheel，用 openEuler rust+cargo+maturin 源码编过。
- 前端 esbuild 0.28 自带 linux-loong64 包，原生构建，无需跨架构。
- 两个坑：① Docker 默认 fd 上限巨大，uwsgi http 路由进程实测吃 8.1GB；`ENV UWSGI_MAX_FD=4096` 后 124MB；② 缺 /etc/mime.types 导致静态资源无 Content-Type，运行时补 mailcap。
- 镜像 1.21GB（完整 Python stdlib + rust 编译产物），可后续裁剪。已上架（第 16 只）。

## 2026-10-19 应用镜像第九批（heimdall，PHP 栈打通）

- Heimdall 2.8.3（linuxserver 版）：openEuler 源 PHP 只有 8.3.31，而上游要 ^8.4（Symfony 8.4 组件要 >=8.4.1），多阶段从 php.net 自编 PHP 8.4.26（含 sodium/intl/zip）；nginx+php-fpm。
- 数据持久化：/config/.env、app.sqlite、storage 三处软链；首请求自动迁移 seed。
- 镜像 691MB，HTTP 200。已上架（第 17 只）。

## 2026-10-19 应用镜像第十批（nextcloud，本轮最后一只大件）

- Nextcloud 33.0.10：PHP 8.3.31（openEuler 源，Nextcloud 33 支持 8.2–8.5）+ nginx/php-fpm，SQLite 测试部署。
- openEuler 的 php-pdo 同时给 sqlite3/pdo_sqlite；php-common 含 bz2/curl/exif；zip 来自 EPOL 的 php-pecl-zip；locale 用 glibc-locale-source + localedef 生成。
- 首次启动 entrypoint 生成 config.php（含 trusted_domains）并修属主；status.php 200、initial-state 无缺扩展。
- 镜像 1.48GB，已上架（第 18 只）。

## 2026-10-19 应用镜像第十一批（typecho）

- Typecho v1.3.0：PHP 8.3 + nginx/php-fpm + SQLite；安装向导完整走通（依赖检查/建库/管理员）。
- 注意：1.3.0 的 config.inc.php 与 typecho.db 在站点根目录，不在 usr 卷内；重建容器前要备份这两个路径。
- 镜像 428MB，已上架（第 19 只）。

## 2026-10-19 Jellyfin ImageSharp 编码器（缩略图恢复）

- 新增 src/Jellyfin.Drawing.ImageSharp（ImageSharp 2.1.11 + Drawing 1.0.0 + Fonts 1.0.0，Apache-2.0；刻意不用 3.x 的分裂许可）。
- 实现 IImageEncoder 全接口：GetImageSize/EncodeImage（EXIF 定向、裁剪缩放、质量、透明 PNG、未看角标/进度条）/CreateImageCollage/CreateSplashscreen/CreateTrickplayTile/GetBlurHash（纯 C#，与参考实现逐字符一致）。
- CoreAppHost 改三级注册：Skia → ImageSharp → Null。
- harness 全 PASS：尺寸识别、320 宽缩放、透明 PNG、方形/宽幅拼图（中文正常）、Trickplay 3x2、Splash 1920x1080；真照片库验证：BlurHash 入库、API 取图 160x120 JPG。
- 镜像补装 google-noto-cjk-fonts（中文库名拼图不再方框），jellyfin:loong64 已替换为 ImageSharp 版（旧版留 jellyfin:loong64-null-backup）。
- 差异：性能低于 Skia、无 ICC 色彩管理、输入无 SVG/DNG/RAW/ICO/AVIF、输出仅 JPG/PNG。

## 2026-10-19 应用镜像第十二批（wallabag）

- wallabag 2.6.14：release 自带 vendor 免 composer；PHP 8.3 + nginx/php-fpm + SQLite。
- 2.6 起无网页安装向导 → entrypoint 首次启动 CLI 安装；web 入口是 web/app.php（不是 index.php）；release 自带 parameters.yml 是 mysql 模板，必须删掉改由 entrypoint 生成 SQLite 配置；容器需 util-linux 才有 su。
- 镜像 688MB，登录/quickstart 验证通过，已上架（第 20 只）。

## 2026-10-19 应用镜像第十三批（drawio；zdinnav 判死）

- drawio v32.5.5：直接取源码仓库 `src/main/webapp`（预构建 app.min.js），nginx 静态服务，无需 npm/maven；镜像 498MB，首页与 10MB JS 均 200。已上架（第 21 只）。
- zdinnav：**无源码**。GitHub 仅 MyTkme/ZdinNav-Link（LuCI 包装，无应用本体），应用只以预构建 `tkme/zdinnav` 镜像分发（仅 amd64/armv7/arm64），无 loong64；技术栈 .NET+SqlSugar。判死（无源码不可移植），记档。

## 2026-10-19 应用镜像第十四批（jackett / xteve）

- Jackett v0.24.2867：.NET 9 源码编（framework-dependent + 内置运行时），`--NoUpdates` 防自替换；openEuler libstdc++ 缺 GLIBCXX_3.4.32（与 jellyfin 同因），内置 6.0.33；发布时用 /p:Version 修正 v0.0.0。
- xTeVe 2.2.0.200：Go 静态编；原依赖 x/sys（2020）无 loong64，升到 latest 后过；镜像含 ffmpeg 故 1.13GB。
- 两只已上架（第 22、23 只）。

## 2026-10-19 应用镜像第十五批（one-api / code-server / casaos）

- one-api v0.6.10：源码 web/build 只有 .gitkeep，需 Node 20 编三套主题后 embed；go-sqlite3 要 CGO，CGO_ENABLED=1 + `-linkmode external -extldflags '-static'` 静态链；镜像 294MB。
- code-server 4.141.0：**硬骨头啃下来了**。必须 Node 24（Node 20 报 `module.registerHooks` 缺失）；npm 包内 loong64 原生模块（argon2/node-pty/sqlite3/spdlog）本机编译通过；ripgrep 无 loong64，cargo 编静态版 15.2；镜像 1.11GB，200/302 验证。
- casaos：把验证过的 bundle 打成 `casaos:loong64`（528MB），entrypoint 无 systemd 启动 7 服务；`--privileged --network=host -v /var/run/docker.sock`，8081 端口，/ping pong、UI 200。
- 三只已上架（第 24、25、26 只）。

## 2026-10-19 应用镜像第十六批（dpanel/shiori/jellyseerr/audiobookshelf）

- dpanel v1.11.1：Go+CGO sqlite（CGO=0 启动 panic），需 openssh-clients（ssh-keygen 缺失会 panic）；566MB。
- shiori v1.8.0：Go 静态（osusergo,netgo,fts5）；290MB。
- jellyseerr v3.5.0：Next 16 默认 Turbopack 无 loong64 binding，回退 @next/swc-wasm-nodejs；sharp 无 loong64 且 wasm 需 SIMD（V8 不支持）→ images.unoptimized；1.56GB。
- audiobookshelf v2.37.1：sqlite3/nusqlite3 源码编；前端 Tailwind4 oxide 无 loong64 → x64 编 dist 回传；1.50GB。
- 四只已上架（第 27-30 只）。

## 2026-10-19 固件补 docker/podman 栈（发现并修复缺口）

- 发现：la5 rootfs 里 dockerd/docker/podman/runc/conmon/crun **一个都没有**——裸机固件上 iStore Docker 应用和 dockerman 实际不可用。
- 修复：config 加 dockerd/docker/containerd/tini（runc 用自编 1.6.0）；v2preset 预置 podman 5.8.8(CGO)/crun/conmon/glib2/libpcre2/libffi/runc + netavark/aardvark 二进制 + /etc/containers 配置；首启 enable dockerd、dockerman socket 改 /var/run/docker.sock。
- 编译坑：① feed libseccomp 无 loongarch 分支 → 去掉 runc/dockerd 的 seccomp 依赖与 tags（与自编 crun/conmon 同策略）；② feed runc 1.1.14 的 syscall_linux_64.go build tag 无 loong64 → 改用自编 runc 1.6.0；③ containerd 1.7.22 vendored cilium/ebpf 的 endian_le.go 无 loong64 → 补 build tag。
- rootfs 分区 1GB→1.5GB（docker 栈后 rootfs 正好顶满，make_ext4fs 段错误）。新镜像 395MB。

## 2026-10-19 应用镜像第十七批（calibre-web / homarr）

- calibre-web 0.6.27：Python 3.11 + venv；lxml/nh3/cryptography/netifaces/regex 无 loong64 wheel，Rust 源码编（OPENSSL_NO_VENDOR=1）；657MB。
- homarr v2.6.0：Bun/Turborepo 无 loong64 → pnpm 复现任务图；Next 16 WASM SWC + 补丁；@parcel/watcher 源码编；sharp 不可用 → images.unoptimized；openEuler 无 su-exec → setpriv；819MB。
- 两只已上架（第 31、32 只）。

## 2026-10-19 固件 docker/podman 收尾（la5 final）

- 最终镜像：398.5MB，md5 `a4d58f827fcb882bb46b9012d185c91e`，rootfs 分区 1.5GB（docker 栈后 rootfs 顶满 1GB，make_ext4fs 段错误）。
- 内容验证：dockerd/containerd/docker/ctr、/etc/init.d/dockerd、/etc/containers 配置、podman/crun/conmon/runc/glib2/pcre2/ffi ipk、netavark-bin.tar.gz、首启自动 enable dockerd。
- 关键教训：① 静态/动态 musl 二进制放进 package/files 会触发 OpenWrt ABI 依赖检查（libc.musl-* 无法满足），改为 tar.gz 首启解压；② 改包后必须跑 `make package/install` 再 `make target/install`，只跑后者会用旧 rootfs；③ feed runc 1.1.14 无 loong64 build tag、containerd vendored ebpf 无 loong64 endian、feed libseccomp 无 loongarch 分支——三处分别用自编 runc / 补 tag / 去 seccomp 解决。
- 盒子 `/var/tmp/personal-p1-20261019.img.gz` 已更新，U 盘可直接写。

## 2026-10-19 应用镜像第十八批（openwebui / kodexplorer）

- openwebui v0.12.3：官方轻量模式 USE_SLIM_DOCKER=true；torch/onnxruntime/whisper/ocr 等无 loong64 wheel，不装（聊天可用，本地 RAG/语音不可用）；编译型依赖优先用 openEuler 原生 RPM，其余源码编（pydantic-core/pycrdt/uuid-utils/google-re2）；pip 23.3 不识别 loongarch64 标签，maturin 轮子手工解包；1.8GB。
- kodexplorer 4.55：PHP 8.3 + nginx/php-fpm；125 个 PHP 文件语法检查全过；507MB。
- 两只已上架（第 33、34 只）。盒子 /var 一度 99%（他人 ha-build 占用），仅清构建缓存。

## 2026-10-19 公版 24.10-la5 发布 + 命名规范 + 清理

- 公版 la5（连续编号）：316MB img，rootfs 0.84GB（分区 1GB），内置 dockerd/containerd/docker/tini + podman 三件套/netavark；敏感串扫描（组网 secret、节点地址、.76、controller 密码）全空；English 默认、无 v2preset。
- 命名规范落盘 docs/NAMING.md：公版 laN 连续；私人 personal-pN-YYYYMMDD；Docker 双 tag（loong64 + 24.10-laN）；CasaOS 磁盘验证前不发布。
- 私人版本整理：p1 为最新；旧两版归档为 archive/personal-pre-p1-*.img.gz；删除 3.2GB 未压缩镜像。
- 清理：盒子 /var 100%→85%（23G 空闲）；本机 xfer-out 2.3G→113M；仓库目录 2.3G→871M；Docker Hub 删除空 casaos 仓库。
- Home Assistant Core 2026.10.2 镜像完成（2.53GB，Python 3.14 自编，全原生依赖源码编），已上架（第 36 只）。

## 2026-10-19 应用镜像第十九批（sonarr/radarr/tautulli/jellystat）

- Sonarr v4.0.20 / Radarr v6.4.4：.NET 9 SDK 发布 framework-dependent，RollForward=LatestMajor；最大坑是 Mono.Posix 无 loong64 原生库——自写 libMonoPosixHelper.so 兼容层（uname/stat/readlink/statvfs 等），两镜像共用；Radarr 的 SourceGear e_sqlite3 用 SQLite amalgamation 按同选项自编译。
- Tautulli v2.18.2：纯 Python；390MB。
- Jellystat 1.1.12：Vite 8 无 loong64 binding → 降 Vite 6 + Babel 插件；Node 20 不支持 require(ESM) → 后端改 CommonJS；**依赖外部 PostgreSQL**。
- 四只已上架（第 37-40 只）。

## 2026-10-19 应用镜像第二十批（prowlarr / bazarr）

- Prowlarr 2.6.5：.NET 9 发布 net8 framework-dependent + RollForward；自编 loong64 Mono.Posix（含 eglib）与 e_sqlite3；官方同版本前端静态资源；358MB。
- Bazarr 1.6.2：Python 3.11；lxml/Pillow 源码编；webrtcvad 加 __loongarch__ 分支；官方 release 的前端静态资源；含 ffmpeg/7za；2.28GB。
- 两只已上架（第 41、42 只）；已清理本地副本，盒子 /var 回到 90%（15G 空闲）。

## 2026-10-19 应用镜像第二十一批（gitea / miniflux）

- Gitea 28.2.0：官方 src 包自带前端 assets；Go 1.27.2 自编（盒子 1.24 低于 go.mod 要求）；modernc SQLite；入口脚本生成 app.ini（`GITEA__section__key` 环境变量实测不生效）；666MB。
- Miniflux 2.3.3：**上游已删除 SQLite 支持**（仅 PostgreSQL），测试用临时 PG 15.18 通过；镜像正常但必须外接 PostgreSQL；290MB。
- 两只已上架（第 43、44 只）。

## 2026-10-19 应用镜像第二十二批（portainer / nginx-proxy-manager）

- Portainer CE 2.45.2 LTS：Go 1.26 自编，前端 pnpm+webpack 本机构建；373MB。
- NPM v2.16.0：Vite 8/rolldown 无 loong64 → 前端在 x64 编 dist；Node 22-abi2；better-sqlite3/sqlite3/bcrypt 源码编；无 s6-overlay → 自写 entrypoint；stream 模块需 load_module；certbot 需显式 python3-acme；774MB。
- 两只已上架（第 45、46 只）。

## 2026-10-19 应用镜像第二十三批（firefly-iii / phpmyadmin，B 机构建）

- Firefly III v6.7.9：上游要求 PHP ≥8.5，openEuler 只有 8.3 → builder 阶段源码编 PHP 8.5.11；SQLite 61 迁移 + 9 seed 全过；821MB。
- phpMyAdmin 5.2.3：PHP 8.3 + nginx/php-fpm；首启需 `/run/php-fpm` 目录（entrypoint 已补）；581MB。
- 两只已上架（第 47、48 只）。B 机（172.16.100.66）通过 A 机跳板访问；工具链 Go 已装，Node/.NET 传输中。

## 2026-10-19 B 机续作（freshrss 修复 / paperless 重建）

- FreshRSS 1.30.1：首次构建用了官方 Dockerfile 导致 entrypoint 缺失；改用仓库自带 Dockerfile，并补 data/{favicons,users,cache,logs,tokens} 目录初始化；302 正常、无告警；已上架（第 49 只）。
- Paperless-ngx 2.20.15：首次镜像入口是 `/init`（s6-overlay，loong64 无），已用自带 Dockerfile 重建中；重建完成后验证，未完成前不发布。
- 网关 502 多次打断子代理；改为主会话直接操作 B 机（经 A 跳板）。

## 2026-10-20 A 机独占、CasaOS P3 磁盘复测、Homer

- A 机（192.168.8.8）成为唯一开发/验证机，B 机（172.16.100.66）移交 NAS 会话。
- 清理：`docker builder prune` 回收 13.88G、删除悬空镜像；`/var/tmp` 构建上下文归档到 `/build/appimages`；`/var` 可用 16G→41G。
- p4（原为空的 `backupfs`，fstab 曾 `noauto` 挂 `/restore`）改为 `/build`（37.5G），fstab 备份 `/etc/fstab.bak-20261020`。
- CasaOS P3 用 8G 文件型 NBD 盘复测：挂载、写入/读回、`DELETE /v1/storage` 卸载、local-storage 重启后按 UUID 自挂、`PUT /v1/storage` 格式化全部通过。
- 磁盘过滤：loop/dm/ram 被 `lsblk` 默认排除或 `IsDiskSupported` 白名单挡住；NBD 虽可通过 `POST /v1/storage` 直接挂载，但不会出现在 `/v1/disks`。真实 sata/nvme 盘仍需实测。
- **P3 打包缺陷**：安装包漏 `share/shell/local-storage-helper.sh`，挂载/格式化报 `exit 127 do_mount: 未找到命令`。已补上游脚本并重打 tarball，sha256 `6efcbb60…7bea`（旧 `54fdd97a…b2b3` 作废）。
- **上游边界问题**：格式化后旧 UUID 行残留在 `o_disk`（`DeleteMountPointFromDB` 按 UUID+mount_point 过滤，不按挂载点清理）；重启仍按新 UUID 挂载，但记录会累积。
- Homer v26.08.3：openEuler nginx 1.24 + 官方静态包，8080，HTTP 200；已推送 `yunixintel/homer:loong64`/`24.10-la5`，digest `sha256:4b3f0e96…3244c`。
- Paperless-ngx 3.3.2 完成（2.53GB，已推送）：
  - openEuler 24.03 只有 qpdf 11.1，pikepdf 10.17 需要 qpdf 12 API → 多阶段源码编 qpdf 12.4.2，装到 `/usr/local/lib`，`ldconfig` 注册。
  - lxml 6.0.3 在构建隔离里仍退化为 sdist（Cython 源码编）；补 `libxml2-devel libxslt-devel` 后可过；Brotli 1.2.0 源码编也通过。
  - 入口补齐 `document_consumer` 与 `celery beat`（否则消费目录不处理）；Redis 启动竞态加 `redis-cli ping` 等待。
  - `en_US.UTF-8` 未生成导致 Redis 以 “invalid locale” 退出 → 镜像与 Redis 改用 `C.UTF-8`。
  - tesseract 语言包在 `/usr/share/tesseract/tessdata`，而 tesseract 5.3 默认找 `/usr/share/tessdata` → 逐文件链接 eng/chi_sim，并补 `tesseract-osd`（方向检测）。
  - 验证：登录页 200；OCR 输出 “Paperless OCR 12345”；消费入库 `document_id=1`；容器重启后文档仍在。
  - 镜像 `arch=loong64 os=linux size=2531968459`；已推送 `yunixintel/paperless-ngx:loong64`/`24.10-la5`，digest `sha256:33fbcdcb…195b4`。
  - Hub 凭据：从本机 Docker Desktop 凭据助手导出，写入 A 机 `/root/.docker/config.json`（0600）；未在日志/终端输出 secret。
- Dashy 4.8.0：官方 release 自带预构建 `dist/`，直接 openEuler nginx 1.24 静态托管；379MB，HTTP 200，`/conf.yml` 200；8080。
- Watchtower v1.7.1：Go 1.24 本机静态编，scratch + CA 证书；14.7MB；`--run-once --label-enable` 扫描 0、无更新；需挂 docker.sock。
- changedetection.io 0.60.9：3.51GB（Firefox + SSIM + Selenium steps 版），已推送 `yunixintel/changedetection:loong64`/`24.10-la5`，digest `sha256:4ff22d22…f6c4`。
  - `jq` 1.13 内置 oniguruma 的旧 `config.sub` 不认 loongarch64 → 用 automake 1.16 新版 `config.guess/config.sub` 替换嵌套 tarball，并在 configure 加 `--build=loongarch64-unknown-linux-gnu`，预编本地 wheel 后接入 `--find-links`。
  - 完整 requirements 安装成功（含 litellm 1.91.5、selenium、pyppeteer-ng、tokenizers loongarch wheel）。
  - **Firefox 支持**：修改 `webdriver_selenium.py`，新增 `WEBDRIVER_BROWSER=firefox` 分支（保留 Chrome 远程分支）；Firefox 140.11ESR 来自 openEuler，geckodriver 0.37.1 在 openEuler 24.03 容器内用 Rust 1.99 编（避免 Loongnix glibc 2.41 与镜像 2.38 不兼容）。
  - **OpenCV/SSIM**：openEuler `opencv` 4.5.2 包自带 cv2，但只兼容 numpy 1.x；venv 降级 `numpy==1.26.4` 并把系统 `cv2` 复制进 venv，设 `DISABLED_PROCESSORS=""` 启用 `image_ssim_diff`。
  - 验证：`html_webdriver` + Firefox 对 example.com 落盘 `last-screenshot.png` 100KB；`image_ssim_diff` 首次保存 baseline、二次检测截图未变并跳过比较，无 cv2 报错；UI 200、worker 正常。
  - **Selenium 浏览器步骤**：`supports_browser_steps=True`；在 webdriver fetcher 内实现 `_run_browser_steps`（Goto/点击/输入/等待/选择/按键/滚动/JS/复选框/iframe 等），并修改 `resolve_content_fetcher`，有 browser_steps 时不再强制切 Playwright。Selenium 官方 web-form 4 步（等待/输入/点击/等待）通过，最终 HTML 出现 `Form submitted`/`Received`，步骤截图与 HTML 全部落盘。
  - 限制：未实现的步骤操作会 warning 跳过；Chrome 远程仍可用 `WEBDRIVER_BROWSER=chrome` + `WEBDRIVER_URL`。
- Caddy v2.11.7：Go 1.24 本机静态编（55MB），scratch + CA；镜像 57MB；默认 Caddyfile 监听 8080，`caddy version` 与 HTTP 200 均通过；已推送 `yunixintel/caddy:loong64`/`24.10-la5`，digest `sha256:8343b2f3…1ec3`。
- Dozzle v11.3.3：前端用 Bun 1.4.3 在 x86 WSL2（Ubuntu 26.04）按上游锁文件构建 `dist`（692 文件，40.81MB→Brotli 7.30MB），无运行时 sidecar；Go 1.27.2 在 A 编 `linux/loong64` 静态二进制（68MB），scratch 镜像 68MiB。
  - Docker Desktop 因残留 AF_UNIX socket（`sailor-ingest.sock`、`engine.sock`）无法启动，改用 WSL2 只做构建期前端编译。
  - 验证：`--version` = v11.3.3、`--help` 退出 0、容器 HTTP 200、日志 `Connected to Docker`。
  - 已推送 `yunixintel/dozzle:loong64`/`24.10-la5`，digest `sha256:35d69438…96a5`；scratch 无 shell，版本串 v11.3.3。
- ntfy v2.32.0：前端 Vite 8 在 x86 WSL2（Node 22）构建（A 上缺 `rolldown-binding.linux-loong64-gnu.node`），Go 端 `go:embed server/site`；**go-sqlite3 需要 CGO**，在 openEuler 24.03 容器内用 Go 1.27.2 + gcc 编，避免宿主 glibc 2.41 与镜像 2.38 不兼容。
  - 启动参数是 `ntfy serve --listen-http 0.0.0.0:8080`（不是 `--listen`）。
  - 验证：`/v1/health` 返回 healthy、UI 200、`PUT/POST /test-topic` 发布成功；日志显示 `ntfy v2.32.0`。
  - 镜像 274MB，已推送 `yunixintel/ntfy:loong64`/`24.10-la5`，digest `sha256:100a53b1…bc05`。
- Gotify v3.1.1：UI 是 Vite 8，WSL2 x86 + Node 22 + yarn 构建（`ui/build`）；Go 端 go-sqlite3 需 CGO，在 openEuler 24.03 容器内用 Go 1.27.2 + gcc 编，ldflags 注入 `v3.1.1`/buildDate。
  - 运行时使用 `GOTIFY_SERVER_PORT=8080`、`GOTIFY_DATABASE_DIALECT=sqlite3`、`GOTIFY_DATABASE_CONNECTION=/data/gotify.db`。
  - 验证：`/health` 返回 `{"health":"green","database":"green"}`、UI 200、`/version` 为 v3.1.1。
  - 镜像 261MB，已推送 `yunixintel/gotify:loong64`/`24.10-la5`，digest `sha256:a6b33306…467e`。
- Node Exporter 1.12.1：纯 Go 静态编，scratch + CA，17MB；`/metrics` 200，`node_cpu_seconds_total` 正常；已推送 `yunixintel/node-exporter:loong64`/`24.10-la5`，digest `sha256:8739c40b…febd`。
- Prometheus 3.15.0：UI 用 pnpm 工作区 + Vite 8 在 x86 WSL2 构建（`web/ui/static` 13MB），Go 端必须加 `-tags builtinassets` 才会嵌入 UI；不加时出现 UI 500、`/static/...` 404。
  - `scripts/compress_assets.sh` 生成 `web/ui/embed.go` 和 gzip 资源后，再 `go build -tags builtinassets`。
  - 验证：`/-/healthy` 200、UI 200（标题 `Prometheus Time Series Collection and Processing Server`）、`/api/v1/status/buildinfo` 3.15.0。
  - 镜像 407MB，已推送 `yunixintel/prometheus:loong64`/`24.10-la5`，digest `sha256:4db755ff…e1ee`。
- Pi-hole FTL v6.8 / web v6.6.1：开始移植。FTL 是 C/C++ + 内置 dnsmasq/Lua/SQLite，web 为 `.lp` 模板 + 静态资源（无需 Node 构建）。
  - 构建坑：openEuler EPOL/debuginfo metalink 404 导致 dnf 长时间重试 → 禁用仓库并限重试；`docs.h` 资源需要 `xxd`（在 `vim-common`）；FTL 需要 nettle 3.9+ 的 `balloon.h`，openEuler 3.8.1 不够 → 源码编 nettle 3.10 到 `/usr/local`。
  - `-Werror` 在龙芯上把 dnsmasq/生成 docs 的警告变错误 → CMake 里改 `-Wno-error`。
  - 完成：FTL 6.8 + web 6.6.1，nettle 3.10.2 静态编入；首启用干净 `gravity.db.sql` 创建 gravity.db；接入上游 `pihole` CLI/`gravity.sh` 和 `pihole-adlist` 管理脚本；镜像 287MB。
  - 验证：`/admin/` 200；`pihole -g` 拉取本地 adlist 并解析 1 条；`dig` 被拦截域名返回 NXDOMAIN，普通域名正常解析。
  - 已推送 `yunixintel/pihole:loong64`/`24.10-la5`，digest `sha256:67e543a2…2e2a`；FTL 自报 `UNKNOWN (not a GIT build)`（源码构建，不影响运行）。
- Gatus 5.37.0：Go 静态编，`web/static` 随仓库提供（无需 Node）；scratch + CA + 默认 config，镜像 35.5MB。
  - 验证：`/` 200、`/api/v1/endpoints/statuses` 200；默认配置监控 `http://127.0.0.1:9090/-/healthy`。
  - 已推送 `yunixintel/gatus:loong64`/`24.10-la5`，digest `sha256:335d7c74…92c6`。
- Alertmanager 0.34.1：Web UI 是 Elm 0.19.1 + Vite 8（`ui/app`），Go 端 `//go:embed app/dist`；`ui/mantine-ui/` 在该 tag 未接入构建，忽略。
  - 前端在 x86_64 WSL2（Node 22.23.3）执行 `npm ci && npm run build`，Elm 编译 84 个模块，Vite 只留 `.gz`/`.br` 压缩资源（`deleteOriginalAssets: true`）。
  - 龙芯端 `CGO_ENABLED=0 -tags netgo` 编 `alertmanager`/`amtool`，ldflags 注入 0.34.1；`amtool check-config` 通过。
  - 镜像 openEuler 24.03 + curl + tzdata + CA，以 `65534:65534` 运行，274MB。
  - 验证：`/-/healthy`、`/-/ready` 200；UI 200；`/api/v2/status` 正常；`amtool alert add` 的告警在 `/api/v2/alerts` 可检索；首启 `gossip not settled` 十余秒后收敛。
  - 已推送 `yunixintel/alertmanager:loong64`/`24.10-la5`，digest `sha256:6f46a30d…8fca`。
- PostgreSQL 15.18：官方镜像无 loong64，改用 openEuler 24.03 SP4 的 `postgresql-server` + `postgresql-contrib`。
  - entrypoint 首次 `initdb`（UTF8/C.UTF-8），用临时 `--pwfile` 设置密码后立即删除；创建 `POSTGRES_DB`；追加 `host all all all` 认证规则；关闭 `logging_collector` 保持 stdout 日志。
  - 用 util-linux `runuser` 降权到 UID 26；镜像 378MB；数据目录 `/var/lib/postgresql/data`。
  - 验证：`pg_isready` healthy、SCRAM TCP 登录、重启后表数据仍在；miniflux 连接该库完成 132 个迁移，首页 200。
  - 已推送 `yunixintel/postgres:loong64`/`24.10-la5`，digest `sha256:c94527ee…825b`。
- Redis 7.2.14：openEuler 包构建，AOF+RDB，`/data` 持久化。
  - entrypoint 支持 `REDIS_PASSWORD`（追加到临时配置副本），用 `runuser` 降权到 UID 998。
  - 验证：`PING`、`SET/GET`、重启后值仍在、无密码时 `NOAUTH`、带密码 `PONG`、健康检查 healthy。
  - 镜像 296MB；已推送 `yunixintel/redis:loong64`/`24.10-la5`，digest `sha256:424db4cd…3137`。
- Mosquitto 2.0.20：openEuler EPOL 包，`mosquitto` 包本身已包含 `mosquitto_pub`/`mosquitto_sub`/`mosquitto_passwd`（没有单独的 `mosquitto-clients` 包，写了会构建失败）。
  - 默认配置 `persistence true` + `log_dest stdout` + `listener 1883` + `allow_anonymous true`；entrypoint 用 `runuser` 降权到 UID 998。
  - 健康检查用 bash `/dev/tcp`，不依赖客户端命令。
  - 验证：匿名 pub/sub 成功；retained 消息在容器重启后仍能订阅；健康检查 healthy。
  - 镜像 290MB；已推送 `yunixintel/mosquitto:loong64`/`24.10-la5`，digest `sha256:d55c5799…edce`。
- MariaDB 10.11.18：openEuler 包构建，entrypoint 首次 `mariadb-install-db` 后起临时 `--skip-networking` 实例，用 socket 完成 root 密码、`MYSQL_DATABASE`、`MYSQL_USER` 与授权，再降权到 UID 27 启动。
  - 踩坑：MariaDB 不接受 `IDENTIFIED BY 0x...` 十六进制字面量；改为 `SET SESSION sql_mode=...,NO_BACKSLASH_ESCAPES` + 单引号加倍，含引号/反斜杠/空格的密码均验证通过。
  - 日志：`/var/log/mariadb/mariadb.log` 在镜像内软链到 `/dev/stderr`，避免 `--log-error=/dev/stderr` 触发 `/dev/stderr.err` 警告。
  - 客户端 socket 统一为 `/run/mysqld/mysqld.sock`，镜像内 `container-client.cnf` 让 `mariadb` 命令无需额外参数。
  - 验证：初始化、root/app TCP 登录、建表、重启持久化、健康检查 healthy。
  - 镜像 549MB；已推送 `yunixintel/mariadb:loong64`/`24.10-la5`，digest `sha256:bf37b65e…5e00`。
