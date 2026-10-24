#!/bin/sh
if [ -f /proc/net/if_inet6 ]; then
    sed -i 's/#listen \[::\]:/listen [::]:/g' /etc/nginx/conf.d/default.conf
fi
