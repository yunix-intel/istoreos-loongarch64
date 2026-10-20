# FreshRSS 1.30.1 on loong64
# Base: openEuler 24.03 LTS (loongarch64), PHP 8.3 + nginx + php-fpm, SQLite.

FROM openeuler/openeuler:24.03

ENV TZ=UTC \
    LANG=en_US.UTF-8 \
    COMPOSER_ALLOW_SUPERUSER=1

RUN set -eux; \
    dnf install -y --setopt=install_weak_deps=False \
        nginx \
        php-cli php-fpm php-common php-pdo php-mbstring php-intl \
        php-gmp php-xml php-gd php-opcache php-pecl-zip php-process php-sodium \
        curl ca-certificates tar unzip; \
    dnf clean all; rm -rf /var/cache/dnf; \
    rm -f /etc/nginx/conf.d/default.conf /etc/php-fpm.d/www.conf

COPY freshrss-1.30.1.tar.gz /tmp/freshrss.tar.gz
COPY deploy/nginx.conf        /etc/nginx/nginx.conf
COPY deploy/freshrss.conf     /etc/nginx/conf.d/freshrss.conf
COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf
COPY deploy/99-freshrss.ini   /etc/php.d/99-freshrss.ini
COPY deploy/entrypoint.sh     /entrypoint.sh

RUN set -eux; \
    tar xzf /tmp/freshrss.tar.gz -C /var/www; \
    mv /var/www/FreshRSS-1.30.1 /var/www/FreshRSS; \
    rm -f /tmp/freshrss.tar.gz; \
    curl -fsSL https://getcomposer.org/download/latest-stable/composer.phar \
        -o /usr/local/bin/composer; \
    chmod +x /usr/local/bin/composer; \
    cd /var/www/FreshRSS; \
    php /usr/local/bin/composer install --no-dev --no-interaction \
        --optimize-autoloader --no-progress; \
    mkdir -p /var/www/FreshRSS/data \
             /run/php-fpm /var/log/php-fpm /var/log/nginx /var/lib/nginx; \
    chown -R root:nginx /var/www/FreshRSS; \
    chown -R nginx:nginx /var/www/FreshRSS/data; \
    chmod +x /entrypoint.sh

EXPOSE 8080
VOLUME ["/var/www/FreshRSS/data"]

ENTRYPOINT ["/entrypoint.sh"]
