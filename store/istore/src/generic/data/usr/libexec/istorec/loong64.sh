#!/bin/sh
# Generic iStore installer for LoongArch64 app-meta packages.
#
# Reads /usr/lib/opkg/meta/<id>.json (field .loong64.runtime is a generated
# shell projection of the JSON schema) and renders docker run commands.
# Falls back to /usr/share/istore-loong64/apps/<id>.conf when jsonfilter is
# unavailable.
#
# Usage: loong64.sh <app-id> <action> [args]
#
# Actions: install upgrade rm purge start stop restart status status-all
#          port ports url logs sidecars render config pull list
#
# Per-app overrides (UCI /etc/config/<id>):
#   option variant      public|private
#   option image        explicit image, wins over variant
#   option host_port    primary host port override
#   option data_path    primary data volume host path override
#   option env_file     KEY=VALUE file (default /etc/istore-loong64/env/<id>.env)
#   option enabled      0 to refuse install/start

set -u

APP_ID="${1:-}"
ACTION="${2:-}"

usage() {
	cat <<'EOF'
usage: loong64.sh <app-id> <action>

  install | upgrade       pull image(s), create network, start sidecars, (re)create app
  rm                      remove app and sidecar containers, keep data
  purge                   rm, and delete /srv/<app-id> when ISTORE_PURGE_DATA=1
  start | stop | restart  control the app and its sidecars
  status                  print main container state (running/exited/not-installed)
  status-all              print main and sidecar states
  port                    print the primary host port
  ports                   print all port mappings
  url                     print the primary URL
  logs [n]                tail main container logs
  sidecars                list sidecar containers and states
  render                  print the generated docker script without running it
  config                  print resolved runtime configuration
  pull                    pull images only
  list                    list installed LoongArch64 app-meta packages
EOF
}

[ -n "$APP_ID" ] || { usage; exit 1; }

META_DIR="${META_DIR:-/usr/lib/opkg/meta}"
STATE_DIR="${STATE_DIR:-/etc/istore-loong64}"
SECRET_DIR="$STATE_DIR/secrets"
ENV_DIR="$STATE_DIR/env"
DEFAULT_DIR="${DEFAULT_DIR:-/usr/share/istore-loong64/defaults}"
APP_CONF="${APP_CONF:-/usr/share/istore-loong64/apps/$APP_ID.conf}"
META="$META_DIR/$APP_ID.json"
DOCKER="${DOCKER:-docker}"
LOCK_DIR="${LOCK_DIR:-/var/lock}"
TMP_DIR="${TMP_DIR:-/tmp}"
mkdir -p "$TMP_DIR" 2>/dev/null || TMP_DIR=/tmp

log() { printf '%s\n' "[istore-loong64] $*" >&2; }
die() { log "ERROR: $*"; exit 1; }

case "$APP_ID" in
*[!a-z0-9_-]*) die "invalid app id: $APP_ID" ;;
esac

command -v "$DOCKER" >/dev/null 2>&1 || die "docker not found (install docker-deps)"

# ---------------------------------------------------------------------------
# metadata loading
# ---------------------------------------------------------------------------

if [ -f "$META" ]; then
	if command -v jsonfilter >/dev/null 2>&1; then
		_runtime=$(jsonfilter -i "$META" -e '@.loong64.runtime' 2>/dev/null || true)
		[ -n "$_runtime" ] && eval "$_runtime"
	fi
fi

if [ -z "${APP_IMAGE:-}" ]; then
	[ -f "$APP_CONF" ] || die "cannot read $META (.loong64.runtime) and no $APP_CONF"
	. "$APP_CONF"
fi

: "${APP_ID:=$APP_ID}"
: "${APP_TITLE:=$APP_ID}"
: "${APP_IMAGE:=yunixintel/$APP_ID:24.10-la5}"
: "${APP_DEFAULT_VARIANT:=public}"
: "${APP_VARIANTS:=}"
: "${APP_PORTS:=}"
: "${APP_VOLUMES:=}"
: "${APP_ENV:=}"
: "${APP_SIDECARS:=}"
: "${APP_SIDECAR_COMMAND:=}"
: "${APP_SIDECAR_ENV:=}"
: "${APP_SIDECAR_VOLUMES:=}"
: "${APP_SIDECAR_PORTS:=}"
: "${APP_DEVICES:=}"
: "${APP_CAPS:=}"
: "${APP_GROUPS:=}"
: "${APP_SYSCTLS:=}"
: "${APP_HOST_NETWORK:=0}"
: "${APP_DOCKER_SOCK:=0}"
: "${APP_DOCKER_SOCK_RO:=1}"
: "${APP_SHM:=}"
: "${APP_USER:=}"
: "${APP_COMMAND:=}"
: "${APP_RESTART:=unless-stopped}"
: "${APP_NETWORK_GROUP:=}"
: "${APP_REQUIRES_APP:=}"
: "${APP_HEALTH_PATH:=}"
: "${APP_HEALTH_PORT:=}"
: "${APP_MANUAL:=}"
: "${APP_REVIEW:=}"

# ---------------------------------------------------------------------------
# config / uci
# ---------------------------------------------------------------------------

uci_get() {
	command -v uci >/dev/null 2>&1 || return 0
	uci -q get "$APP_ID.main.$1" 2>/dev/null || true
}

variant_get() {
	_v=$(uci_get variant)
	if [ -z "${_v:-}" ] && command -v uci >/dev/null 2>&1; then
		_v=$(uci -q get istore_loong64.settings.default_variant 2>/dev/null || true)
	fi
	[ -n "${_v:-}" ] || _v="$APP_DEFAULT_VARIANT"
	printf '%s' "$_v"
}

image_get() {
	_explicit=$(uci_get image)
	if [ -n "${_explicit:-}" ]; then
		printf '%s' "$_explicit"
		return 0
	fi
	_v=$(variant_get)
	_img="$APP_IMAGE"
	if [ -n "$APP_VARIANTS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r v img _url <<EOF
$rec
EOF
			if [ "$v" = "$_v" ] && [ -n "${img:-}" ]; then
				_img="$img"
			fi
		done <<EOF
$APP_VARIANTS
EOF
	fi
	printf '%s' "$_img"
}

detect_host_ip() {
	_ip=$(uci_get_ip 2>/dev/null || true)
	if [ -z "$_ip" ] && command -v hostname >/dev/null 2>&1; then
		_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
	fi
	if [ -z "$_ip" ] && command -v ip >/dev/null 2>&1; then
		_ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
	fi
	[ -n "$_ip" ] || _ip="127.0.0.1"
	printf '%s' "$_ip"
}

uci_get_ip() {
	command -v uci >/dev/null 2>&1 || return 0
	uci -q get network.lan.ipaddr 2>/dev/null || true
}

primary_port() {
	_override=$(uci_get host_port)
	if [ -n "${_override:-}" ]; then
		printf '%s' "$_override"
		return 0
	fi
	if [ -n "$APP_PORTS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r _name _cont _host _proto _prim <<EOF
$rec
EOF
			if [ "${_prim:-0}" = "1" ]; then
				if [ "${_host:-0}" = "0" ] || [ -z "${_host:-}" ]; then
					printf '%s' "$_cont"
				else
					printf '%s' "$_host"
				fi
				return 0
			fi
		done <<EOF
$APP_PORTS
EOF
	fi
	printf '0'
}

HOST_IP=$(detect_host_ip)
VARIANT=$(variant_get)
PRIMARY_PORT=$(primary_port)
PUBLIC_URL="http://$HOST_IP:$PRIMARY_PORT"

# ---------------------------------------------------------------------------
# secrets and value expansion
# ---------------------------------------------------------------------------

secret_get() {
	_name=$1
	_len=${2:-32}
	if ! mkdir -p "$SECRET_DIR" 2>/dev/null; then
		SECRET_DIR="$TMP_DIR/istore-secrets"
		mkdir -p "$SECRET_DIR" 2>/dev/null || die "cannot create secret directory"
	fi
	chmod 700 "$SECRET_DIR" 2>/dev/null || true
	_file="$SECRET_DIR/$APP_ID.env"
	[ -f "$_file" ] || { : >"$_file"; chmod 600 "$_file"; }
	_val=$(grep -F "$_name=" "$_file" 2>/dev/null | tail -n 1 | cut -d= -f2- || true)
	if [ -z "${_val:-}" ]; then
		_val=$(head -c 96 /dev/urandom 2>/dev/null | base64 2>/dev/null | tr -dc 'A-Za-z0-9' | head -c "$_len")
		if [ -z "${_val:-}" ]; then
			_val=$(date +%s%N 2>/dev/null | sha256sum 2>/dev/null | cut -c1-"$_len")
		fi
		[ -n "${_val:-}" ] || die "cannot generate secret $_name"
		printf '%s=%s\n' "$_name" "$_val" >>"$_file"
	fi
	printf '%s' "$_val"
}

# expand ${SECRET:name[:len]}, ${PUBLIC_URL}, ${HOST_IP}, ${PRIMARY_PORT},
# ${APP_ID} and ${VARIANT} in an environment value.
expand_value() {
	_v=$1
	_v=$(printf '%s' "$_v" | sed \
		-e "s|\${PUBLIC_URL}|$PUBLIC_URL|g" \
		-e "s|\${HOST_IP}|$HOST_IP|g" \
		-e "s|\${PRIMARY_PORT}|$PRIMARY_PORT|g" \
		-e "s|\${APP_ID}|$APP_ID|g" \
		-e "s|\${VARIANT}|$VARIANT|g")
	_n=0
	while :; do
		_n=$((_n + 1))
		[ "$_n" -le 32 ] || break
		case "$_v" in
		*'${SECRET:'*) ;;
		*) break ;;
		esac
		_rest=${_v#*'${SECRET:'}
		_token=${_rest%%\}*}
		_sname=$_token
		_slen=32
		case "$_token" in
		*:*)
			_sname=${_token%%:*}
			_slen=${_token#*:}
			;;
		esac
		case "$_slen" in
		'' | *[!0-9]*) _slen=32 ;;
		esac
		_sval=$(secret_get "$_sname" "$_slen")
		_v=$(printf '%s' "$_v" | sed -e "s|\${SECRET:$_token}|$_sval|g")
	done
	printf '%s' "$_v"
}

env_override() {
	_key=$1
	_file=$(uci_get env_file)
	[ -n "${_file:-}" ] || _file="$ENV_DIR/$APP_ID.env"
	[ -f "$_file" ] || return 0
	grep -F "$_key=" "$_file" 2>/dev/null | tail -n 1 | cut -d= -f2- || true
}

# ---------------------------------------------------------------------------
# script helpers
# ---------------------------------------------------------------------------

shq() {
	printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

append_line() {
	printf '%s\n' "$*" >>"$SCRIPT"
}

# volume preparation command lines
volume_prep_lines() {
	_records=$1
	[ -n "$_records" ] || return 0
	while IFS= read -r rec; do
		[ -n "$rec" ] || continue
		IFS='|' read -r _name _host _cont _mode _owner _primary _type _seed <<EOF
$rec
EOF
		[ -n "${_host:-}" ] || continue
		if [ "${_type:-dir}" = "file" ]; then
			append_line "mkdir -p $(shq "$(dirname "$_host")")"
			append_line "if [ ! -e $(shq "$_host") ]; then"
			if [ -n "${_seed:-}" ] && [ -f "$DEFAULT_DIR/$APP_ID/$_seed" ]; then
				append_line "  cp $(shq "$DEFAULT_DIR/$APP_ID/$_seed") $(shq "$_host")"
			else
				append_line "  : > $(shq "$_host")"
			fi
			append_line "fi"
		else
			append_line "mkdir -p $(shq "$_host")"
		fi
		if [ -n "${_owner:-}" ]; then
			append_line "chown $_owner $(shq "$_host") 2>/dev/null || true"
		fi
	done <<EOF
$_records
EOF
}

# sidecar volume records: sidecar|volname|host|container|mode|owner
sidecar_volume_prep_lines() {
	_records=$1
	[ -n "$_records" ] || return 0
	while IFS= read -r rec; do
		[ -n "$rec" ] || continue
		IFS='|' read -r _sn _vn _host _cont _mode _owner <<EOF
$rec
EOF
		[ -n "${_host:-}" ] || continue
		append_line "mkdir -p $(shq "$_host")"
		if [ -n "${_owner:-}" ]; then
			append_line "chown $_owner $(shq "$_host") 2>/dev/null || true"
		fi
	done <<EOF
$_records
EOF
}

# ---------------------------------------------------------------------------
# render the docker script
# ---------------------------------------------------------------------------

render_script() {
	_out=$1
	_img=$(image_get)
	_net_group=$APP_NETWORK_GROUP
	[ -n "$_net_group" ] || _net_group=$APP_ID
	NET_NAME="istore-$_net_group"
	MAIN_NET="--network $NET_NAME"
	[ "$APP_HOST_NETWORK" = "1" ] && MAIN_NET="--network host"

	SCRIPT="$_out"
	: >"$SCRIPT"
	append_line "#!/bin/sh"
	append_line "set -e"
	append_line "# generated by /usr/libexec/istorec/loong64.sh for $APP_ID"
	append_line "DOCKER=$(shq "$DOCKER")"

	if [ "$APP_HOST_NETWORK" != "1" ]; then
		append_line "if ! \$DOCKER network inspect $(shq "$NET_NAME") >/dev/null 2>&1; then"
		append_line "  \$DOCKER network create $(shq "$NET_NAME") >/dev/null"
		append_line "fi"
	fi

	# main volumes
	volume_prep_lines "$APP_VOLUMES"

	# sidecars
	if [ -n "$APP_SIDECARS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r s_name s_image s_shm s_network s_variants s_hcmd s_hint s_htmo s_hret s_preload <<EOF
$rec
EOF
			[ -n "${s_name:-}" ] || continue
			if [ -n "${s_variants:-}" ]; then
				case ",$s_variants," in
				*",$VARIANT,"*) ;;
				*) continue ;;
				esac
			fi
			s_full="${s_name}"
			sidecar_volume_prep_lines "$(printf '%s\n' "$APP_SIDECAR_VOLUMES" | grep "^${s_name}|" || true)"
			append_line "if \$DOCKER inspect $(shq "$s_full") >/dev/null 2>&1; then"
			append_line "  \$DOCKER start $(shq "$s_full") >/dev/null 2>&1 || true"
			append_line "else"
			_run="$DOCKER run -d --name $(shq "$s_full") --restart $(shq "$APP_RESTART") --label $(shq "com.yunixintel.istore.app=$APP_ID") --label $(shq "com.yunixintel.istore.sidecar=$s_name")"
			if [ -n "${s_network:-}" ] && [ "$s_network" != "$NET_NAME" ]; then
				_run="$_run --network $(shq "$s_network")"
			elif [ "$APP_HOST_NETWORK" != "1" ]; then
				_run="$_run --network $(shq "$NET_NAME")"
			fi
			if [ -n "${s_shm:-}" ]; then
				_run="$_run --shm-size $(shq "$s_shm")"
			fi
			if [ -n "${s_hcmd:-}" ]; then
				s_hcmd=$(expand_value "$s_hcmd")
				_run="$_run --health-cmd $(shq "$s_hcmd") --health-interval ${s_hint:-10s} --health-timeout ${s_htmo:-5s} --health-retries ${s_hret:-10}"
			fi
			# sidecar ports
			if [ -n "$APP_SIDECAR_PORTS" ]; then
				_p=$(printf '%s\n' "$APP_SIDECAR_PORTS" | grep "^${s_name}|" || true)
				if [ -n "$_p" ]; then
					while IFS= read -r prec; do
						[ -n "$prec" ] || continue
						IFS='|' read -r _sn _pc _ph _pp <<EOF
$prec
EOF
						if [ "${_ph:-0}" != "0" ] && [ -n "${_ph:-}" ]; then
							_map="${_ph}:${_pc}"
							[ "${_pp:-tcp}" = "udp" ] && _map="$_map/udp"
							_run="$_run -p $(shq "$_map")"
						fi
					done <<EOF
$_p
EOF
				fi
			fi
			# sidecar volumes
			if [ -n "$APP_SIDECAR_VOLUMES" ]; then
				_v=$(printf '%s\n' "$APP_SIDECAR_VOLUMES" | grep "^${s_name}|" || true)
				if [ -n "$_v" ]; then
					while IFS= read -r vrec; do
						[ -n "$vrec" ] || continue
						IFS='|' read -r _sn _vn _vh _vc _vm _vo <<EOF
$vrec
EOF
						_mount="${_vh}:${_vc}"
						[ "${_vm:-rw}" = "ro" ] && _mount="$_mount:ro"
						_run="$_run -v $(shq "$_mount")"
					done <<EOF
$_v
EOF
				fi
			fi
			# sidecar env
			if [ -n "$APP_SIDECAR_ENV" ]; then
				_e=$(printf '%s\n' "$APP_SIDECAR_ENV" | grep "^${s_name}|" || true)
				if [ -n "$_e" ]; then
					while IFS= read -r erec; do
						[ -n "$erec" ] || continue
						IFS='|' read -r _sn _ek _ev _er <<EOF
$erec
EOF
						_ev=$(expand_value "$_ev")
						_ov=$(env_override "${s_name}_${_ek}")
						[ -n "${_ov:-}" ] && _ev="$_ov"
						_run="$_run -e $(shq "$_ek=$_ev")"
					done <<EOF
$_e
EOF
				fi
			fi
			# image first, then the command arguments
			_run="$_run $(shq "$s_image")"
			# sidecar command
			if [ -n "$APP_SIDECAR_COMMAND" ]; then
				_c=$(printf '%s\n' "$APP_SIDECAR_COMMAND" | grep "^${s_name}\^" || true)
				if [ -n "$_c" ]; then
					_args=""
					_rest=${_c#*^}
					_old_ifs=$IFS
					IFS='^'
					for _a in $_rest; do
						_args="$_args $(shq "$_a")"
					done
					IFS=$_old_ifs
					_run="$_run$(printf '%s' "$_args")"
				fi
			fi
			append_line "  $_run"
			append_line "fi"
			# wait for sidecar
			append_line "i=0"
			append_line "while [ \$i -lt ${s_hret:-30} ]; do"
			append_line "  st=\$(\$DOCKER inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $(shq "$s_full") 2>/dev/null || echo missing)"
			append_line "  case \"\$st\" in healthy|running) break;; exited|dead|unhealthy) \$DOCKER logs --tail 80 $(shq "$s_full") >&2 || true; echo $(shq "sidecar failed: $s_full") >&2; exit 1;; esac"
			append_line "  i=\$((i+1)); sleep 2"
			append_line "done"
			if [ -z "${s_hcmd:-}" ]; then
				append_line "sleep 2"
			fi
		done <<EOF
$APP_SIDECARS
EOF
	fi

	# main container
	append_line "\$DOCKER rm -f $(shq "$APP_ID") >/dev/null 2>&1 || true"
	_run="$DOCKER run -d --name $(shq "$APP_ID") --restart $(shq "$APP_RESTART") --label $(shq "com.yunixintel.istore.app=$APP_ID") --label $(shq "com.yunixintel.istore.variant=$VARIANT") $MAIN_NET"
	if [ "$APP_HOST_NETWORK" != "1" ] && [ -n "$APP_PORTS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r _name _cont _host _proto _prim <<EOF
$rec
EOF
			[ "${_host:-0}" = "0" ] && continue
			[ -n "${_host:-}" ] || continue
			_map="${_host}:${_cont}"
			[ "${_proto:-tcp}" = "udp" ] && _map="$_map/udp"
			_run="$_run -p $(shq "$_map")"
		done <<EOF
$APP_PORTS
EOF
	fi
	if [ -n "$APP_VOLUMES" ]; then
		_data_override=$(uci_get data_path)
		_first=1
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r _name _host _cont _mode _owner _primary _type _seed <<EOF
$rec
EOF
			if [ "${_primary:-0}" = "1" ] && [ -n "${_data_override:-}" ]; then
				_host="$_data_override"
			fi
			[ -n "${_host:-}" ] || continue
			_mount="${_host}:${_cont}"
			[ "${_mode:-rw}" = "ro" ] && _mount="$_mount:ro"
			_run="$_run -v $(shq "$_mount")"
			_first=0
		done <<EOF
$APP_VOLUMES
EOF
	fi
	if [ "$APP_DOCKER_SOCK" = "1" ]; then
		_sock="/var/run/docker.sock:/var/run/docker.sock"
		[ "$APP_DOCKER_SOCK_RO" = "1" ] && _sock="$_sock:ro"
		_run="$_run -v $(shq "$_sock")"
	fi
	if [ -n "$APP_ENV" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r _ek _ev _er _evars <<EOF
$rec
EOF
			if [ -n "${_evars:-}" ]; then
				case ",$_evars," in
				*",$VARIANT,"*) ;;
				*) continue ;;
				esac
			fi
			_ov=$(env_override "$_ek")
			[ -n "${_ov:-}" ] && _ev="$_ov"
			_ev=$(expand_value "$_ev")
			if [ -z "${_ev:-}" ] && [ "${_er:-0}" = "1" ]; then
				_envf=$(uci_get env_file)
				[ -n "${_envf:-}" ] || _envf="$ENV_DIR/$APP_ID.env"
				die "required environment variable $_ek is empty (set it in $_envf)"
			fi
			case "$_ev" in
			*'<'*'>'* | *'${'*)
				if [ "${_er:-0}" = "1" ]; then
					die "required environment variable $_ek is unresolved: $_ev"
				fi
				log "WARNING: unresolved $_ek=$_ev"
				;;
			esac
			[ -z "${_ev:-}" ] && continue
			_run="$_run -e $(shq "$_ek=$_ev")"
		done <<EOF
$APP_ENV
EOF
	fi
	if [ -n "$APP_DEVICES" ]; then
		while IFS= read -r _d; do
			[ -n "$_d" ] || continue
			_run="$_run --device $(shq "$_d")"
		done <<EOF
$APP_DEVICES
EOF
	fi
	if [ -n "$APP_CAPS" ]; then
		while IFS= read -r _c; do
			[ -n "$_c" ] || continue
			_run="$_run --cap-add $(shq "$_c")"
		done <<EOF
$APP_CAPS
EOF
	fi
	if [ -n "$APP_GROUPS" ]; then
		while IFS= read -r _g; do
			[ -n "$_g" ] || continue
			_run="$_run --group-add $(shq "$_g")"
		done <<EOF
$APP_GROUPS
EOF
	fi
	if [ -n "$APP_SYSCTLS" ]; then
		while IFS= read -r _s; do
			[ -n "$_s" ] || continue
			_run="$_run --sysctl $(shq "$_s")"
		done <<EOF
$APP_SYSCTLS
EOF
	fi
	if [ -n "$APP_SHM" ]; then
		_run="$_run --shm-size $(shq "$APP_SHM")"
	fi
	if [ -n "$APP_USER" ]; then
		_run="$_run --user $(shq "$APP_USER")"
	fi
	# image first, then the command arguments
	_run="$_run $(shq "$_img")"
	if [ -n "$APP_COMMAND" ]; then
		_old_ifs=$IFS
		IFS='^'
		for _a in $APP_COMMAND; do
			_run="$_run $(shq "$_a")"
		done
		IFS=$_old_ifs
	fi
	append_line "$_run"
	append_line "echo $(shq "installed $APP_TITLE ($APP_ID)")"
	append_line "echo $(shq "URL: $PUBLIC_URL/")"
}

# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------

LOCK_PATH=""
acquire_lock() {
	if ! mkdir -p "$LOCK_DIR" 2>/dev/null; then
		LOCK_DIR="$TMP_DIR"
	fi
	LOCK_PATH="$LOCK_DIR/istore-$APP_ID.lock"
	_i=0
	while ! mkdir "$LOCK_PATH" 2>/dev/null; do
		_i=$((_i + 1))
		[ "$_i" -lt 60 ] || die "another operation is in progress for $APP_ID"
		sleep 1
	done
	trap 'rmdir "$LOCK_PATH" 2>/dev/null || true' EXIT INT TERM
}

check_arch() {
	case "$(uname -m 2>/dev/null || echo unknown)" in
	loongarch64 | loong64) ;;
	*) log "WARNING: host is $(uname -m), images are linux/loong64 only" ;;
	esac
}

check_manual() {
	if [ -n "$APP_MANUAL" ]; then
		log "WARNING: this app needs manual preparation: $APP_MANUAL"
	fi
	if [ -n "$APP_REQUIRES_APP" ]; then
		_req_conf="$META_DIR/$APP_REQUIRES_APP.json"
		if [ ! -f "$_req_conf" ]; then
			log "WARNING: recommended companion app not installed: $APP_REQUIRES_APP"
		fi
	fi
}

pull_images() {
	_img=$(image_get)
	case "$_img" in
	local/*)
		"$DOCKER" image inspect "$_img" >/dev/null 2>&1 || die "private image not preloaded: $_img"
		log "using preloaded private image $_img"
		;;
	*)
		log "pulling $_img"
		"$DOCKER" pull "$_img" || die "docker pull failed: $_img"
		;;
	esac
	if [ -n "$APP_SIDECARS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r s_name s_image _s_shm _s_net s_variants _s_cmd _s_hint _s_htmo _s_hret s_preload <<EOF
$rec
EOF
			if [ -n "${s_variants:-}" ]; then
				case ",$s_variants," in
				*",$VARIANT,"*) ;;
				*) continue ;;
				esac
			fi
			if [ "${s_preload:-0}" = "1" ]; then
				"$DOCKER" image inspect "$s_image" >/dev/null 2>&1 || die "sidecar image must be preloaded (not redistributable or local-only): $s_image"
			else
				case "$s_image" in
				local/*) "$DOCKER" image inspect "$s_image" >/dev/null 2>&1 || die "private sidecar image not preloaded: $s_image" ;;
				*) log "pulling $s_image"; "$DOCKER" pull "$s_image" || die "docker pull failed: $s_image" ;;
				esac
			fi
		done <<EOF
$APP_SIDECARS
EOF
	fi
}

do_render() {
	_out="$TMP_DIR/istore-$APP_ID.run.sh"
	render_script "$_out"
	cat "$_out"
}

do_install() {
	check_arch
	check_manual
	_enabled=$(uci_get enabled)
	[ "${_enabled:-1}" = "0" ] && die "$APP_ID is disabled in /etc/config/$APP_ID"
	_out="$TMP_DIR/istore-$APP_ID.run.sh"
	render_script "$_out"
	pull_images
	log "running install script for $APP_ID"
	if ! sh "$_out"; then
		log "install failed; recent output follows"
		[ -f "$SECRET_DIR/$APP_ID.env" ] && log "secrets: $SECRET_DIR/$APP_ID.env"
		exit 1
	fi
	log "done: $APP_TITLE ($APP_ID), port $(primary_port)"
}

do_rm() {
	check_arch
	"$DOCKER" rm -f "$APP_ID" >/dev/null 2>&1 || true
	if [ -n "$APP_SIDECARS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			s_name=$(printf '%s' "$rec" | cut -d'|' -f1)
			"$DOCKER" rm -f "${s_name}" >/dev/null 2>&1 || true
		done <<EOF
$APP_SIDECARS
EOF
	fi
	_net_group=$APP_NETWORK_GROUP
	[ -n "$_net_group" ] || _net_group=$APP_ID
	"$DOCKER" network rm "istore-$_net_group" >/dev/null 2>&1 || true
	log "removed containers for $APP_ID; data kept"
}

do_start() {
	check_arch
	_state=$(container_state "$APP_ID")
	if [ "$_state" = "not-installed" ]; then
		log "$APP_ID is not installed; running install"
		do_install
		return $?
	fi
	if [ -n "$APP_SIDECARS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			s_name=$(printf '%s' "$rec" | cut -d'|' -f1)
			"$DOCKER" start "${s_name}" >/dev/null 2>&1 || true
		done <<EOF
$APP_SIDECARS
EOF
	fi
	"$DOCKER" start "$APP_ID" >/dev/null 2>&1 || die "docker start failed for $APP_ID"
	log "started $APP_ID"
}

do_stop() {
	"$DOCKER" stop "$APP_ID" >/dev/null 2>&1 || true
	if [ -n "$APP_SIDECARS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			s_name=$(printf '%s' "$rec" | cut -d'|' -f1)
			"$DOCKER" stop "${s_name}" >/dev/null 2>&1 || true
		done <<EOF
$APP_SIDECARS
EOF
	fi
	log "stopped $APP_ID"
}

container_state() {
	_c=$1
	"$DOCKER" inspect -f '{{.State.Status}}' "$_c" 2>/dev/null || echo "not-installed"
}

do_status() {
	if [ "${1:-}" = "--verbose" ] || [ "$ACTION" = "status-all" ]; then
		printf '%s: %s\n' "$APP_ID" "$(container_state "$APP_ID")"
		if [ -n "$APP_SIDECARS" ]; then
			while IFS= read -r rec; do
				[ -n "$rec" ] || continue
				s_name=$(printf '%s' "$rec" | cut -d'|' -f1)
				s_variants=$(printf '%s' "$rec" | cut -d'|' -f5)
				if [ -n "$s_variants" ]; then
					case ",$s_variants," in
					*",$VARIANT,"*) ;;
					*) continue ;;
					esac
				fi
				printf '  %s: %s\n' "${s_name}" "$(container_state "${s_name}")"
			done <<EOF
$APP_SIDECARS
EOF
		fi
	else
		container_state "$APP_ID"
	fi
}

do_ports() {
	if [ -n "$APP_PORTS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			IFS='|' read -r _name _cont _host _proto _prim <<EOF
$rec
EOF
			printf '%s\t%s\t%s\t%s\t%s\n' "${_name:-port}" "${_host:-0}" "${_cont:-0}" "${_proto:-tcp}" "${_prim:-0}"
		done <<EOF
$APP_PORTS
EOF
	else
		printf '%s\n' "$(primary_port)"
	fi
}

do_config() {
	_img=$(image_get)
	printf 'APP_ID=%s\n' "$APP_ID"
	printf 'APP_TITLE=%s\n' "$APP_TITLE"
	printf 'IMAGE=%s\n' "$_img"
	printf 'VARIANT=%s\n' "$VARIANT"
	printf 'HOST_IP=%s\n' "$HOST_IP"
	printf 'PRIMARY_PORT=%s\n' "$(primary_port)"
	printf 'PUBLIC_URL=%s\n' "$PUBLIC_URL"
	printf 'NETWORK=%s\n' "$([ "$APP_HOST_NETWORK" = 1 ] && echo host || echo "istore-${APP_NETWORK_GROUP:-$APP_ID}")"
	printf 'HOST_NETWORK=%s\n' "$APP_HOST_NETWORK"
	printf 'DOCKER_SOCK=%s\n' "$APP_DOCKER_SOCK"
	printf 'MANUAL=%s\n' "$APP_MANUAL"
	printf 'REVIEW=%s\n' "$APP_REVIEW"
	do_ports
}

do_list() {
	printf '%-22s %-14s %s\n' "APP" "STATE" "TITLE"
	for _f in "$META_DIR"/*.json; do
		[ -f "$_f" ] || continue
		command -v jsonfilter >/dev/null 2>&1 || break
		_id=$(jsonfilter -i "$_f" -e '@.name' 2>/dev/null || true)
		[ -n "${_id:-}" ] || continue
		_has=$(jsonfilter -i "$_f" -e '@.loong64.schema' 2>/dev/null || true)
		[ -n "${_has:-}" ] || continue
		_title=$(jsonfilter -i "$_f" -e '@.title' 2>/dev/null || echo "$_id")
		_state="not-installed"
		if command -v "$DOCKER" >/dev/null 2>&1; then
			_state=$(container_state "$_id")
		fi
		printf '%-22s %-14s %s\n' "$_id" "$_state" "$_title"
	done
}

case "$ACTION" in
install)
	acquire_lock
	do_install
	;;
upgrade)
	acquire_lock
	do_install
	;;
rm)
	acquire_lock
	do_rm
	;;
purge)
	acquire_lock
	do_rm
	if [ "${ISTORE_PURGE_DATA:-0}" = "1" ]; then
		rm -rf "/srv/$APP_ID"
		log "deleted /srv/$APP_ID"
	else
		log "data kept; set ISTORE_PURGE_DATA=1 to delete /srv/$APP_ID"
	fi
	;;
start)
	acquire_lock
	do_start
	;;
stop)
	acquire_lock
	do_stop
	;;
restart)
	acquire_lock
	do_stop
	do_start
	;;
status)
	do_status
	;;
status-all)
	do_status --verbose
	;;
port)
	primary_port
	printf '\n'
	;;
ports)
	do_ports
	;;
url)
	printf '%s/\n' "$PUBLIC_URL"
	;;
logs)
	"$DOCKER" logs --tail "${3:-200}" "$APP_ID" 2>&1 || true
	;;
sidecars)
	if [ -n "$APP_SIDECARS" ]; then
		while IFS= read -r rec; do
			[ -n "$rec" ] || continue
			s_name=$(printf '%s' "$rec" | cut -d'|' -f1)
			s_variants=$(printf '%s' "$rec" | cut -d'|' -f5)
			if [ -n "$s_variants" ]; then
				case ",$s_variants," in
				*",$VARIANT,"*) ;;
				*) continue ;;
				esac
			fi
			printf '%s\t%s\n' "${s_name}" "$(container_state "${s_name}")"
		done <<EOF
$APP_SIDECARS
EOF
	fi
	;;
render)
	do_render
	;;
config)
	do_config
	;;
pull)
	acquire_lock
	pull_images
	;;
list)
	do_list
	;;
*)
	usage
	exit 1
	;;
esac
