#!/bin/sh
set -e
rm -rf /srv/ente
cp -a /out /srv/ente
find /srv/ente -name '*.js' -print0 | xargs -0 -r sed -i "s#ENTE_API_ORIGIN_PLACEHOLDER#${ENTE_API_ORIGIN}#g"
sed -i 's#root /out/#root /srv/ente/#g' /etc/nginx/conf.d/default.conf
echo "ente-web: endpoint rewritten to ${ENTE_API_ORIGIN}"
