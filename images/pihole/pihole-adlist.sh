#!/bin/bash
# Minimal adlist manager for the loong64 Pi-hole image.
# Usage:
#   pihole-adlist list
#   pihole-adlist add <url> [comment]
#   pihole-adlist remove <id>
set -euo pipefail

DB="${GRAVITY_DB:-/etc/pihole/gravity.db}"

usage() {
    echo "usage: pihole-adlist {list|add <url> [comment]|remove <id>}" >&2
    exit 1
}

sql_escape() {
    printf '%s' "$1" | sed "s/'/''/g"
}

case "${1:-}" in
    list)
        sqlite3 -header -column "$DB" \
            "SELECT id, address, enabled, comment FROM adlist ORDER BY id;"
        ;;
    add)
        url="${2:-}"
        comment="${3:-}"
        [ -n "$url" ] || usage
        sqlite3 "$DB" \
            "INSERT INTO adlist(address, enabled, comment) VALUES('$(sql_escape "$url")', 1, '$(sql_escape "$comment")');"
        echo "[pihole-adlist] added: $url"
        pihole -g
        ;;
    remove)
        id="${2:-}"
        [ -n "$id" ] || usage
        sqlite3 "$DB" "DELETE FROM adlist WHERE id = $id;"
        echo "[pihole-adlist] removed id=$id"
        pihole -g
        ;;
    *)
        usage
        ;;
esac
