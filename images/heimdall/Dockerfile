# Heimdall 2.8.3 on loong64
# openEuler 24.03 ships PHP 8.3, but Heimdall 2.8.3 (Laravel 13 / Symfony 8.4)
# requires PHP >= 8.4.1, so PHP 8.4 is built from source in a builder stage.
FROM openeuler/openeuler:24.03 AS php-build

ARG PHP_VERSION=8.4.26
ARG PHP_SHA256=32a2de53862ad44ed4a5005244ce4f1b50c271e74dced215449a4443b40569f1

RUN dnf install -y gcc gcc-c++ make pkgconf curl tar xz \
        libxml2-devel sqlite-devel libcurl-devel openssl-devel \
        oniguruma-devel libicu-devel libzip-devel libsodium-devel \
        zlib-devel bzip2-devel \
    && dnf clean all && rm -rf /var/cache/dnf

RUN curl -fsSL -o /tmp/php.tar.xz "https://www.php.net/distributions/php-${PHP_VERSION}.tar.xz" \
    && echo "${PHP_SHA256}  /tmp/php.tar.xz" | sha256sum -c - \
    && mkdir -p /tmp/php-src \
    && tar -xJf /tmp/php.tar.xz -C /tmp/php-src --strip-components=1 \
    && cd /tmp/php-src \
    && ./configure \
        --prefix=/usr/local/php \
        --sysconfdir=/usr/local/php/etc \
        --with-config-file-path=/usr/local/php/etc \
        --enable-fpm \
        --with-fpm-user=nginx \
        --with-fpm-group=nginx \
        --enable-mbstring \
        --with-openssl \
        --with-curl \
        --with-zip \
        --with-sodium \
        --enable-intl \
        --with-pdo-sqlite \
        --with-sqlite3 \
        --with-zlib \
        --disable-cgi \
        --disable-phpdbg \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/php-src /tmp/php.tar.xz

RUN curl -fsSL -o /usr/local/bin/composer https://getcomposer.org/download/latest-stable/composer.phar \
    && chmod +x /usr/local/bin/composer

FROM openeuler/openeuler:24.03

ENV PATH=/usr/local/php/bin:/usr/local/php/sbin:$PATH \
    TZ=UTC

RUN dnf install -y nginx libicu libzip oniguruma libsodium sqlite libcurl libxml2 openssl-libs tar gzip ca-certificates \
    && dnf clean all && rm -rf /var/cache/dnf \
    && rm -f /etc/nginx/conf.d/default.conf

COPY --from=php-build /usr/local/php /usr/local/php
COPY --from=php-build /usr/local/bin/composer /usr/local/bin/composer

COPY src /var/www/html
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/heimdall.conf /etc/nginx/conf.d/heimdall.conf
COPY deploy/php-fpm.conf /usr/local/php/etc/php-fpm.conf
COPY deploy/php.ini /usr/local/php/etc/php.ini
COPY deploy/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh /usr/local/bin/composer \
    && cd /var/www/html \
    && COMPOSER_ALLOW_SUPERUSER=1 composer install --no-dev --no-interaction --no-scripts --prefer-dist --optimize-autoloader \
    && rm -rf /root/.composer /root/.cache/composer

EXPOSE 8080
VOLUME ["/config"]
CMD ["/entrypoint.sh"]
