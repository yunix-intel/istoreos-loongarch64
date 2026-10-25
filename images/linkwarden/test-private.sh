#!/bin/bash
# Private single-image Linkwarden test: PostgreSQL + one app container that
# carries LBrowser.  No sidecar, no /opt/apps/lbrowser bind mount.
set -uo pipefail

PORT=14112
PUB_PORT=14113
APP_IMAGE=local/linkwarden-private:2.16.3-p1
PUB_IMAGE=yunixintel/linkwarden:2.16.3
PG_IMAGE=yunixintel/postgres:loong64
NET=lwp-net
PG=lwp-pg
APP=lwp-app
PUB=lwp-app-pub
VOL_DATA=lwp-data
VOL_PG=lwp-pgdata
BASE="http://127.0.0.1:${PORT}"
PUB_BASE="http://127.0.0.1:${PUB_PORT}"
JAR=/tmp/lwp-cookies.txt
USER=privtester
PASS=private-test-pass
OUT="${OUT:-$(pwd)/test-output}"
mkdir -p "$OUT"

log() { echo; echo "=== $* ==="; }
fail() { echo "FAIL: $*" >&2; exit 1; }

jget() { python3 -I -c "import json,sys;d=json.load(open(sys.argv[1]));print(eval(sys.argv[2]))" "$1" "$2"; }

log "cleanup"
docker rm -f "$APP" "$PUB" "$PG" >/dev/null 2>&1 || true
docker network rm "$NET" >/dev/null 2>&1 || true
docker volume rm "$VOL_DATA" "$VOL_PG" >/dev/null 2>&1 || true
docker network create "$NET" >/dev/null

log "start postgres"
docker run -d --name "$PG" --network "$NET" \
    -e POSTGRES_USER=linkwarden -e POSTGRES_PASSWORD=change-me \
    -e POSTGRES_DB=linkwarden \
    -v "$VOL_PG":/var/lib/postgresql/data \
    "$PG_IMAGE" >/dev/null
for i in $(seq 1 60); do
    docker exec "$PG" pg_isready -U linkwarden >/dev/null 2>&1 && break
    sleep 1
done
docker exec "$PG" pg_isready -U linkwarden >/dev/null 2>&1 || fail "postgres not ready"

log "start private app (--shm-size=1g, no browser sidecar, no host mount)"
SECONDS=0
docker run -d --name "$APP" --network "$NET" \
    -p "127.0.0.1:${PORT}:3000" \
    --shm-size=1g \
    -v "$VOL_DATA":/data/data \
    -e DATABASE_URL=postgresql://linkwarden:change-me@"$PG":5432/linkwarden \
    -e NEXTAUTH_URL="http://127.0.0.1:${PORT}/api/v1/auth" \
    -e NEXTAUTH_SECRET=private-test-secret-000000000000000000 \
    "$APP_IMAGE" >/dev/null || fail "docker run failed"

READY=""
for i in $(seq 1 240); do
    if curl -fsS "$BASE/" >/dev/null 2>&1; then READY=$SECONDS; break; fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$APP" 2>/dev/null)" != "true" ]; then
        docker logs "$APP" 2>&1 | tail -40
        fail "app exited during startup"
    fi
    sleep 1
done
[ -n "$READY" ] || fail "app not ready within 240s"
echo "startup_to_http_200_seconds=$READY"

SECONDS=0
for i in $(seq 1 240); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$APP" 2>/dev/null)" = "healthy" ] && break
    sleep 1
done
echo "http_ready_to_docker_healthy_seconds=$SECONDS"
echo "health=$(docker inspect -f '{{.State.Health.Status}}' "$APP")"

log "migrations"
docker logs "$APP" 2>&1 | grep -E "MIGRATIONS_OK|\[entrypoint\]|No browser" | head -20

log "image identity"
docker image inspect "$APP_IMAGE" --format 'id={{.Id}} size={{.Size}} arch={{.Architecture}}'
docker inspect "$APP" --format 'mounts={{json .Mounts}} shm={{.HostConfig.ShmSize}}'
docker exec "$APP" sh -c 'echo executable=$(test -x /opt/apps/lbrowser/lbrowser && echo yes || echo no); /opt/apps/lbrowser/lbrowser --version 2>/dev/null | head -2'
docker exec "$APP" sh -c 'rpm -q perl dpkg 2>&1 | head -4'

log "register / login / collection / link"
code=$(curl -s -o "$OUT/register.json" -w '%{http_code}' -X POST "$BASE/api/v1/users" \
    -H 'Content-Type: application/json' \
    -d "{\"name\":\"Private Test\",\"email\":\"private@example.com\",\"password\":\"${PASS}\",\"username\":\"${USER}\"}")
echo "register_http=$code body=$(cat "$OUT/register.json")"
[ "$code" = "201" ] || fail "register"

rm -f "$JAR"
curl -s -c "$JAR" "$BASE/api/v1/auth/csrf" -o "$OUT/csrf.json"
CSRF=$(jget "$OUT/csrf.json" "d['csrfToken']")
code=$(curl -s -b "$JAR" -c "$JAR" -o "$OUT/login.json" -w '%{http_code}' \
    -X POST "$BASE/api/v1/auth/callback/credentials" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "csrfToken=${CSRF}" \
    --data-urlencode "username=${USER}" \
    --data-urlencode "password=${PASS}" \
    --data-urlencode "callbackUrl=${BASE}/" \
    --data-urlencode "json=true")
echo "login_http=$code body=$(cat "$OUT/login.json")"
code=$(curl -s -b "$JAR" -o "$OUT/me.json" -w '%{http_code}' "$BASE/api/v1/users/me")
echo "me_http=$code body=$(cat "$OUT/me.json")"
[ "$code" = "200" ] || fail "users/me"

code=$(curl -s -b "$JAR" -o "$OUT/collection.json" -w '%{http_code}' \
    -X POST "$BASE/api/v1/collections" -H 'Content-Type: application/json' \
    -d '{"name":"Private Test"}')
COLL=$(jget "$OUT/collection.json" "d['response']['id']")
echo "collection_http=$code id=$COLL"
case "$code" in 200|201) ;; *) fail "collection" ;; esac
[ -n "$COLL" ] || fail "collection id"

curl -s -b "$JAR" "$BASE/api/v1/config" -o "$OUT/config.json" || true
code=$(curl -s -b "$JAR" -o "$OUT/link.json" -w '%{http_code}' \
    -X POST "$BASE/api/v1/links" -H 'Content-Type: application/json' \
    -d "{\"url\":\"https://example.com\",\"collection\":{\"id\":${COLL}}}")
LINK=$(jget "$OUT/link.json" "d['response']['id']")
echo "link_http=$code id=$LINK"
case "$code" in 200|201) ;; *) fail "link" ;; esac
[ -n "$LINK" ] || fail "link id"

log "wait for preservation (worker, local LBrowser)"
PRESERVED=""
for i in $(seq 1 180); do
    curl -s -b "$JAR" "$BASE/api/v1/links" -o "$OUT/links.json"
    if python3 -I - "$OUT/links.json" "$LINK" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
items=d.get("response", d) if isinstance(d, dict) else d
if isinstance(items, dict): items=items.get("links", [])
for x in items:
    if x.get("id")==int(sys.argv[2]):
        ok=all(x.get(k) not in (None,"unavailable") for k in ("image","pdf","readable","preview"))
        print(json.dumps({k:x.get(k) for k in ("id","url","image","pdf","readable","preview","monolith","lastPreserved")}))
        sys.exit(0 if ok else 1)
sys.exit(2)
PY
    then PRESERVED=yes; break; fi
    sleep 2
done
cat "$OUT/links.json" | python3 -I -m json.tool > "$OUT/links.pretty.json" 2>/dev/null || true
[ "$PRESERVED" = "yes" ] || { docker logs "$APP" 2>&1 | tail -60; fail "preservation incomplete"; }

log "worker browser path"
docker logs "$APP" 2>&1 | grep -E "Launching browser|Connecting to remote browser|Succeeded processing|Browser closed" | tail -10
docker logs -t "$APP" 2>&1 | grep -E "Starting link processing|Launching browser|Succeeded processing" | tail -8
docker logs "$APP" 2>&1 | grep -q "Connecting to remote browser" && fail "unexpected remote browser"
docker logs "$APP" 2>&1 | grep -q "Launching browser" || fail "no local launch log"

log "archives"
docker exec "$APP" sh -c "ls -l /data/data/archives/${COLL} /data/data/archives/preview/${COLL}"
docker exec "$APP" sh -c "stat -c '%n %s' /data/data/archives/${COLL}/${LINK}.jpeg /data/data/archives/${COLL}/${LINK}.pdf /data/data/archives/${COLL}/${LINK}_readability.json /data/data/archives/preview/${COLL}/${LINK}.jpeg"
docker exec "$APP" sh -c "printf 'pdf_magic='; head -c 5 /data/data/archives/${COLL}/${LINK}.pdf; echo; printf 'jpeg_magic='; od -An -tx1 -N3 /data/data/archives/${COLL}/${LINK}.jpeg; printf 'preview_magic='; od -An -tx1 -N3 /data/data/archives/preview/${COLL}/${LINK}.jpeg"
docker exec "$APP" sh -c "head -c 300 /data/data/archives/${COLL}/${LINK}_readability.json; echo"

log "processes"
docker top "$APP" -o pid,user,comm,args | head -20

log "restart persistence (private)"
docker restart "$APP" >/dev/null
SECONDS=0
for i in $(seq 1 240); do
    if curl -fsS "$BASE/" >/dev/null 2>&1; then break; fi
    sleep 1
done
echo "restart_to_http_200_seconds=$SECONDS"
docker logs "$APP" 2>&1 | grep "MIGRATIONS_OK" | tail -1
curl -s -b "$JAR" "$BASE/api/v1/links" -o "$OUT/links-after-restart.json"
python3 -I - "$OUT/links-after-restart.json" "$LINK" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); items=d.get("response", d) if isinstance(d, dict) else d
for x in items:
    if x.get("id")==int(sys.argv[2]):
        print({k:x.get(k) for k in ("id","image","pdf","readable","preview")})
PY
docker exec "$APP" sh -c "ls /data/data/archives/${COLL}/${LINK}.pdf >/dev/null && echo archive_survived_restart=yes"

log "public image startup comparison (same migrated DB)"
docker stop "$APP" >/dev/null
SECONDS=0
docker run -d --name "$PUB" --network "$NET" \
    -p "127.0.0.1:${PUB_PORT}:3000" \
    --shm-size=1g \
    -v "$VOL_DATA":/data/data \
    -e DATABASE_URL=postgresql://linkwarden:change-me@"$PG":5432/linkwarden \
    -e NEXTAUTH_URL="http://127.0.0.1:${PUB_PORT}/api/v1/auth" \
    -e NEXTAUTH_SECRET=private-test-secret-000000000000000000 \
    "$PUB_IMAGE" >/dev/null
PUB_READY=""
for i in $(seq 1 240); do
    if curl -fsS "$PUB_BASE/" >/dev/null 2>&1; then PUB_READY=$SECONDS; break; fi
    sleep 1
done
echo "public_startup_to_http_200_seconds=$PUB_READY"
docker rm -f "$PUB" >/dev/null 2>&1 || true

log "sizes"
docker image inspect "$APP_IMAGE" --format 'private_size_bytes={{.Size}}'
docker image inspect "$PUB_IMAGE" --format 'public_size_bytes={{.Size}}'
python3 -I -c "p=$(docker image inspect "$APP_IMAGE" --format '{{.Size}}'); q=$(docker image inspect "$PUB_IMAGE" --format '{{.Size}}'); print('delta_bytes=%d delta_mib=%.1f' % (p-q, (p-q)/1048576))"

log "done"
