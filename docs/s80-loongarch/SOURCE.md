# 来源说明

- 报告出自另一会话 2026-10-11 的实物调研（官方包下载解剖+逐字节比对），由本会话复验关键项后入库。
- 已复验：libmtml.so e_machine=0x102（LoongArch）；osfunc_loongarch.c/dmi_loongarch.c 存在且 Dual MIT/GPLv2；S80 amd64 与 X300 x86 两包 SHA256 相同（0a758b…cdfac）。
- 原始证据（dl/、extract/、raw/、scripts/fetch_driver.py）在本机 `outputs/dig-s80-driver/`，未进库（体积大）。
- 结论摘要见 report.md 第一节；行动清单见第十一节。
