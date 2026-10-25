#!/usr/bin/env bash
# Validate every CasaOS definition with the target CasaOS AppManagement API
# in dry-run mode. Requires SSH access to the CasaOS host via $HOST.
set -uo pipefail

HOST="${HOST:-loongson-lab}"
HERE="$(cd "$(dirname "$0")" && pwd)"
APPS="$HERE/Apps"
REMOTE_DIR="${REMOTE_DIR:-/tmp/casaos-defs}"
BASE="${BASE:-http://127.0.0.1:8081/v2/app_management}"

if [[ ! -d "$APPS" ]]; then
  echo "missing $APPS" >&2
  exit 2
fi

tar -C "$APPS" -cf - . | ssh "$HOST" "rm -rf '$REMOTE_DIR' && mkdir -p '$REMOTE_DIR' && tar -C '$REMOTE_DIR' -xf -" || exit 2

ssh "$HOST" "BASE='$BASE' REMOTE_DIR='$REMOTE_DIR' bash -s" <<'REMOTE'
set -u
pass=0
fail=0
declare -a failures=()
for f in "$REMOTE_DIR"/*/docker-compose.yml; do
  id="$(basename "$(dirname "$f")")"
  body="$(mktemp)"
  code="$(curl -sS -o "$body" -w '%{http_code}' -X POST \
    "$BASE/compose?dry_run=true&check_port_conflict=true" \
    -H 'Content-Type: application/yaml' --data-binary "@$f")"
  if [[ "$code" == "200" ]]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    failures+=("$id HTTP $code $(head -c 300 "$body" | tr '\n' ' ')")
  fi
  rm -f "$body"
done
printf 'dry-run pass=%d fail=%d\n' "$pass" "$fail"
for item in "${failures[@]:-}"; do
  [[ -n "$item" ]] && printf 'FAIL %s\n' "$item"
done
[[ "$fail" -eq 0 ]]
REMOTE
