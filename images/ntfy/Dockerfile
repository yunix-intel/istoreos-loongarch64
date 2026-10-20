FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False ca-certificates tzdata && \
    dnf clean all && rm -rf /var/cache/dnf && \
    mkdir -p /var/cache/ntfy /etc/ntfy
COPY ntfy /usr/bin/ntfy
EXPOSE 80
VOLUME ["/var/cache/ntfy", "/etc/ntfy"]
ENTRYPOINT ["/usr/bin/ntfy"]
CMD ["serve"]
