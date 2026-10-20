# Paperless-ngx 3.3.2 on loong64
# Base: openEuler 24.03 LTS (loongarch64), Python 3.11, PHP-free stack.
#
# The Angular frontend is architecture-independent static JS/CSS/HTML.  It is
# taken from the official multi-arch 3.3.2 image (linux/amd64) because the
# Angular 22 CLI requires Node >= 22, while loongarch64 only has Node 20.
# Everything else (Python deps, native extensions, OCR toolchain) is built
# from source or from loongarch64 wheels on the Loongson PyPI mirror.

# qpdf 12.4.2 is required by pikepdf 10.x (ocrmypdf 17.12 requires
# pikepdf>=10.2).  openEuler 24.03 ships qpdf 11.1.0, whose C++ API is too old.
FROM openeuler/openeuler:24.03 AS qpdf
RUN set -eux; \
    dnf install -y --setopt=install_weak_deps=False \
        gcc gcc-c++ make cmake zlib-devel libjpeg-turbo-devel \
        openssl-devel curl tar; \
    dnf clean all; rm -rf /var/cache/dnf; \
    curl -fsSL https://github.com/qpdf/qpdf/releases/download/v12.4.2/qpdf-12.4.2.tar.gz \
        | tar xz -C /tmp; \
    cmake -S /tmp/qpdf-12.4.2 -B /tmp/qpdf-build \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_DOC=OFF -DINSTALL_MANUAL=OFF \
        -DCMAKE_INSTALL_LIBDIR=lib; \
    cmake --build /tmp/qpdf-build -j"$(nproc)"; \
    cmake --install /tmp/qpdf-build; \
    rm -rf /tmp/qpdf-12.4.2 /tmp/qpdf-build

FROM openeuler/openeuler:24.03

# Headers, shared library and the qpdf CLI; runtime loader path is registered
# below so pikepdf and the CLI find libqpdf.so.30.
COPY --from=qpdf /usr/local /usr/local
RUN echo /usr/local/lib > /etc/ld.so.conf.d/usr-local.conf && ldconfig

ENV TZ=UTC \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/paperless/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PAPERLESS_DATA_DIR=/data \
    PAPERLESS_MEDIA_ROOT=/data/media \
    PAPERLESS_CONSUMPTION_DIR=/data/consume \
    PAPERLESS_EXPORT_DIR=/data/export \
    PAPERLESS_REDIS=redis://127.0.0.1:6379/0 \
    PAPERLESS_TIME_ZONE=UTC \
    TESSDATA_PREFIX=/usr/share/tessdata \
    PAPERLESS_OCR_LANGUAGE=eng \
    # unpaper is not packaged for openEuler 24.03 loongarch64.
    PAPERLESS_OCR_CLEAN=none \
    PAPERLESS_AI_ENABLED=NO

WORKDIR /usr/src/paperless

COPY requirements.txt /tmp/requirements.txt
COPY entrypoint.sh /entrypoint.sh
COPY paperless-ngx-3.3.2/src/ ./src/
COPY frontend/ ./src/documents/static/frontend/

# One RUN keeps compilers, cargo registry and pip build trees out of the final
# image layer.
RUN set -eux; \
    dnf install -y --setopt=install_weak_deps=False \
        python3 python3-pip \
        gcc gcc-c++ make cmake pkgconf patchelf rust cargo \
        python3-devel \
        libjpeg-turbo-devel zlib-devel libtiff-devel freetype-devel \
        lcms2-devel libwebp-devel openjpeg2-devel harfbuzz-devel \
        openssl-devel libffi-devel sqlite-devel \
        libxml2-devel libxslt-devel \
        curl ca-certificates tar unzip xz gettext \
        ghostscript poppler-utils file \
        tesseract tesseract-langpack-eng tesseract-langpack-chi_sim tesseract-osd \
        pngquant jbig2dec ImageMagick gnupg redis tzdata; \
    ln -sf /usr/share/tesseract/tessdata/eng.traineddata /usr/share/tessdata/eng.traineddata; \
    ln -sf /usr/share/tesseract/tessdata/chi_sim.traineddata /usr/share/tessdata/chi_sim.traineddata; \
    ln -sf /usr/share/tesseract/tessdata/osd.traineddata /usr/share/tessdata/osd.traineddata; \
    dnf clean all; rm -rf /var/cache/dnf; \
    python3 -m venv /opt/paperless/venv; \
    /opt/paperless/venv/bin/pip install --no-cache-dir -U pip setuptools wheel; \
    CARGO_HOME=/tmp/cargo CARGO_TARGET_DIR=/tmp/cargo-target \
    /opt/paperless/venv/bin/pip install --no-cache-dir --prefer-binary \
        --index-url https://lpypi.loongnix.cn/loongson/pypi/+simple \
        --extra-index-url https://pypi.org/simple \
        --trusted-host lpypi.loongnix.cn \
        -r /tmp/requirements.txt; \
    dnf remove -y --setopt=clean_requirements_on_remove=False \
        gcc gcc-c++ make cmake pkgconf patchelf rust cargo python3-devel \
        libjpeg-turbo-devel zlib-devel libtiff-devel freetype-devel \
        lcms2-devel libwebp-devel openjpeg2-devel harfbuzz-devel \
        openssl-devel libffi-devel sqlite-devel \
        libxml2-devel libxslt-devel; \
    rm -rf /usr/local/include/qpdf /usr/local/lib/cmake/qpdf \
        /usr/local/lib/pkgconfig/libqpdf.pc /usr/local/lib/libqpdf.a; \
    dnf clean all; \
    rm -rf /var/cache/dnf /tmp/* /root/.cache /root/.cargo /usr/local/cargo; \
    chmod +x /entrypoint.sh; \
    mkdir -p /data/media /data/consume /data/export /usr/src/paperless/static; \
    cd /usr/src/paperless/src; \
    PAPERLESS_SECRET_KEY=build-time-dummy \
        /opt/paperless/venv/bin/python manage.py collectstatic --no-input; \
    PAPERLESS_SECRET_KEY=build-time-dummy \
        /opt/paperless/venv/bin/python manage.py compilemessages || true

VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=10 \
    CMD curl -fsS -L --max-time 3 http://127.0.0.1:8000/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
