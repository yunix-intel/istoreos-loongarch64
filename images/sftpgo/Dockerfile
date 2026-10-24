FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux sqlite-libs && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1103 sftpgo && \
    useradd -u 1103 -g 1103 -M -d /var/lib/sftpgo -s /sbin/nologin sftpgo && \
    mkdir -p /etc/sftpgo /var/lib/sftpgo /usr/share/sftpgo /srv/sftpgo/data /srv/sftpgo/backups && \
    chown -R sftpgo:sftpgo /var/lib/sftpgo /srv/sftpgo
COPY sftpgo /usr/local/bin/sftpgo
COPY sftpgo.json /etc/sftpgo/sftpgo.json
COPY templates/ /usr/share/sftpgo/templates/
COPY static/ /usr/share/sftpgo/static/
COPY openapi/ /usr/share/sftpgo/openapi/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's|"users_base_dir": "",|"users_base_dir": "/srv/sftpgo/data",|' /etc/sftpgo/sftpgo.json && \
    sed -i 's|"backups_path": "backups"|"backups_path": "/srv/sftpgo/backups"|' /etc/sftpgo/sftpgo.json && \
    chmod 0755 /usr/local/bin/sftpgo /usr/local/bin/docker-entrypoint.sh && \
    chown -R sftpgo:sftpgo /srv/sftpgo
ENV TZ=Asia/Shanghai \
    SFTPGO_LOG_FILE_PATH=""
EXPOSE 8080 2022
VOLUME ["/srv/sftpgo/data", "/srv/sftpgo/backups", "/var/lib/sftpgo"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/ >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
