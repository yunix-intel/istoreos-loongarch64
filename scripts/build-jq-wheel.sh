#!/bin/bash
# Build a loongarch64 wheel for jq==1.13.0 inside openEuler 24.03.
# Usage: ./scripts/build-jq-wheel.sh [output-dir]
# The wheel is needed because jq's bundled oniguruma has an old config.sub
# that does not know loongarch64.
set -euo pipefail

OUT="${1:-$(pwd)/wheels}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

docker run --rm -i \
  -v "$OUT":/out \
  openeuler/openeuler:24.03 bash -s <<'INNER'
set -eux
dnf install -y --setopt=install_weak_deps=False \
  gcc make python3-devel python3-pip diffutils bison flex automake >/dev/null
python3 -m pip install -q -U pip setuptools wheel Cython

URL=$(python3 -c "import json,urllib.request; d=json.load(urllib.request.urlopen('https://pypi.org/pypi/jq/1.13.0/json')); print([u['url'] for u in d['urls'] if u['packagetype']=='sdist'][0])")
curl -fsSL "$URL" | tar xz -C /tmp
cd /tmp/jq-1.13.0

python3 - <<'PYPATCH'
p = 'setup.py'
s = open(p).read()
old = '["./configure", "CFLAGS=-fPIC -pthread"'
new = '["./configure", "--build=loongarch64-unknown-linux-gnu", "CFLAGS=-fPIC -pthread"'
assert old in s
open(p, 'w').write(s.replace(old, new, 1))
PYPATCH

CG=$(ls /usr/share/automake-*/config.guess | head -1)
CS=$(ls /usr/share/automake-*/config.sub | head -1)
cp "$CG" "$CS" /tmp/jq-1.13.0/
rm -rf /tmp/jq-1.8.2
tar xzf /tmp/jq-1.13.0/deps/jq-1.8.2.tar.gz -C /tmp
cp "$CG" "$CS" /tmp/jq-1.8.2/
cp "$CG" "$CS" /tmp/jq-1.8.2/vendor/oniguruma/
tar czf /tmp/jq-1.13.0/deps/jq-1.8.2.tar.gz -C /tmp jq-1.8.2

python3 -m pip wheel --no-deps --no-build-isolation -w /out .
ls -lh /out
INNER
