FROM openeuler/openeuler:24.03

RUN dnf install -y ca-certificates tzdata \
    && dnf clean all

COPY out/filebrowser /usr/local/bin/filebrowser
RUN chmod 0755 /usr/local/bin/filebrowser \
    && mkdir -p /database /srv

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/filebrowser","-a","0.0.0.0","-d","/database/filebrowser.db","-r","/srv"]
