# KodExplorer 4.55 (latest stable, 2026-09-28) on openEuler 24.03 / loong64
# PHP 8.3 (openEuler) + nginx + php-fpm. Source: kalcaddle/KodExplorer tag 4.55.
FROM openeuler/openeuler:24.03

ENV TZ=UTC \
    LANG=en_US.UTF-8

RUN dnf install -y \
        nginx \
        php-cli php-fpm php-common php-pdo php-mbstring php-curl \
        php-gd php-opcache php-xml php-json php-pecl-zip php-fileinfo \
        ca-certificates tar \
    && dnf clean all && rm -rf /var/cache/dnf \
    && rm -f /etc/nginx/conf.d/default.conf /etc/php-fpm.d/www.conf

COPY kodexplorer-4.55.tar.gz /tmp/kodexplorer.tar.gz

RUN mkdir -p /var/www/html \
    && tar xzf /tmp/kodexplorer.tar.gz -C /var/www/html --strip-components=1 \
    && rm -f /tmp/kodexplorer.tar.gz \
    && mkdir -p /run/php-fpm /var/log/php-fpm /var/log/nginx /var/lib/nginx

COPY deploy/nginx.conf        /etc/nginx/nginx.conf
COPY deploy/kodexplorer.conf  /etc/nginx/conf.d/kodexplorer.conf
COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf
COPY deploy/99-kodexplorer.ini /etc/php.d/99-kodexplorer.ini
COPY deploy/entrypoint.sh     /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && chown -R root:nginx /var/www/html \
    && chmod 775 /var/www/html /var/www/html/config /var/www/html/data \
    && chown -R nginx:nginx /var/www/html/data

EXPOSE 8080
VOLUME ["/var/www/html/data"]

ENTRYPOINT ["/entrypoint.sh"]
