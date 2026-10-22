FROM openeuler/openeuler:24.03
RUN sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/*.repo && \
    dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        ca-certificates tzdata curl bash shadow util-linux procps-ng git tar xz \
        openssl-devel libffi-devel zlib-devel bzip2-devel xz-devel sqlite-devel \
        ncurses-devel readline-devel libxml2-devel libxslt-devel \
        libjpeg-turbo-devel libtiff-devel freetype-devel \
        gcc gcc-c++ make rust cargo pkgconf-pkg-config && \
    dnf clean all && rm -rf /var/cache/dnf && \
    groupadd -g 1000 hermes && useradd -u 1000 -g 1000 -M -d /data/.hermes -s /bin/bash hermes && \
    mkdir -p /data/.hermes/webui /workspace /opt/hermes-agent /opt/hermes-webui && \
    chown -R hermes:hermes /data /workspace
COPY python/ /usr/local/
RUN ln -sf /usr/local/bin/python3.14 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/python3.14 /usr/local/bin/python
COPY get-pip.py /tmp/get-pip.py
RUN python3 /tmp/get-pip.py --no-cache-dir && rm -f /tmp/get-pip.py && python3 -m pip --version
COPY app/ /opt/hermes-agent/
COPY gen-requirements.py /tmp/gen-requirements.py
RUN python3 -m pip install --no-cache-dir --no-deps \
        browser-harness==0.1.13 "cryptography==50.0.1" "pynacl>=1.6,<1.7"
RUN python3 -m pip install --no-cache-dir packaging && \
    HERMES_NIX_BUILD=1 python3 -m pip install --no-cache-dir --no-deps /opt/hermes-agent && \
    python3 /tmp/gen-requirements.py && \
    python3 -m pip install --no-cache-dir -r /tmp/hermes-reqs.txt
COPY webui/ /opt/hermes-webui/
RUN python3 -m pip install --no-cache-dir -r /opt/hermes-webui/requirements.txt
COPY docker-entrypoint.sh /usr/local/bin/hermes-entrypoint
RUN chmod 0755 /usr/local/bin/hermes-entrypoint && \
    chown -R hermes:hermes /data /workspace /opt/hermes-agent /opt/hermes-webui
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HERMES_HOME=/data/.hermes \
    HERMES_AGENT_DIR=/opt/hermes-agent \
    HERMES_WEBUI_DIR=/opt/hermes-webui \
    HERMES_WEBUI_HOST=0.0.0.0 \
    HERMES_WEBUI_PORT=8787 \
    HERMES_WEBUI_STATE_DIR=/data/.hermes/webui \
    HERMES_WEBUI_AGENT_DIR=/workspace \
    HERMES_WEBUI_DEFAULT_WORKSPACE=/workspace
WORKDIR /workspace
EXPOSE 8787
VOLUME ["/data/.hermes", "/workspace"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8787/health || exit 1
ENTRYPOINT ["/usr/local/bin/hermes-entrypoint"]
