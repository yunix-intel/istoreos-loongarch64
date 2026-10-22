FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng \
        nginx libvirt-client libvirt-libs openldap cyrus-sasl-lib libffi libxml2 libxslt openssl-libs && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -o -g 33 www-data && useradd -u 33 -g 33 -M -d /var/www -s /sbin/nologin www-data && \
    mkdir -p /var/www/.ssh /srv/webvirtcloud/data /var/lib/nginx /var/log/nginx && \
    chown -R www-data:www-data /var/www /srv/webvirtcloud/data /var/lib/nginx /var/log/nginx
COPY app/ /srv/webvirtcloud/
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh /srv/webvirtcloud/console/novncd && \
    chown -R www-data:www-data /srv/webvirtcloud
WORKDIR /srv/webvirtcloud
EXPOSE 80
VOLUME ["/srv/webvirtcloud/data", "/var/www/.ssh"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
