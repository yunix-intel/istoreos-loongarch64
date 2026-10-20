# 构建文档

## 环境

- 主机：Windows 11 + WSL2 Ubuntu（x86_64，32 核 / 60GB / 951G 可用）
- 目标：loongarch64/generic，内核 6.6
- 源码：istoreos/istoreos（commit 见 build-src-version.txt）

## 步骤

见 `scripts/build-wsl.sh`，三段：依赖 → feeds → config → `make -j32`。

## 构建日志

`docs/BUILDLOG.md` 按日期记：每次报错原文 + 原因 + 修法 + patch 文件名。
修完的 patch 放 `patches/`，命名 `NNN-简述.patch`，同步向 istoreos 上游提 PR。

## 发版

- `bin/targets/loongarch64/generic/*combined-efi.img.gz` → GitHub Releases（KVM/物理机刷机用）
- `bin/packages/loongarch64_generic/` → 同一 Release（opkg 源用）
- 发版说明写：源码 commit、config 摘要、验证过的功能清单
