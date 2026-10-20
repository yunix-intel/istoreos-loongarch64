#!/usr/bin/env bash
set -Eeuo pipefail

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-$POSTGRES_USER}"
POSTGRES_HOST_AUTH_METHOD="${POSTGRES_HOST_AUTH_METHOD:-scram-sha-256}"
export PGDATA POSTGRES_USER POSTGRES_DB

as_postgres() {
    runuser -u postgres -- "$@"
}

mkdir -p "$PGDATA" /var/run/postgresql
chown postgres:postgres "$PGDATA" /var/run/postgresql

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    if [ -z "${POSTGRES_PASSWORD:-}" ] && [ "$POSTGRES_HOST_AUTH_METHOD" != "trust" ]; then
        echo >&2 "error: POSTGRES_PASSWORD is required unless POSTGRES_HOST_AUTH_METHOD=trust"
        exit 1
    fi

    chown -R postgres:postgres "$PGDATA"

    pwfile=""
    if [ -n "${POSTGRES_PASSWORD:-}" ]; then
        pwfile="$(mktemp)"
        printf '%s\n' "$POSTGRES_PASSWORD" >"$pwfile"
        chown postgres:postgres "$pwfile"
        chmod 0600 "$pwfile"
    fi

    args=(
        initdb -D "$PGDATA" -U "$POSTGRES_USER"
        --auth-local=trust --auth-host="$POSTGRES_HOST_AUTH_METHOD"
        --encoding=UTF8 --locale=C.UTF-8
    )
    if [ -n "$pwfile" ]; then
        args+=(--pwfile="$pwfile")
    fi
    as_postgres "${args[@]}"
    rm -f "$pwfile"

    {
        echo "listen_addresses = '*'"
        echo "unix_socket_directories = '/var/run/postgresql'"
        echo "logging_collector = off"
    } >>"$PGDATA/postgresql.conf"
    echo "host all all all $POSTGRES_HOST_AUTH_METHOD" >>"$PGDATA/pg_hba.conf"

    as_postgres pg_ctl -D "$PGDATA" \
        -o "-c listen_addresses='' -c unix_socket_directories=/tmp" -w start
    if [ "$POSTGRES_DB" != "postgres" ]; then
        as_postgres createdb -h /tmp -U "$POSTGRES_USER" "$POSTGRES_DB"
    fi
    as_postgres pg_ctl -D "$PGDATA" -m fast -w stop
fi

if [ "$#" -eq 0 ]; then
    set -- postgres -D "$PGDATA" \
        -c listen_addresses='*' \
        -c unix_socket_directories=/var/run/postgresql
fi

exec runuser -u postgres -- "$@"
