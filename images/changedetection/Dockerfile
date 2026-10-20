FROM openeuler/openeuler:24.03

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    WEBDRIVER_BROWSER=firefox \
    FIREFOX_BIN=/usr/bin/firefox \
    GECKODRIVER_PATH=/usr/bin/geckodriver \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    MOZ_DISABLE_GMP_SANDBOX=1 \
    DISABLED_PROCESSORS=""

RUN set -eux; \
    dnf install -y --setopt=install_weak_deps=False \
        python3 python3-pip \
        gcc gcc-c++ make cmake pkgconf python3-devel \
        libxml2-devel libxslt-devel libjpeg-turbo-devel zlib-devel \
        openssl-devel libffi-devel \
        rust cargo gettext curl ca-certificates tzdata firefox opencv; \
    dnf clean all; rm -rf /var/cache/dnf; \
    python3 -m venv /opt/venv; \
    /opt/venv/bin/pip install --no-cache-dir -U pip setuptools wheel

COPY wheels /wheels
COPY geckodriver /usr/bin/geckodriver
COPY requirements.txt /tmp/requirements.txt
RUN CARGO_HOME=/tmp/cargo CARGO_TARGET_DIR=/tmp/cargo-target \
    /opt/venv/bin/pip install --no-cache-dir --prefer-binary \
        --index-url https://lpypi.loongnix.cn/loongson/pypi/+simple \
        --extra-index-url https://pypi.org/simple \
        --trusted-host lpypi.loongnix.cn \
        --find-links /wheels \
        -r /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir --prefer-binary \
        -i https://lpypi.loongnix.cn/loongson/pypi/+simple \
        --extra-index-url https://pypi.org/simple \
        --trusted-host lpypi.loongnix.cn \
        "numpy==1.26.4"
RUN SP=$(/opt/venv/bin/python -c "import site; print(site.getsitepackages()[0])") && \
    cp -a /usr/lib/python3.11/site-packages/cv2 "$SP/"

COPY . /app
WORKDIR /app
RUN chmod +x /usr/bin/geckodriver
RUN /opt/venv/bin/pybabel compile -d changedetectionio/translations || true

VOLUME ["/datastore"]
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=10 \
    CMD curl -fsS http://127.0.0.1:5000/ || exit 1
CMD ["/opt/venv/bin/python", "./changedetection.py", "-d", "/datastore"]
