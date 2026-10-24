FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g; s|^metalink=|#metalink=|' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        nginx php-fpm php-cli php-pdo php-mysqlnd php-mbstring php-xml php-gd \
        php-curl php-intl php-opcache \
        curl tzdata bash shadow util-linux procps-ng && \
    dnf install -y php-pecl-zip && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/www/bookstack /run/php-fpm /var/log/nginx /var/lib/nginx && \
    chown -R nginx:nginx /var/lib/nginx /var/log/nginx
COPY app/ /var/www/bookstack/
COPY vendor/ /var/www/bookstack/vendor/
COPY nginx.conf /etc/nginx/nginx.conf
COPY bookstack.conf /etc/nginx/conf.d/bookstack.conf
COPY php-fpm-www.conf /etc/php-fpm.d/www.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh && \
    chown -R nginx:nginx /var/www/bookstack/storage /var/www/bookstack/bootstrap/cache /var/www/bookstack/public/uploads 2>/dev/null || true
ENV TZ=Asia/Shanghai \
    APP_ENV=production \
    APP_DEBUG=false
EXPOSE 80
VOLUME ["/var/www/bookstack/storage", "/var/www/bookstack/public/uploads"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -fsS http://127.0.0.1/login >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
