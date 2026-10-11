# 摩尔线程 MTT S80 的 LoongArch 驱动

### 能不能自己开发 · 能不能用 S30/S50 的改 · 官方驱动从哪拿

---

调研日期：**2026-10-11** ｜ 方法：**官方站点接口实调 + 驱动包下载解剖 + 源码级逐字节比对**

> **本报告的全部技术结论均来自实物证据**（厂商发行的二进制包、驱动源码、官方页面内嵌数据），不依赖二手报道。原始证据与解析脚本见 `dl/`、`src_all/`、`raw/`、`scripts/`。

---

## 目录

1. [结论速览](#一结论速览)
2. [调研方法与取数路径](#二调研方法与取数路径可复现)
3. [S80 驱动包解剖](#三s80-驱动包解剖)
4. [跨架构移植的真实缺口](#四跨架构移植的真实缺口源码级)
5. [芯片族与统一驱动模型](#五芯片族与统一驱动模型)
6. [LoongArch 现状：官方口径与实物](#六loongarch-现状官方口径与实物)
7. [龙芯驱动的官方获取入口](#七龙芯驱动的官方获取入口已定位)
8. [「网上有人说驱动成功过」怎么判](#八网上有人说驱动成功过怎么判)
9. [能不能用 S30/S50 的驱动带 S80](#九能不能用-s30s50-的驱动带-s80)
10. [三条路线的裁决](#十三条路线的裁决)
11. [分步操作清单](#十一分步操作清单)
12. [顺带发现](#十二顺带发现)
13. [证据文件索引](#十三证据文件索引)
14. [修订记录](#十四修订记录)

---

## 一、结论速览

### 一句话

> **S80 的 LoongArch 驱动不是「技术难题」，是「一份二进制没发」。**
> 开放部分（内核模块脚手架、显示/音频/VPU 驱动、固件、DRM UAPI）已全部随 amd64 包发布，甚至 LoongArch 专用代码都写好了；闭源核心按架构预编译。而**厂商手里那份东西大概率是可以拿到的**——摩尔线程自己的官网就挂着集成驱动的**龙芯镜像下载入口**。

### 判据表

| 问题 | 结论 | 证据强度 |
|---|---|---|
| S80 有公开的 LoongArch 驱动吗？ | **没有** | 官方下载站、开发者站、龙芯/麒麟/UOS 公开仓全扫，零命中 |
| 能自己从源码编译出来吗？ | **不能**。缺 `objs/loongarch64/mtgpu_core.o_binary`，且无法从源码生成 | 源码级确证：`Makefile` 只有 symlink 规则，`src/` 下无 PVR 核心实现 |
| S80 的驱动是开源的还是闭源的？ | **混合**：内核模块脚手架全部开源（Dual MIT/GPLv2，随包发布），**唯一闭源件是一枚按架构预编译的 blob** | 包内 `/usr/src/mtgpu-3.0.0/` 12MB C 源码 + `objs/x86_64/mtgpu_core.o_binary` |
| 跨架构移植的工作量大吗？ | **只差一枚 blob + 一行 `ARCH=` + 一套用户态 .so**。am64 与 arm64 两个包的开放源码**逐字节相同** | SHA256 全等比对 |
| S80 和 S50 是同一颗芯片吗？ | **不是**。S50 = SUDI104「苏堤」，S80 = QUYUAN1「曲院1号」 | `mtgpu_pci_tbl` + `mtgpu_defs.h` |
| 那 S50 的驱动能带 S80 吗？ | **很可能不用改就能带**。驱动是「每架构一份、全芯片族统一」（S80 与 X300 的 x86 包整包 SHA256 完全相同），PCI 匹配表在**开放源码**里且含 S80 的 `0x0201` | 整包哈希 + 统一设备表 |
| 网上能拿到 S30/S50 的龙芯驱动吗？ | **能，而且是官方入口**。MT 官网挂着含驱动的 UOS 龙芯镜像链接（附提取码） | 官网内嵌数据 + 官方文档 + 统一FAQ |
| S80 在龙芯上「成功过」的说法可信吗？ | 需要分级。能查到的都是 2023 年底 B 站的「兼容/点亮、**驱动没开放**」；按包结构，真做出来的人只能拿到厂商内部构建 | 见 [第八节](#八网上有人说驱动成功过怎么判) |

---

## 二、调研方法与取数路径（可复现）

### 2.1 摩尔线程驱动中心（`www.mthreads.com/pes/`）

该站是**静态导出的 Next.js 应用**（`nextExport: true`，`assetPrefix: "/pes"`），页面自带客户端签名算法：

| 用途 | 请求 |
|---|---|
| 产品 × 操作系统矩阵 | `GET /pes/drivers/search/` → `__NEXT_DATA__` 内嵌完整树 |
| 某产品某系统的版本列表 | `GET /pes/drivers/driver-info?productType=DESKTOP&productModel=<PM>&osVersion=<OS>` |
| 下载直链 | `GET /pes/front/pes/driver/log/<driverId>` |

**注意**：路径**末尾带斜杠会 308 重定向**到不带斜杠的形式；不带斜杠才能拿到 200。

签名算法（硬编码在 `/_next/static/chunks/pages/drivers/driver-info-*.js` 里）：

```js
sign = md5("website" + "3fi2yim8agwxuol1sds0wcmirq0cg1l3" + timestamp + nonce + "1.0")
// headers: { appId: "website", timestamp, nonce, sign }
```

返回的 `fileNameUrl` 指向**火山 TOS 桶，无需鉴权即可下载**（示例密钥形如
`privacy/pes/uploaded/driver/2025/04/29/g5ivtdq5air.deb`）。

### 2.2 摩尔线程开发者站（`developer.mthreads.com`）

`/drivers/2077283971481341952` 是 MUSA SDK / 工具下载枢纽，`__NEXT_DATA__` 里含 **93 条**资源的完整记录（`title`、`download`、`downloadPrivacy`、`downloadSize`、`equipment`、`os`、`driverVersion`、`instructions`、`systemInfo`）。

其文件同样在火山 TOS 桶，且**匿名可直接下载**：

```
https://mt-website-prod.tos-cn-beijing.volces.com/privacy/developer/resource/download/<路径>
```

### 2.3 自有脚本

| 脚本 | 作用 |
|---|---|
| `scripts/fetch_driver.py` | 复刻 pes 签名，取任意驱动版本的真实下载直链 |
| `scripts/read_deb.py` | **纯 Python 解 `.deb`**（ar 容器 + tar.xz），`list` / `ls` / `cat` / `x` 四个子命令，不依赖 `dpkg` / `ar` / `7z`（Windows 上也能用） |

---

## 三、S80 驱动包解剖

### 3.1 版本历史与命名

S80 的 Linux 驱动**只有三个版本**（`driver-info?productModel=DESKTOP_MTT_S80&osVersion=MTT_S80_Ubuntu`）：

| 版本 | 发布日期 | 文件大小 | 包名 |
|---|---|---|---|
| **v3.0.0** | 2025-04-29 | 93 MB | `musa_3.0.0-pc.amd64.deb`（实测 97,903,324 B） |
| v2.5.0 | 2024-02-20 | 40 MB | `musa_2.5.0-Ubuntu_amd64.deb` |
| v2.1.0 | 2023-07-04 | 42 MB | `musa_2.1.0-Ubuntu_amd64.deb` |

**对照 X300（同一 v3.0.0 时点）**：

| 版本 | x86 | arm64 |
|---|---|---|
| v3.1.0（2025-06-12） | `musa_3.1.0-pc_x86.deb` 88MB | 80MB |
| v3.0.0（2025-04-29） | 93MB | `musa_3.0.0-pc.arm64.deb` 89,303,112 B |

**命名规律**：`musa_<版本>-<发行版标签>_<架构>.deb`。所以一个 LoongArch 构建应形如 `musa_<ver>-<distro>_loongarch64.deb`。

### 3.2 包元数据

```deb
Package: musa
Version: 3.0.0-pc
Architecture: amd64
Depends: libdrm2 (>= 2.4.97), dkms, libgles2
Conflicts: mtsnd, mtgpu, musa-wine, musa_all-in-one
Replaces: mtsnd, mtgpu, musa-wine, musa_all-in-one, linux-firmware, musa (<< 3.0.0)
Installed-Size: 821978
```

两条关键信息：

1. **`Depends: dkms`** —— 内核模块以**源码形式**随包分发，在目标机本机编译。
2. **`Conflicts` / `Replaces: mtsnd, mtgpu, musa-wine`** —— 这几个正是发行版仓库里拆分打包的旧包名（见 [§7](#七龙芯驱动的官方获取入口已定位)）。**说明 `musa` 是同一产品线的新统一包。**

### 3.3 分层结构

| 层 | 内容 | 架构相关？ | 源码可得？ | 许可 |
|---|---|---|---|---|
| **GPU 固件** | `/lib/firmware/mthreads/` | **否**（下载到卡上运行） | 二进制（固件本就如此） | 专有 |
| **内核模块脚手架** | `/usr/src/mtgpu-3.0.0/` 共 12 MB C 源码 | 是（每架构一个 `osfunc_*.c`） | **是，随包发布** | **Dual MIT/GPLv2** |
| **内核模块核心** | `objs/<ARCH>/mtgpu_core.o_binary` | **是，按架构预编译** | **否 —— 唯一闭源件** | 专有 |
| **用户态** | `/usr/lib/<triple>/` 下 60 个 `.so` | 是（二进制） | 否 | 专有（含 Mesa 分支） |
| **计算栈** | MUSA SDK（2–4 GB） | 是，按 host CPU 构建 | 否 | 专有 |

### 3.4 闭源件的物证

| | S80 amd64 包 | X300 arm64 包 |
|---|---|---|
| 路径 | `objs/x86_64/mtgpu_core.o_binary` | `objs/arm64/mtgpu_core.o_binary` |
| 大小 | 5,806,664 B | 6,415,416 B |
| `e_type` | 1（`ET_REL`，可重定位目标文件） | 1（`ET_REL`） |
| `e_machine` | **0x3E**（x86-64） | **0xB7**（aarch64） |
| `dkms.conf` 的 `MAKE` | `make ARCH=x86_64 KERNELVER=$kernelver` | `make ARCH=arm64 KERNELVER=$kernelver` |

`mtgpu_core.o_binary` 在链接时被 `symlink` 成 `mtgpu_core.o`，与 60 多个开放 `.o` 一起链进 `mtgpu.ko`。它对应的是 **Imagination PowerVR 的闭源内核服务层**（`pvrsrvkm`），与 Imagination 的商业模式一脉相承。

### 3.5 用户态清单

全部位于 `./usr/lib/x86_64-linux-gnu/`（60 个）与 `./usr/lib/xorg/`（4 个）：

| 类别 | 文件 |
|---|---|
| **Mesa 分支** | `libGL_MUSA_MESA.so`、`libGLESv1_CM_MUSA_MESA.so`、`libGLESv2_MUSA_MESA.so`、`libglapi_musa.so`、`kms_swrast_musa_dri.so`、`libmusa_dri_support.so`、`libmusa_mesa_wsi.so` |
| **GLX / EGL / GBM** | `libGLX_mtgpu.so`、`libEGL_mtgpu.so`、`libmusa_gbm.so` |
| **Vulkan** | `libVK_MT.so`、`libMT_SPIRV-Tools.so` |
| **DRM** | `libdrm_mtgpu.so` |
| **图形 / 编解码** | `librogue2d_api_MUSA.so`（PowerVR Rogue 2D API）、`libencode_musa.so`、`libcapture_musa.so` |

另有 `/usr/bin/mthreads-gmi`（6.8 MB 管理工具）、`/usr/local/{musa, mt_vaapi}/` 等安装位。

**架构判断**：MTT 的 GPU 是 **Imagination PowerVR Rogue 血统** —— 源码树里 `inc/pvr/`、`inc/imgtec/`、`rgx_*` 系列文件（`rgx_fwif_km.h`、`rgxcore_km_*.h`、`rgx_bvnc_defs_km.h`）是 IMG 的驱动框架，用户态还有 `librogue2d_api_MUSA.so`。

### 3.6 固件（架构无关，无需移植）

```
mtfw-gen1.bin .. mtfw-gen6.bin     199512 / 222428 / 231688 / 207776 / 207412
mtfw-gen4rv.elf  1210872           mtfw-gen6rv.elf  1236464
mtlog-gen1..6.dict（日志字典）
mtvpu-00-1.0.bin / mtvpu-01-{1.0,2.0,3.0}.bin / mtvpu-02-{1.0,2.0,3.0}.bin
musa.fw.{1.0.0.0,1.1.0.0,1.1.1.0,2.0.0.0}   musa.sh.1.0.0.0（1786672）
```

一个包装了 **6 代 GPU 固件 + 3 版 VPU 固件** —— 这本身就是「一枚驱动通吃多代芯片」的旁证。

---

## 四、跨架构移植的真实缺口（源码级）

### 4.1 `Makefile` 已有 LoongArch 分支

**`Makefile` 第 83–88 行**：

```make
mtgpu-$(CONFIG_RISCV)     += src/pvr/osfunc_riscv.o
mtgpu-$(CONFIG_ARM)       += src/pvr/osfunc_arm.o
mtgpu-$(CONFIG_ARM64)     += src/pvr/osfunc_arm64.o
mtgpu-$(CONFIG_LOONGARCH) += src/pvr/osfunc_loongarch.o \
                             src/mtgpu/dmi_loongarch.o
mtgpu-$(CONFIG_X86)       += src/pvr/osfunc_x86.o
```

**`Makefile` 第 119–129 行**（缺口所在）：

```make
MTGPU_BINARY   := $(OBJ_DIR)/objs/$(ARCH)/mtgpu_core.o_binary
MTGPU_BINARY_O := $(OBJ_DIR)/objs/$(ARCH)/mtgpu_core.o

$(MTGPU_BINARY_O): $(MTGPU_BINARY)
	$(call if_changed,symlink)      # ← 只有 symlink 规则，没有任何编译规则
```

`objs/` 下**只有 x86_64 一个目录**。而这个 blob **无法从源码生成**：`src/pvr/` 下只有 `osfunc*.c`、`pvr_drm.c`、`physmem_osmem_linux.c`、`pmr_os.c`、`pvr_fence.c` 等**外壳/适配层**；真正的大块实现（srvcore / rgx / mmu / sync / devicemem / tlstream）**在 `inc/pvr/services/*.h` 里只有声明，没有实现**。

### 4.2 LoongArch 专用代码已经写好（MIT/GPLv2）

**`src/pvr/osfunc_loongarch.c`**（2,206 B，`@License Dual MIT/GPLv2`）—— 不是占位符：

```c
void OSCPUCacheFlushRangeKM(PVRSRV_DEVICE_NODE *psDevNode, void *pvVirtStart, ...)
{
	/* dev must be pcie device */
	dev = psDevNode->psDevConfig->pvOSDevice;
	dev = dev->parent->parent;
	dma_sync_single_for_device(dev, sCPUPhysStart.uiAddr, ..., DMA_TO_DEVICE);
	dma_sync_single_for_cpu(dev, sCPUPhysStart.uiAddr, ..., DMA_FROM_DEVICE);
}

OS_CACHE_OP_ADDR_TYPE OSCPUCacheOpAddressType(void)
{
	return OS_CACHE_OP_ADDR_TYPE_PHYSICAL;   /* LoongArch 需用物理地址做 cache 操作 */
}

IMG_BOOL OSIsWriteCombineUnalignedSafe(void) { return IMG_TRUE; }
```

**`src/mtgpu/dmi_loongarch.c`**（477 B，同样 MIT/GPLv2）—— LoongArch 的 DMI 访问需要绕：

```c
void __init __iomem *dmi_remap(u64 phys_addr, unsigned long size)
{
        return ((void *)TO_CAC(phys_addr));   /* LoongArch 一致性别名窗口 */
}
void dmi_unmap(volatile void __iomem *addr) { }
```

**`src/mtgpu/mtgpu_drv.c` 第 27–31 行**：

```c
#ifndef CONFIG_LOONGARCH
#include <asm/dmi.h>
#else
#include "dmi_loongarch.h"
#endif
```

全树 grep `loongarch` 只有 3 个文件命中：`Makefile`、`src/mtgpu/dmi_loongarch.c`、`src/mtgpu/mtgpu_drv.c`。

**这三个文件出现在 x86 的发行包里，只能有一个解释：摩尔线程内部已经用这套源码在 LoongArch 上构建过（并跑通过），只是没对外发布 S80 的构建产物。**

### 4.3 amd64 与 arm64 两个包的开放源码逐字节相同

| 文件 | S80 (amd64) | X300 (arm64) | 一致？ |
|---|---|---|---|
| `Makefile` | `7d013a0b2875` | `7d013a0b2875` | **YES** |
| `src/mtgpu/mtgpu_drm_drv.c` | `e08edd7eaa1b` | `e08edd7eaa1b` | **YES** |
| `src/mtgpu/dmi_loongarch.c` | `4ff256a42443` | `4ff256a42443` | **YES** |
| `src/pvr/osfunc_loongarch.c` | `de7f59833f5a` | `de7f59833f5a` | **YES** |
| `src/pvr/osfunc_x86.c` | `f5397dfdf654` | `f5397dfdf654` | **YES** |
| `src/pvr/osfunc_arm64.c` | `c05179f6a77c` | `c05179f6a77c` | **YES** |

（SHA256 前 12 位）

**结论：同一棵架构中立的源码树，换一枚 blob 就换一个架构。**

### 4.4 缺口的精确清单

若要让 S80 驱动跑在 LoongArch 上，需要三件东西：

| # | 缺什么 | 卡在哪 |
|---|---|---|
| 1 | `objs/loongarch64/mtgpu_core.o_binary` | **闭源、按架构预编译，无法自行生成** |
| 2 | `dkms.conf` 的 `ARCH=loongarch64` + `postinst` 的架构白名单（现只认 `x86_64`/`i686`） | 同一文件在 arm64 包里已改成 `ARCH=arm64`，照抄即可 |
| 3 | `usr/lib/loongarch64-linux-gnu/*.so`（60 个） | 闭源用户态；但 MTML 已出过 loongarch64 |

---

## 五、芯片族与统一驱动模型

### 5.1 `mtgpu_pci_tbl`：一张统一设备表

`src/mtgpu/mtgpu_drv.c:411` 起，厂商 ID `PCI_VENDOR_ID_MT = 0x1ED5`：

| 芯片族 | 族基址 | 产品 | 设备 ID | `driver_data` |
|---|---|---|---|---|
| **SUDI104「苏堤」** | 0x0100 | SUDI104 / S10 / S30(2Core) / **S30(4Core)** / S1000M / **S50** / S60 / X100 / S100 / S1000 / S2000 | 0x0100 / 0x0103 / **0x0105** | `sudi_drvdata` |
| **QUYUAN1「曲院1号」** | 0x0200 | **S80** / S70 / X300 / S3000 / S3000E-8CORE / S3000E-7CORE | **0x0201** / 0x0202 / 0x0211 | `quyuan1_drvdata` |
| **QUYUAN2「曲院2号」** | 0x0300 | QUYUAN2 / S90 / G3D80 / X500 / S4000(4/5/6/7/8CORE) / G3S90 | 0x0300 / **0x0323** | `quyuan2_drvdata` |

另有 `DEVICE_ID_HAPS_SUDI104`（XIX 厂的仿真平台）、`DEVICE_ID_QUYUAN1_VF`（SR-IOV 虚函数）。

数值定义在 `inc/mtgpu/mtgpu_defs.h`：

```c
#define PCI_VENDOR_ID_MT         (0x1ED5)
#define DEVICE_ID_SUDI104        (0x0100)
#define DEVICE_ID_MTT_S30_4_Core (0x0103)
#define DEVICE_ID_MTT_S50        (0x0105)
#define DEVICE_ID_QUYUAN1        (0x0200)
#define DEVICE_ID_MTT_S80        (0x0201)
#define DEVICE_ID_MTT_S70        (0x0202)
#define DEVICE_ID_MTT_X300       (0x0211)
#define DEVICE_ID_QUYUAN2        (0x0300)
#define DEVICE_ID_MTT_S4000_8CORE (0x0323)
```

**要点一：S80 与 S50 不是同一颗芯片**（QUYUAN1 vs SUDI104）。
**要点二：这张表在开放源码里，跨架构逐字节相同 —— 谁编这个模块，编出来的都能匹配 S80。**

### 5.2 一枚 blob 通吃全部芯片族（整包哈希实证）

下载 S80 的 `musa_3.0.0-pc.amd64.deb` 与 X300 的 `musa_3.0.0-pc_x86.deb`，**整包 SHA256 完全相同**：

```
0a758b751f9edf91bdd7d689c96c3aefc6371defc680b80b2fcd4d29296cdfac  ← S80  v3.0.0 的包
0a758b751f9edf91bdd7d689c96c3aefc6371defc680b80b2fcd4d29296cdfac  ← X300 v3.0.0_x86 的包
```

（两包都 97,903,324 B，仅 TOS 对象键不同：`g5ivtdq5air.deb` / `evp95yv6wgc.deb`）

即：**同一个文件挂了两个目录项。** 而这张包里 `mtgpu_pci_tbl` 同时列着 SUDI104、QUYUAN1、QUYUAN2 三代芯片的全部产品。

**要点三：摩尔线程的驱动是「每架构一份、覆盖全芯片族」，不是「每产品一份」。**

### 5.3 模型总结

```
        Open（随包发布，跨架构逐字节相同）
        ├── src/mtgpu/*        显示 DRM/KMS、DP、HDMI、DSC、GEM
        ├── src/mtvpu/*        VPU（视频编解码）
        ├── src/mtsnd/*        音频（HDMI 声卡）
        ├── src/pvr/osfunc_*.c 每架构一个 CPU 适配层（含 loongarch）
        ├── src/common/*       PCI / 中断 / OS 抽象
        └── mtgpu_pci_tbl[]    ★ 全芯片族统一设备表（含 S80 的 0x0201）
                 ↓ 链接
        Closed（每架构一枚，全芯片族通用）
        └── objs/<ARCH>/mtgpu_core.o_binary   ← PowerVR 内核服务层
                 ↓
        Closed（每架构一套）
        └── usr/lib/<triple>/*.so              ← Mesa 分支 + Vulkan + 计算栈
```

---

## 六、LoongArch 现状：官方口径与实物

### 6.1 龙芯官方适配清单：是 S10/S30/S50/S60，**不是 S80**

IT之家 2023-06-25 报道（`raw/ithome_701810.html`）原文：

> 适配产品面向数字档案管理、金融证券、运维监控、医疗健康等多个领域，**包括摩尔线程 MTT S10 / S30 / S50 / S60 国产显卡**。

三条互相独立的证据完全吻合：

| 来源 | 内容 |
|---|---|
| 龙芯中科官方适配清单（2023-05） | MTT **S10 / S30 / S50 / S60** |
| 摩尔线程开发者站 MTML `V2.0.0_Linux` 的 `equipment` | `["S10","S30","S50"]` |
| 统信官方 FAQ 的显卡型号 | 摩尔线程 **S10、S30、S50** |

→ **摩尔线程的 LoongArch 支持是一条清晰、持续两年多稳定的产品线划分：信创办公段（S10/S30/S50/S60）有龙芯驱动；消费游戏卡（S70/S80）没有。** 这不是"漏了"，是定位不同——前者常配龙芯整机出货，后者主攻 x86 消费市场。

> ⚠️ **更正**：早期调研（`../dig-gpu/report.md`）记作「2023-06 龙芯 5 月适配清单**含 MTT S80**」。经查原文，**这是错的**，清单里没有 S80。

### 6.2 摩尔线程官方文档的白纸黑字

**`docs.mthreads.com/s30/s30-doc-online/introduction`**：

> MTT S30 兼容 **X86、ARM、LoongArch** 等多种 CPU 架构，支持 Windows、国产 Linux 操作系统及常见 Linux 发行版\*
> …支持 **X86、ARM、LoongArch** 支持 **统信、麒麟、中科方德、Ubuntu、Windows**
> \*具体适配完成时间因 CPU 架构和操作系统版本不同存在差异，详细信息请联系您的客户代表咨询

**`docs.mthreads.com/s30/s30-doc-online/install_guide`**：

> 2. **兆芯/海光/龙芯平台**：确认主板 System BIOS 需要开启 **Above 4G 和 Resizable BAR** 功能
> 3. 操作系统准备 …… 摩尔线程官网提供了统信桌面操作系统 V20 1050 update3 和银河麒麟桌面操作系统 V10 SP1 2303 的镜像下载链接，**该操作系统镜像已经集成摩尔线程显卡驱动**
> 4. 显卡驱动安装 …… 本例中驱动包为 **`musa_2.5.0-Kylin_amd64.deb`** …… `dpkg -s musa` 查询版本
> **显卡驱动版本请咨询销售人员或者技术支持人员**

**`docs.mthreads.com/s30/s30-doc-online/faq`**：有专门一节
> 「**兆芯/海光/龙芯平台如何确认 Resizable BAR 和 Above 4G 是否打开？**」（给出 `lspci | grep VGA` + `lspci -vvvs <Bus-Id>` 的查法）

**「S50 是苏堤、S80 是曲院」在这里得到了另一条印证**：MT 官方给的示例包 `musa_2.5.0-Kylin_amd64.deb` 与 S80 的 `musa_2.5.0-Ubuntu_amd64.deb` **同包名 `musa`、同版本号 2.5.0，只是发行版标签不同**。

**对照：S80 的官方文档是空壳** —— `docs.mthreads.com/s80/s80-doc-online/install_guide/` 返回 200 但正文为空，且导航是「产品介绍/发布版本信息/安装指导/入门指南/API参考手册/帮助(FAQ)/产品白皮书」这一套 **MUSA SDK（计算）** 结构。S80 的 Linux 显示驱动在官方文档里基本等于没有。

### 6.3 loongarch64 与 sw64 的**实物**：MTML

开发者站 `V2.0.0_Linux`（`resourceId 1924409065837039616`，设备 `["S10","S30","S50"]`）的 `instructions` 字段原文：

```
支持MTML的Linux系统，适用于
  Hygon CPU + amd64 Arch + kylin v10 sp1
  兆芯 CPU + amd64 Arch + UOS desktop 20 pro
  phytium CPU + aarch64 + kylin v10 sp1
  loongson CPU + loongarch64 + kylin v10 sp1
  loongson CPU + loongarch64 + UOS desktop 20 pro
  intel CPU + amd64 + ubuntu20.04.1
```

下载该包（`dl/mtml_2.0.0_linux.zip`，10,189,325 B）后，内含 **14 个文件**：

```
Linux/mtml_2.0.0-linux-R_{aarch64, amd64, arm32, i386, loongarch64, sw64}.{deb, rpm}
```

**实测 `mtml_2.0.0-linux-R_loongarch64.deb`**：

```
Architecture: loongarch64
Package: mtml
./usr/lib/libmtml.so     e_machine = 0x102   ← LoongArch 真身
./usr/include/mtml.h     (178,955 B)
```

**这是摩尔线程公开发行 loongarch64（连 sw64 / 申威都有）产物的直接证据。**

### 6.4 一条反向硬证据：管理库有龙芯版 ⇒ 驱动必然也有龙芯版

loongarch64 版 `libmtml.so` 的字符串表里含：

```
mtgpu        mtgpu-        mtgpu.        mtgpu.x
mtgpu_driver_mode     mtgpu_vde     mtgpu_vgpu     drm
```

而其 `DT_NEEDED` 只有 `libc.so.6 / libgcc_s.so.1 / libm.so.6 / libstdc++.so.6`（无 `libdrm`）。

**一个管理库是对着真实内核模块做 ioctl / procfs / sysfs 的** —— 管理库既然有 loongarch64 版，S30/S50 的龙芯驱动就必然存在。（`mtgpu_vgpu` 还对应驱动源码里的 `inc/mtgpu/vgpu/mtgpu_sriov.h`。）

### 6.5 公开仓库扫描（前序工作，结论未变）

| 仓库 | 范围 | 结果 |
|---|---|---|
| 龙芯 Loongnix 25 主仓 `Contents-loong64.gz` | 7,261,821 行 | `musa`/`mthreads`/`moorethreads` **零命中** |
| 麒麟 V10SP1.1 loongarch64 updates | 13,410 个包 | 零命中 |
| UOS `packages.chinauos.com/uos/` | 只有 2020–2021 的 `eagle`（早于摩尔线程） | `pool/main/m/` 无 `musa`/`mtgpu` |

即：**公开可爬的官方仓库里没有，驱动走镜像/整机/厂商渠道。**

---

## 七、龙芯驱动的官方获取入口（已定位）

**摩尔线程自己的官网就挂着龙芯镜像的下载入口，不需要任何灰色渠道。**

### 入口一：MT 官网 MTT S30/S10 页

页面：`https://www.mthreads.com/product/S10`（页面标题即「MTT S30 / S10 **驱动下载**」）

该页内嵌数据（`raw/s10_page.html`，Nuxt chunk `raw/nu_22c32e4.js`）原文：

```
统信桌面操作系统 V20 含有摩尔线程驱动的 1050 Update3 镜像下载，此镜像支持 MTT S10 / S30 / S50。
images:[[
  {label:"Arm 平台镜像下载",   link:"https://iso.uniontech.com/#/productdetails/HLkGEYxjG7ZsJuQg7teq6xC", code:"9QA9"},
  {label:"x86 平台镜像",      link:"https://iso.uniontech.com/#/productdetails/b2epJG5tqF7ztoa05Q8yklk", code:"teU2"},
  {label:"LoongArch 平台镜像", link:"https://iso.uniontech.com/#/productdetails/k1iWnWvM0JkxWC3sHnnH3bC", code:"ZR5o"}
]]
```

**镜像内已集成摩尔线程驱动**（`musa` / `mtgpu` / `mtsnd` / `musa-wine`），可从中取出 loongarch64 的驱动包。

> 注：`iso.uniontech.com` 是 Angular 应用，产品详情接口形如
> `<host>/product/v1/...`（bundle 内可见 `/product/v1`、`/downloadrecords`、`/statistics/downloadList`），
> 需在页面输入提取码后取件。

### 入口二：统信官方 FAQ

`https://faq.uniontech.com/desktop/sysmain/graphics/bf66`（2023-08-22）：

> 应用场景
> OS版本信息：**UOS桌面专业版全架构各版本**
> 硬件/整机信息：搭载摩尔线程显卡终端 ｜ 显卡型号：摩尔线程 **S10、S30、S50**
> 驱动信息：【驱动版本】**1.0.25**
> 驱动涉及相关包名：**musa，mtgpu，mtsnd，musa-wine**
> 【在线安装】：`sudo apt install musa`
> 【离线安装】：下载 mtgpu，mtsnd，musa，musa-wine 四个包后离线安装
> 镜像信息：目前统信官网在合作厂商评测镜像专区已提供了基于 1050u3 版本的相关镜像下载
> 策略说明：官网主线镜像并未默认集成摩尔线程显卡驱动……**摩尔线程显卡驱动仅会上架仓库**，不会集成到主线镜像当中。

**「全架构各版本」包含 loongarch64，而 `mtgpu` 正是那个 DKMS 内核模块包。**

### 入口三：官方文档的明确指引

MT 官方 S30 安装指导原话：「**显卡驱动版本请咨询销售人员或者技术支持人员**」。

---

## 八、「网上有人说驱动成功过」怎么判

### 8.1 能查到的说法

| 来源 | 时间 | 内容 | 可信度 |
|---|---|---|---|
| B站 `BV1se411Z7n1`（UP「蝰蛇设计-万兴专家」，18,849 播放） | 2023-11-29 | 标题「好消息：龙芯3A6000兼容摩尔线程S80！**坏消息，没开放驱动**！」简介「**大佬个人制作的驱动没开放**！可能要再等等，到24年第1季度，深度Deepin Linux龙芯版的时候」 | 高（与包结构自洽） |
| B站 `BV1yC4y1U75x`（UP「音未」） | 2023-11-13 | 「龙芯3A6000+摩尔线程s80测试预告」 | 中 |
| B站专栏 `cv28076724` | — | 「龙芯3A6000 + 摩尔线程S80」 | 未知（正文未取到，SPA） |
| B站专栏 `cv29709061` | — | 「龙芯3A6000已经可以流畅运行原神，摩尔线程S80等驱动，整机设计图已完成」 | **极弱**（174 阅读、0 评论、0 点赞） |

### 8.2 用包结构去校验这些说法

S80 的龙芯驱动**不可能从公开渠道自行产生** —— `objs/loongarch64/mtgpu_core.o_binary` 是闭源的，且公开包里根本没有这个目录（见 [§4.1](#41-makefile-已有-loongarch-分支)）。

因此若「有人做出来了」为真，那个人只可能是**拿到厂商内部构建的人**（或厂商员工）。这与「大佬个人制作」+「没开放」的说法自洽：能编的人手里有 blob，但不能公开（Imagination 的 IP + 不能开源 DKMS 树）。

**而这个推断反过来强化了「厂商手里有 S80 的 LoongArch 构建」** —— 是要包的加分项。

### 8.3 给未来任何此类声明的分级判据

让对方贴三条命令即可，一分钟辨真假：

| 级别 | 判据 | 说明 |
|---|---|---|
| **0 级「点亮」** | `lspci` 能看到 Moore Threads 设备 | **不需要任何驱动**。只要卡通电、PCIe 枚举成功。这是绝大多数「兼容了」的真实含义 |
| **1 级「驱动起来」** | `lspci -nnk` 出现 `Kernel driver in use: mtgpu` | 才证明 `mtgpu.ko` 真的加载绑定 ⇒ 龙芯上必然存在 loongarch64 blob |
| **2 级「可用」** | `ls /dev/dri` 有节点、`mthreads-gmi` 能出信息 | 驱动初始化完成 |
| **3 级「能跑图形/计算」** | `glxinfo -B` 显示 MUSA/MTT、Vulkan / 计算栈可用 | 用户态那 60 个 `.so` 也在 |

**一句话**：如果对方贴不出 `lspci -nnk` 里的 `Kernel driver in use: mtgpu`，那就连驱动都没加载，不叫驱动成功。

---

## 九、能不能用 S30/S50 的驱动带 S80

### 9.1 三步推理

**第一步：S50 和 S80 不是同一颗芯片。**

S50 → `sudi_drvdata`（SUDI104「苏堤」，PCI ID `0x0105`）
S80 → `quyuan1_drvdata`（QUYUAN1「曲院1号」，PCI ID `0x0201`）

如果 blob 是按芯片族编的，那么「拿 S50 的 blob 直接顶 S80」就不成立。

**第二步：但 blob 恰恰不是按芯片族编的。**

- 整包 SHA256 证明：S80 的 x86 包与 X300 的 x86 包是**同一个文件**（见 [§5.2](#52-一枚-blob-通吃全部芯片族整包哈希实证)）
- 而该包的 `mtgpu_pci_tbl` 同时列着 SUDI104、QUYUAN1、QUYUAN2 三代芯片的全部产品
- 固件目录里也躺着 6 代 GPU 固件

→ **一枚 blob 通吃所有芯片族。**

**第三步：设备匹配写在开放源码里，不在 blob 里。**

`mtgpu_pci_tbl[]` 属于 `src/mtgpu/mtgpu_drv.c`，而该文件在 amd64 包和 arm64 包里**逐字节相同**。

### 9.2 结论

> **拿到 S30/S50 的 loongarch64 驱动包，它的开放部分自带 S80 的 PCI 表项（`0x0201`），blob 又是全芯片族通用的 —— 所以很可能不需要「改」，装上就能绑。**

### 9.3 剩余的不确定点（只能实测）

| # | 不确定点 | 如何消除 |
|---|---|---|
| 1 | UOS 镜像里那份驱动的**实际版本**决定其 PCI 表里有没有 QUYUAN1 | 解包后看 `inc/mtgpu/mtgpu_defs.h` 有无 `DEVICE_ID_MTT_S80`，或直接试装 |
| 2 | blob 有没有按产品**裁剪** | 从架构证据看不太可能（x86 那份是全芯片族通用的），但只有试了才知道 |
| 3 | 用户态 `.so` 是否覆盖 QUYUAN1 | `glxinfo -B` / Vulkan 实测 |

**因此第一步永远是 `lspci -nnk`，不是改包。**

---

## 十、三条路线的裁决

### 路线 A：自研编译内核模块 —— **走不通（死锁在 blob）**

即使 hack 掉 `dkms.conf` 的 `ARCH=x86_64`、改掉 `postinst` 只认 `x86_64/i686` 的白名单，`Makefile` 仍会去找 `objs/loongarch64/mtgpu_core.o_binary` —— 不存在，且无法生成。

### 路线 B：从零写一个 DRM/KMS 驱动 —— **理论可行，工程不可行**

包里确实公开了 ABI：

- `inc/shared_include/linux/uapi/drm/mtgpu_drm.h`（72,723 B，`@License Dual MIT/GPLv2`）、`mtgpu_aligncheck.h`
- `inc/shared_include/fwif/mtfw_fwif*.h`（固件接口结构体，`Copyright (C) 2024 Moore Threads`，All Rights Reserved 但可读）

**但**：你要实现的是整个 PowerVR 内核服务层 + 固件加载 + 命令提交 + MMU + 同步原语 + 显示控制器，对标 Imagination 的 `pvrsrvkm`，固件 ABI 行为无文档，工作量以**人年**计。

**更致命的是**：即使内核写出来，用户态那 60 个 `.so` 是 x86_64 ELF，你依然没有 GL/Vulkan/计算栈 —— 而这部分的源码（Mesa 分支、`libVK_MT`、MUSART）一概没有。

### 路线 C：拿到现成的 loongarch64 驱动包 —— **唯一现实路径**

见 [§11](#十一分步操作清单)。

---

## 十一、分步操作清单

### 路线 C-1：有龙芯机器且能装 UOS（最省事）

```bash
# 1. 装 UOS 桌面专业版（龙芯版），或从"合作厂商评测镜像专区"取 1050u3 镜像
# 2. 在线装驱动
sudo apt install musa

# 若网络受限，改离线：从仓库/镜像取出下列四个包后
sudo dpkg -i mtgpu_*.deb mtsnd_*.deb musa_*.deb musa-wine_*.deb

# 3. 查驱动版本
dpkg -s musa
```

**BIOS 前置条件**（MT 官方要求）：龙芯平台须开启 **Above 4G** 与 **Resizable BAR**。

### 路线 C-2：下载官方 LoongArch 镜像取包

1. 打开 `https://iso.uniontech.com/#/productdetails/k1iWnWvM0JkxWC3sHnnH3bC`，提取码 **`ZR5o`**
2. 取得 统信桌面操作系统 V20 1050 Update3 **LoongArch 平台**镜像（该镜像已集成 MTT 驱动）
3. 从镜像中取出驱动包（镜像内路径通常在 `pool/main/{m/musa,m/mtgpu,m/mtsnd}/`）
4. 搬到目标龙芯机器安装

> 同类镜像还有 Arm 平台（提取码 `9QA9`）与 x86 平台（提取码 `teU2`），可用于对照取包。

### 路线 C-3：找厂商要

MT 官方文档明确写了渠道：**「显卡驱动版本请咨询销售人员或者技术支持人员」**。

建议的诉求文本（依据充分，可直接发出）：

> 我方在龙芯 3A6000/3C6000（LoongArch，麒麟 V10 SP1 / UOS）上部署 MTT S80。
> 已知贵司 `musa_3.0.0-pc.amd64.deb` 内核模块源码 `/usr/src/mtgpu-3.0.0/` 中**已含 `CONFIG_LOONGARCH` 分支**与 `src/pvr/osfunc_loongarch.c`、`src/mtgpu/dmi_loongarch.c`（均 Dual MIT/GPLv2），
> 且贵司已公开发布 `mtml_2.0.0-linux-R_loongarch64.deb`（含 sw64），X300 亦有公开 `musa_3.0.0-pc.arm64.deb`，
> 官网并提供**含驱动的 UOS V20 1050u3 LoongArch 平台镜像**。
> 请提供 **MTT S80 的 loongarch64 驱动包**（`musa_<ver>-<distro>_loongarch64.deb`，含 `objs/loongarch64/mtgpu_core.o_binary` 与 loongarch64 用户态库），或告知获取渠道与 roadmap。
> 若 S80 的 Linux 驱动线已停止维护，请告知替代型号建议。

### 验证（三条命令，一分钟）

```bash
# ① 卡是否被枚举（0 级：不需要驱动）
lspci | grep -i -E "1ed5|moore"

# ② 驱动是否真的绑上（1 级：这一条才是关键）
lspci -nnk | grep -A3 -i "1ed5"
#   → 期望看到  Kernel driver in use: mtgpu

# ③ 是否有 DRI 节点与初始化信息
ls /dev/dri/
dmesg | grep -i mtgpu
mthreads-gmi
```

| 结果 | 含义 | 下一步 |
|---|---|---|
| ② 出现 `Kernel driver in use: mtgpu` | blob 认 QUYUAN1，**成了** | 进 ③ 验用户态，再 `glxinfo -B` |
| ② 没有绑定 | — | `sudo modprobe mtgpu` 看 dmesg 报什么 |
| dmesg 报「设备不支持」 | blob 里缺 QUYUAN1 | 只能回头找厂商 |
| ② 通过但 ③ 无 DRI 节点 | 驱动加载但初始化失败 | 查 BIOS 的 Above 4G / Resizable BAR |

---

## 十二、顺带发现

1. **S80 的 Linux 驱动线明显慢于 Windows。** Windows 侧已到 `v350.160`（2026-09-21，月更），Linux 侧停在 `v3.0.0`（2025-04-29）—— 距调研日已 **18 个月**无新版；同期 X300 的 Linux 驱动走到了 v3.1.0（2025-06）。**S80 的 Linux 支持存在事实上的停滞风险**，这会影响向厂商要新架构包的成功率判断。

2. **驱动栈里带音频。** `src/mtsnd/`（`mtsnd_pcm.c`、`mtsnd_codec.c`）+ initramfs hook 里 `manual_add_modules snd-pcm` —— HDMI 音频走同一模块。

3. **装包会顶掉发行版的 `linux-firmware`**（`Replaces: ... linux-firmware`），在定制固件里要注意。

4. **`Conflicts: musa_all-in-one`** —— 说明存在过一个"全家桶"包形态；现在的 `musa_3.0.0-pc` 是合并包，而 UOS 仓库里仍是四包拆分（`musa`/`mtgpu`/`mtsnd`/`musa-wine`）。

5. **驱动源码里有 SR-IOV / vGPU 支持**（`inc/mtgpu/vgpu/mtgpu_sriov.h`、`mtgpu_mdev.h`、`DEVICE_ID_QUYUAN1_VF`），以及 `CONFIG_VZ_MOORE_THREADS` 编译开关。

6. **MUSA SDK 是按 host CPU 出包的**：开发者站可见 `v4.0.1_Hygon_CPU_Kylin`、`v4.0.1_Intel_CPU_Ubuntu`、`v1.5.2_Kunpeng920_CPU_Kylin V10` 等条目。

7. **`mtgpu-next` 一代新驱动的 UAPI 头已在包里**（`inc/mtgpu-next/`，含 `mtgpu_drm.h`、`mtgpu_sched.h`、`mtgpu_fw.h` 等），但 `src/mtgpu-next/` 没有实现 —— 与旧的 `pvr` 栈并存。

---

## 十三、证据文件索引

```
dig-s80-driver/
├─ report.md                                  本文
├─ scripts/
│  ├─ fetch_driver.py                         ★ pes 签名算法 + 直链获取（可复用）
│  └─ read_deb.py                             ★ 纯 Python 解 .deb（可复用，不依赖 dpkg/ar/7z）
├─ dl/                                        （下载的厂商发行物）
│  ├─ musa_3.0.0-pc.amd64.deb     97,903,324 B  S80 v3.0.0 Linux 驱动
│  ├─ x300_v300_x86.deb           97,903,324 B  X300 v3.0.0_x86（与上式 SHA256 相同）
│  ├─ musa_3.0.0-pc.arm64.deb     89,303,112 B  X300 v3.0.0 arm64
│  ├─ mtml_2.0.0_linux.zip        10,189,325 B  开发者站 V2.0.0_Linux（含 loongarch64 / sw64）
│  ├─ mtml_la.deb                    733,488 B  MTML loongarch64（e_machine=0x102 实物）
│  └─ mtml_v200.zip                      251 B  （失败响应，可删）
├─ src_all/usr/src/mtgpu-3.0.0/               S80 驱动内核模块完整源码树（12 MB）
├─ extract/usr/src/mtgpu-3.0.0/               关键文件（含 objs/x86_64/mtgpu_core.o_binary）
├─ mtml/libmtml.so                            loongarch64 管理库（字符串证据）
└─ raw/                                       （原始抓取）
   ├─ data_listing.txt          amd64 包 data.tar.xz 全量文件清单（1059 行）
   ├─ search.html               pes 产品 × 系统矩阵（__NEXT_DATA__）
   ├─ s80_win.html / s80_linux.html / s80_ubuntu.html   驱动版本列表
   ├─ s80_v300_url.txt          S80 v3.0.0 的 TOS 直链
   ├─ x300_arm64_v300.json      X300 arm64 直链响应
   ├─ driver-info-*.js / nu_*.js / iso_main.js   签名算法与镜像链接所在的前端 bundle
   ├─ ithome_701810.html        龙芯 2023-05 适配清单（S10/S30/S50/S60）
   ├─ s30_install.html          MT 官方 S30 安装指导（龙芯 BIOS 要求、musa 包名示例）
   ├─ s30_intro.html            MT 官方 S30 产品介绍（LoongArch 声明）
   ├─ s80_doc.html              MT 官方 S80 安装指导（空壳）
   ├─ s10_page.html             ★ MT 官网 S30/S10 页（LoongArch 镜像入口）
   ├─ uniontech_bf66.html       ★ 统信官方 FAQ（全架构、apt install musa、四个包名）
   ├─ iso_ut.html / iso_main.js  iso.uniontech.com 应用与接口线索
   └─ cv29709061.html           B站专栏（SPA 壳，正文未取到）
```

**上游依据（前序调研报告）**：

- `../dig-s80/report.md` —— 公开渠道无 S80 LoongArch 驱动（官网/龙芯仓/麒麟仓/GitHub 全扫）
- `../dig-s80-docker/report.md` —— Docker 渠道与全网网盘线索为零
- `../dig-gpu/report.md` —— 龙芯上跑 LLM 的整体路线对比（**其中「适配清单含 S80」一条有误，见 [§6.1](#61-龙芯官方适配清单是-s10s30s50s60不是-s80)**）
- `../dig-ascend/report.md` §5 —— MUSA SDK 66 条 `systemInfo` 全 x86_64

---

## 十四、修订记录

| 日期 | 修订 |
|---|---|
| 2026-10-11 | 初版：S80 驱动的分层解剖、跨架构缺口、官方架构矩阵、三条路线裁决 |
| 2026-10-11 | 补 §5.1 更正（龙芯适配清单实为 S10/S30/S50/S60）、§5.2 说法分级判据 |
| 2026-10-11 | 补 §5.3 官方获取入口；新增 §5（芯片族与统一驱动模型）、§9（能否用 S30/S50 的驱动带 S80） |
| 2026-10-11 | 整合为完整报告；新增 §11 分步操作清单、§12 顺带发现 |
