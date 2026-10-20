#!/usr/bin/env bash
set -Eeuo pipefail

DATADIR="${MYSQL_DATADIR:-/var/lib/mysql}"
SOCKET="${MYSQL_SOCKET:-/run/mysqld/mysqld.sock}"
PIDFILE="/run/mysqld/mysqld.pid"
export DATADIR SOCKET PIDFILE

sql_str() {
    printf "'%s'" "$(printf '%s' "$1" | sed "s/'/''/g")"
}

sql_ident() {
    printf '%s' "$1" | sed 's/`/``/g'
}

sql_user() {
    printf '%s' "$1" | sed "s/'/''/g"
}

mkdir -p "$DATADIR" /run/mysqld
chown mysql:mysql "$DATADIR" /run/mysqld

if [ ! -d "$DATADIR/mysql" ]; then
    if [ -z "${MYSQL_ROOT_PASSWORD:-}" ] && [ "${MYSQL_ALLOW_EMPTY_PASSWORD:-}" != "yes" ]; then
        echo >&2 "error: MYSQL_ROOT_PASSWORD is required unless MYSQL_ALLOW_EMPTY_PASSWORD=yes"
        exit 1
    fi
    if [ -n "${MYSQL_USER:-}" ] && [ -z "${MYSQL_PASSWORD:-}" ] && [ "${MYSQL_ALLOW_EMPTY_PASSWORD:-}" != "yes" ]; then
        echo >&2 "error: MYSQL_PASSWORD is required when MYSQL_USER is set"
        exit 1
    fi

    chown -R mysql:mysql "$DATADIR"
    echo >&2 "info: initializing MariaDB data directory $DATADIR"
    runuser -u mysql -- mariadb-install-db \
        --user=mysql --datadir="$DATADIR" \
        --auth-root-authentication-method=normal --skip-test-db >/dev/null

    runuser -u mysql -- mariadbd \
        --datadir="$DATADIR" --socket="$SOCKET" --pid-file="$PIDFILE" \
        --skip-networking \
        --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci &
    tmppid=$!

    for _ in $(seq 1 60); do
        mariadb-admin --socket="$SOCKET" ping >/dev/null 2>&1 && break
        if ! kill -0 "$tmppid" 2>/dev/null; then
            echo >&2 "error: temporary MariaDB server exited during initialization"
            wait "$tmppid" || true
            exit 1
        fi
        sleep 1
    done

    root_pw="$(sql_str "${MYSQL_ROOT_PASSWORD:-}")"
    {
        echo "SET SESSION sql_mode=CONCAT(@@sql_mode, ',NO_BACKSLASH_ESCAPES');"
        echo "ALTER USER 'root'@'localhost' IDENTIFIED BY $root_pw;"
        if [ -n "${MYSQL_DATABASE:-}" ]; then
            echo "CREATE DATABASE IF NOT EXISTS \`$(sql_ident "$MYSQL_DATABASE")\`;"
        fi
        if [ -n "${MYSQL_USER:-}" ]; then
            echo "CREATE USER IF NOT EXISTS '$(sql_user "$MYSQL_USER")'@'%' IDENTIFIED BY $(sql_str "${MYSQL_PASSWORD:-}");"
            if [ -n "${MYSQL_DATABASE:-}" ]; then
                echo "GRANT ALL PRIVILEGES ON \`$(sql_ident "$MYSQL_DATABASE")\`.* TO '$(sql_user "$MYSQL_USER")'@'%';"
            fi
        fi
        echo "FLUSH PRIVILEGES;"
    } | mariadb --socket="$SOCKET" -u root

    kill -TERM "$(cat "$PIDFILE")" 2>/dev/null || true
    wait "$tmppid" || true
    echo >&2 "info: initialization complete"
fi

if [ "$#" -eq 0 ]; then
    set -- mariadbd \
        --datadir="$DATADIR" --socket="$SOCKET" --pid-file="$PIDFILE" \
        --bind-address=0.0.0.0 \
        --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
fi

exec runuser -u mysql -- "$@"
