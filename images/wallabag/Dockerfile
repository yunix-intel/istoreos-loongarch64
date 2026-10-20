# Wallabag 2.6.14 on loong64
# openEuler 24.03 ships PHP 8.3.31; wallabag 2.6.x supports PHP 8.1-8.3.
# SQLite deployment (lab); switch parameters.yml to MySQL/PostgreSQL for production.
FROM openeuler/openeuler:24.03

ENV TZ=UTC \
    LANG=en_US.UTF-8

RUN dnf install -y \
        nginx \
        php-cli php-fpm php-common php-pdo php-mbstring php-xml \
        php-gd php-intl php-tidy php-opcache php-pecl-zip \
        tar gzip openssl ca-certificates util-linux \
    && dnf clean all && rm -rf /var/cache/dnf \
    && rm -f /etc/nginx/conf.d/default.conf /etc/php-fpm.d/www.conf

COPY wallabag-2.6.14.tar.gz /tmp/wallabag.tar.gz

RUN mkdir -p /var/www/wallabag \
    && tar -xzf /tmp/wallabag.tar.gz -C /var/www/wallabag --strip-components=1 \
    && rm -f /tmp/wallabag.tar.gz /var/www/wallabag/app/config/parameters.yml \
    && mkdir -p /var/www/wallabag/data/db \
                /var/www/wallabag/var/cache \
                /var/www/wallabag/var/logs \
                /run/php-fpm /var/log/php-fpm /var/log/nginx \
                /var/lib/nginx /var/lib/php/session

COPY deploy/nginx.conf        /etc/nginx/nginx.conf
COPY deploy/wallabag.conf     /etc/nginx/conf.d/wallabag.conf
COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf
COPY deploy/99-wallabag.ini   /etc/php.d/99-wallabag.ini
COPY deploy/entrypoint.sh     /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && chown -R nginx:nginx /var/www/wallabag/data /var/www/wallabag/var \
                /var/www/wallabag/app/config /var/lib/php/session /var/log/php-fpm \
    && chmod 750 /var/www/wallabag/data

EXPOSE 8080
VOLUME ["/var/www/wallabag/data"]

ENTRYPOINT ["/entrypoint.sh"]
