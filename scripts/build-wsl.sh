#!/usr/bin/env bash
# WSL2 Ubuntu (x86_64) 上交叉编译 iStoreOS loongarch64 完整固件
# 用法：./scripts/build-wsl.sh
# 产物：bin/targets/loongarch64/generic/*combined-efi.img + 全套 .ipk
set -euo pipefail

WORK="$HOME/istore-la-build"
NPROC="$(nproc)"
REPO="https://github.com/istoreos/istoreos.git"

echo "=== 0. 依赖 ==="
sudo apt update
sudo apt install -y build-essential libncurses-dev gawk unzip file \
  python3 rsync git wget curl diffutils flex gettext libssl-dev

echo "=== 1. 拉源码 ==="
mkdir -p "$WORK" && cd "$WORK"
[ -d istoreos ] || git clone --depth 1 "$REPO" istoreos
cd istoreos
git log --oneline -1 | tee ../build-src-version.txt

echo "=== 2. feeds ==="
./scripts/feeds update -a
./scripts/feeds install -a

echo "=== 3. 写 config（loongarch64/generic + 商店件） ==="
cp ../../config/loongarch64-generic.config .config
make defconfig

echo "=== 4. 整编（后台跑，几小时） ==="
make -j"$NPROC" 2>&1 | tee ../build-full.log

echo "=== DONE，产物在 bin/targets/loongarch64/generic/ ==="
ls -lh bin/targets/loongarch64/generic/*combined-efi.img.gz
