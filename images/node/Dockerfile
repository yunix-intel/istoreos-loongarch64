FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata libstdc++ && \
    dnf clean all && rm -rf /var/cache/dnf
COPY node-v22.23.3-linux-loong64/ /opt/node22/
ENV PATH=/opt/node22/bin:$PATH
CMD ["node", "--version"]
