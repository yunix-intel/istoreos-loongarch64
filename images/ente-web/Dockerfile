FROM cr.loongnix.cn/library/nginx:1.30.0

COPY out/ /out/
COPY default.conf /etc/nginx/conf.d/default.conf
COPY 90-replace-ente-env.sh /docker-entrypoint.d/90-replace-ente-env.sh
COPY 40-enable-ipv6.sh /docker-entrypoint.d/40-enable-ipv6.sh
RUN chmod +x /docker-entrypoint.d/90-replace-ente-env.sh /docker-entrypoint.d/40-enable-ipv6.sh

ENV ENTE_API_ORIGIN=http://localhost:8080

EXPOSE 3000 3001 3002 3003 3004 3005 3006 3008 3009 3010
