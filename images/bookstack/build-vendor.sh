#!/usr/bin/env bash
set -Eeuo pipefail

sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo
dnf install -y --setopt=install_weak_deps=False \
    php-cli php-pdo php-mysqlnd php-mbstring php-xml php-gd php-curl php-intl php-pecl-zip \
    unzip git >/tmp/bookstack-dnf.log 2>&1

curl -sS https://getcomposer.org/installer | \
    php -- --install-dir=/usr/local/bin --filename=composer >/tmp/composer-install.log 2>&1
composer --version

cd /app
composer install --no-dev --prefer-dist --no-interaction --no-progress \
    --optimize-autoloader

rm -rf /vendor/vendor
cp -a vendor /vendor/vendor
rm -rf /vendor/bootstrap-cache
cp -a bootstrap/cache /vendor/bootstrap-cache
