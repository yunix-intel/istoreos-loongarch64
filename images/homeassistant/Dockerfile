# Home Assistant Core 2026.10.2 - loong64 image
# Python 3.14.8 built from source on openEuler 24.03 (loongarch64)
# All C/Rust extensions compiled from source for linux_loongarch64
FROM openeuler/openeuler:24.03
RUN dnf install -y ca-certificates tzdata \
        brotli bzip2 freetype jbigkit-libs lcms2 libffi libgcc libjpeg-turbo \
        libpng libstdc++ libtiff libwebp libyaml ncurses-libs openjpeg2 \
        openssl-libs readline sqlite xz-libs zlib ffmpeg \
    && dnf clean all
COPY usrlocal/ /usr/local/
ENV PATH=/usr/local/ha-venv/bin:/usr/local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1
WORKDIR /config
VOLUME ["/config"]
EXPOSE 8123
CMD ["python3", "-m", "homeassistant", "--config", "/config"]
