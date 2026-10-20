# Nextcloud 33.0.10 on loong64
# openEuler 24.03 ships PHP 8.3.31; Nextcloud 33 supports PHP 8.2-8.5.
# SQLite deployment (test/lab); production should use MySQL/MariaDB or PostgreSQL.
FROM openeuler/openeuler:24.03

ENV TZ=UTC \
    LANG=en_US.UTF-8

RUN dnf install -y \
        nginx \
        php-cli php-fpm php-common php-pdo php-mbstring php-xml \
        php-gd php-intl php-ldap php-opcache php-process php-sodium \
        php-pecl-zip \
        bzip2 tar ca-certificates glibc-locale-source \
    && localedef -i en_US -f UTF-8 en_US.UTF-8 \
    && localedef -i zh_CN -f UTF-8 zh_CN.UTF-8 \
    && dnf remove -y glibc-locale-source \
    && dnf clean all && rm -rf /var/cache/dnf \
    && rm -f /etc/nginx/conf.d/default.conf /etc/php-fpm.d/www.conf

COPY nextcloud-33.0.10.tar.bz2 /tmp/nextcloud.tar.bz2

RUN mkdir -p /var/www/html \
    && tar -xjf /tmp/nextcloud.tar.bz2 -C /var/www/html --strip-components=1 \
    && rm -f /tmp/nextcloud.tar.bz2 \
    && mkdir -p /var/www/html/data /var/www/html/config \
                /run/php-fpm /var/log/nginx /var/lib/nginx

COPY deploy/nginx.conf        /etc/nginx/nginx.conf
COPY deploy/nextcloud.conf    /etc/nginx/conf.d/nextcloud.conf
COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf
COPY deploy/99-nextcloud.ini  /etc/php.d/99-nextcloud.ini
COPY deploy/entrypoint.sh     /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && chown -R nginx:nginx /var/www/html/data /var/www/html/config

EXPOSE 8080
VOLUME ["/var/www/html/data", "/var/www/html/config"]

ENTRYPOINT ["/entrypoint.sh"]
