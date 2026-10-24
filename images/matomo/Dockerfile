FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        nginx php-fpm php-cli php-pdo php-mysqlnd php-mbstring php-xml php-gd \
        php-curl php-intl php-bcmath php-opcache curl tzdata bash shadow util-linux procps-ng && \
    dnf install -y php-pecl-zip && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/www/matomo /run/php-fpm /var/log/nginx /var/lib/nginx && \
    chown -R nginx:nginx /var/lib/nginx /var/log/nginx
COPY app/ /var/www/matomo/
COPY nginx.conf /etc/nginx/nginx.conf
COPY matomo.conf /etc/nginx/conf.d/matomo.conf
COPY php-fpm-www.conf /etc/php-fpm.d/www.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh && \
    mkdir -p /var/www/matomo/config /var/www/matomo/tmp && \
    chown -R nginx:nginx /var/www/matomo/config /var/www/matomo/tmp
ENV TZ=Asia/Shanghai
EXPOSE 80
VOLUME ["/var/www/matomo/config", "/var/www/matomo/tmp"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -fsS http://127.0.0.1/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
