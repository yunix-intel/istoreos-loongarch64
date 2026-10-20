FROM openeuler/openeuler:24.03

RUN dnf install -y ca-certificates tzdata && dnf clean all && rm -rf /var/cache/dnf

COPY pkg/syncthing-linux-loong64-v2.1.6/syncthing /usr/local/bin/syncthing
RUN chmod 0755 /usr/local/bin/syncthing && mkdir -p /var/syncthing

ENV TZ=Asia/Shanghai
VOLUME ["/var/syncthing"]

EXPOSE 8384 22000 21027/udp

ENTRYPOINT ["/usr/local/bin/syncthing", "--home=/var/syncthing", "--gui-address=0.0.0.0:8384"]
