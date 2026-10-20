# Calibre-Web 0.6.27 loong64 image
# Base: openEuler 24.03 LTS SP4 (loongarch64 packages)
# Python: system 3.11.6 + venv; wheels built from source where loong64
# wheels are missing (lxml, nh3, cryptography, netifaces-plus, regex).
FROM openeuler/openeuler:24.03 AS pybuild

# cryptography/openssl-sys: link system OpenSSL instead of vendoring
ENV OPENSSL_NO_VENDOR=1

RUN dnf install -y \
        python3 python3-pip python3-devel \
        gcc gcc-c++ make pkgconf \
        rust cargo \
        openssl-devel libxml2-devel libxslt-devel libffi-devel zlib-devel \
        sqlite-devel libjpeg-turbo-devel libpng-devel ImageMagick-devel file-devel \
    && dnf clean all

COPY src/calibre-web-0.6.27/requirements.txt /tmp/requirements.txt

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && /opt/venv/bin/pip check

# ---- runtime ----
FROM openeuler/openeuler:24.03

RUN dnf install -y \
        python3 \
        libxml2 libxslt libffi openssl-libs zlib libjpeg-turbo libpng \
        ImageMagick ghostscript file-libs sqlite-libs \
        ca-certificates curl tzdata \
    && dnf clean all

COPY --from=pybuild /opt/venv /opt/venv
COPY src/calibre-web-0.6.27 /app

ENV PATH=/opt/venv/bin:$PATH \
    CALIBRE_DBPATH=/config

WORKDIR /app
RUN mkdir -p /config /books

EXPOSE 8083
VOLUME ["/config", "/books"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8083/ >/dev/null || exit 1

CMD ["python3", "/app/cps.py"]
