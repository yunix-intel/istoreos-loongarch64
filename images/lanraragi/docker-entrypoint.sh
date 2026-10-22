#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /home/koyomi/lanraragi/{content,thumb,database,log,temp}
chown -R koyomi:koyomi /home/koyomi/lanraragi

redis-server --daemonize yes \
    --dir /home/koyomi/lanraragi/database \
    --save "" --appendonly no
for _ in $(seq 1 30); do
    redis-cli ping >/dev/null 2>&1 && break
    sleep 0.5
done

cd /home/koyomi/lanraragi
exec runuser -u koyomi -- env \
    PERL5LIB=/home/koyomi/perl5/lib/perl5:/home/koyomi/perl5/lib/perl5/loongarch64-linux-thread-multi \
    LRR_NETWORK="${LRR_NETWORK:-http://*:3000}" \
    perl script/launcher.pl -f script/lanraragi "$@"
