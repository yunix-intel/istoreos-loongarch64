FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates httpd-tools && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /data
COPY rest-server /usr/bin/rest-server
COPY create_user /usr/bin/create_user
COPY delete_user /usr/bin/delete_user
COPY entrypoint.sh /entrypoint.sh
RUN chmod 0755 /usr/bin/rest-server /usr/bin/create_user /usr/bin/delete_user /entrypoint.sh
ENV DATA_DIRECTORY=/data \
    PASSWORD_FILE=/data/.htpasswd
VOLUME ["/data"]
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
