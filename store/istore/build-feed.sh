#!/bin/sh
# Reproducible dual-feed builder for the LoongArch64 iStore packages.
#
# Outputs:
#   feed/public/all/meta/*.ipk + Packages*
#   feed/public/all/nas_luci/luci-app-istore-loong64_*.ipk + Packages*
#   feed/public/isfeeds.conf
#   feed/private/... (same layout, private defaults / private store URLs)
#   feed/README.txt
#
# Requirements: python3 (or python), standard library only. No network.
# Signing: set USIGN_KEY=/path/to/key and install usign. Otherwise
# Packages.sig is intentionally empty (development feed).

set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
	PY=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
	PY=python
else
	echo "ERROR: python3/python not found" >&2
	exit 1
fi

if [ "${NO_GEN:-0}" != "1" ]; then
	"$PY" -I "$HERE/gen_istore.py"
fi

VER=$(sed -n 's/^Version: //p' "$HERE/src/generic/control" | head -n 1)
[ -n "$VER" ] || { echo "ERROR: no Version in src/generic/control" >&2; exit 1; }

PUBLIC_URL="${PUBLIC_STORE_URL:-https://github.com/yunix-intel/istoreos-loongarch64}"
PRIVATE_URL="${PRIVATE_STORE_URL:-https://github.com/yunix-intel/istore-la-private}"
FEED_BASE_URL="${FEED_BASE_URL:-http://<your-feed-host>/istore-loong64}"

OUT="$HERE/feed"
BUILD="$HERE/.build"
rm -rf "$OUT" "$BUILD"
mkdir -p "$BUILD"

echo "building luci-app-istore-loong64 $VER"
"$PY" -I "$HERE/tools/mkipk.py" "$HERE/src/generic" \
	"$BUILD/luci-app-istore-loong64_${VER}_all.ipk" >/dev/null

build_one() {
	feed=$1
	root="$OUT/$feed"
	meta="$root/all/meta"
	luci="$root/all/nas_luci"
	mkdir -p "$meta" "$luci"
	cp "$BUILD/luci-app-istore-loong64_${VER}_all.ipk" "$luci/"
	app_ver="$VER"
	[ "$feed" = "private" ] && app_ver="${VER}-p1"

	count=0
	for d in "$HERE"/src/app-meta/*; do
		[ -d "$d" ] || continue
		id=$(basename "$d")
		stage="$BUILD/$feed/$id"
		"$PY" -I "$HERE/tools/mkvariant.py" "$d" "$stage" "$feed" \
			"$PUBLIC_URL" "$PRIVATE_URL" >/dev/null
		"$PY" -I "$HERE/tools/mkipk.py" "$stage" \
			"$meta/app-meta-${id}_${app_ver}_all.ipk" >/dev/null
		count=$((count + 1))
	done

	"$PY" -I "$HERE/tools/mkindex.py" "$meta"
	"$PY" -I "$HERE/tools/mkindex.py" "$luci"

	cat >"$root/isfeeds.conf" <<EOF
# $feed feed; deploy this directory under \$FEED_BASE_URL/$feed/
src/gz istore-loong64-meta $FEED_BASE_URL/$feed/all/meta
src/gz istore-loong64-luci $FEED_BASE_URL/$feed/all/nas_luci
EOF

	if [ "$feed" = "public" ]; then
		cat >"$root/README.txt" <<'EOF'
Public feed. Only the public image variant is present in each app-meta JSON.
Images are referenced as yunixintel/<app>:24.10-la5.
Deploy this directory under your HTTP base URL and point isfeeds.conf at it.
EOF
	else
		cat >"$root/README.txt" <<'EOF'
Private feed. Apps with a private single-image build default to local/* and
must have those images preloaded; this script never pushes them. Apps without
a private image keep the public image but every store URL points at the
private store. Deploy this directory under your private HTTP base URL.
EOF
	fi
	echo "built $count $feed app-meta packages"
}

build_one public
build_one private

cat >"$OUT/README.txt" <<'EOF'
Two independent feeds are generated from the same app-meta schema:

  public/   only public variants, public store URL, public images
  private/  private defaults for local/* single-image apps; private store URL
            for every app; no local/* image is pushed or copied

Each feed has all/meta/, all/nas_luci/, Packages, Packages.gz, Packages.sig
and isfeeds.conf. Packages.sig is empty unless USIGN_KEY was set.

isfeeds.conf uses FEED_BASE_URL (default http://<your-feed-host>/istore-loong64).
Copy feed/public/ or feed/private/ under that URL before running opkg update.
EOF

if [ "${SKIP_VALIDATE:-0}" != "1" ] && [ -f "$HERE/validate.py" ]; then
	"$PY" -I "$HERE/validate.py"
fi

rm -rf "$BUILD"
echo "feeds: $OUT/public and $OUT/private"
