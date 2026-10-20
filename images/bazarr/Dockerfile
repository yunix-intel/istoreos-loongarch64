# Bazarr 1.6.2 on loong64
# Python application; dependencies built from source where PyPI has no loongarch64 wheels.
FROM openeuler/openeuler:24.03 AS builder

RUN dnf install -y python3 python3-pip python3-devel python3-numpy \
        gcc gcc-c++ make patch \
        libxml2-devel libxslt-devel zlib-devel libjpeg-turbo-devel \
        freetype-devel libffi-devel openssl-devel \
    && dnf clean all && rm -rf /var/cache/dnf

# --system-site-packages lets pip use the distro numpy (1.24.3, loongarch64).
RUN python3 -m venv --system-site-packages /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# PyPI has no loongarch64 Pillow wheel and requirements.txt pins --only-binary;
# install it first from source so the requirements pass sees it satisfied.
RUN pip install --no-cache-dir --no-binary=Pillow "Pillow>=9.0.0"

# webrtcvad-wheels only ships binary wheels (no loongarch64, no sdist);
# the upstream webrtcvad sdist provides the same module and builds cleanly.
COPY requirements-docker.txt /tmp/requirements.txt
COPY webrtcvad-2.0.10/ /tmp/webrtcvad-2.0.10/
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir /tmp/webrtcvad-2.0.10

COPY bazarr-1.6.2/ /app/


FROM openeuler/openeuler:24.03

# Runtime libraries for lxml/Pillow/numpy plus ffmpeg for audio sync.
RUN dnf install -y python3 python3-numpy \
        libxml2 libxslt zlib libjpeg-turbo freetype libpng \
        p7zip ffmpeg ca-certificates tzdata \
    && dnf clean all && rm -rf /var/cache/dnf

# openEuler p7zip only ships 7za; Bazarr looks for the "7z" name.
RUN ln -sf /usr/bin/7za /usr/local/bin/7z

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    XDG_CONFIG_HOME=/config \
    HOME=/config \
    TZ=UTC

RUN mkdir -p /config

EXPOSE 6767
VOLUME ["/config"]

ENTRYPOINT ["python3", "/app/bazarr.py", "--config", "/config", "--no-update"]
