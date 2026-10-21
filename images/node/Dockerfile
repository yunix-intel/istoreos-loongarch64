FROM openeuler/openeuler:24.03
RUN dnf install -y --setopt=install_weak_deps=False \
        ca-certificates tzdata libstdc++ && \
    dnf clean all && rm -rf /var/cache/dnf
COPY node-v24.22.1-linux-loong64/ /opt/node24/
ENV PATH=/opt/node24/bin:$PATH
CMD ["node", "--version"]
