# Typecho 1.3.0 on loong64
# openEuler 24.03 ships PHP 8.3; Typecho 1.3.0 runs on PHP 7.2+ (8.3 tested here).
# SQLite deployment for lab use (no external database server).
FROM openeuler/openeuler:24.03

ENV TZ=UTC \
    LANG=en_US.UTF-8

RUN dnf install -y \
        nginx \
        php-cli php-fpm php-common php-pdo php-mbstring php-curl \
        php-gd php-opcache \
        ca-certificates tar unzip \
    && dnf clean all && rm -rf /var/cache/dnf \
    && rm -f /etc/nginx/conf.d/default.conf /etc/php-fpm.d/www.conf

COPY typecho-1.3.0.zip /tmp/typecho.zip

RUN mkdir -p /var/www/html \
    && unzip -q /tmp/typecho.zip -d /var/www/html \
    && rm -f /tmp/typecho.zip \
    # Default the SQLite database to /var/www/html/typecho.db instead of usr/<rand>.db
    && sed -i "s|__TYPECHO_ROOT_DIR__ . '/usr/' . uniqid() . '.db'|__TYPECHO_ROOT_DIR__ . '/typecho.db'|" /var/www/html/install.php \
    && mkdir -p /var/www/html/usr/uploads \
                /run/php-fpm /var/log/php-fpm /var/log/nginx /var/lib/nginx

COPY deploy/nginx.conf        /etc/nginx/nginx.conf
COPY deploy/typecho.conf      /etc/nginx/conf.d/typecho.conf
COPY deploy/php-fpm-www.conf  /etc/php-fpm.d/www.conf
COPY deploy/99-typecho.ini    /etc/php.d/99-typecho.ini
COPY deploy/entrypoint.sh     /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    # Code stays root-owned; the docroot is group-writable so the installer can
    # create config.inc.php and typecho.db. usr/ (themes, plugins, uploads) is
    # owned by nginx because it is backed by a named volume.
    && chown -R root:nginx /var/www/html \
    && chmod 775 /var/www/html \
    && chown -R nginx:nginx /var/www/html/usr

EXPOSE 8080
VOLUME ["/var/www/html/usr"]

ENTRYPOINT ["/entrypoint.sh"]
