# Open WebUI 0.12.3 (latest stable, 2026-10-16) on openEuler 24.03 / loong64
# Lightweight ("slim") build: external AI providers only, SQLite state, no local
# torch/sentence-transformers/onnxruntime/chromadb/whisper/OCR stack.
# The PyPI wheel ships the prebuilt Svelte frontend (240 MB), so no Node/Vite step.
FROM openeuler/openeuler:24.03

ENV TZ=UTC \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    USE_SLIM_DOCKER=true \
    DATA_DIR=/app/backend/data

COPY open_webui-0.12.3-py3-none-any.whl /tmp/open_webui.whl
COPY requirements-lite.txt /tmp/requirements-lite.txt
# maturin 1.15.0 loongarch wheel is installed by hand: pip 23.3 does not know
# the loongarch64 platform tag and would fall back to building maturin from
# source (which recursively needs maturin). The PEP 517 backend also needs the
# Python module, not only the executable.
COPY maturin-1.15.0.whl /tmp/maturin.whl

# Single RUN: install build toolchain + loongarch RPM deps, build the four
# source packages, then remove the build-only packages in the same layer so
# they do not inflate the final image.
RUN set -eux; \
    dnf install -y \
        python3 python3-pip python3-setuptools python3-devel \
        gcc gcc-c++ make cmake ninja-build pkgconf-pkg-config unzip \
        rust cargo re2 re2-devel abseil-cpp abseil-cpp-devel libstdc++ \
        python3-numpy python3-cryptography python3-aiohttp python3-brotli \
        python3-lxml python3-pillow python3-psutil python3-bcrypt \
        python3-argon2-cffi python3-regex python3-orjson python3-tiktoken \
        python3-greenlet python3-pycares python3-zstandard \
        python3-uvloop python3-httptools python3-websockets \
        python3-pyyaml python3-attrs python3-jsonschema python3-referencing \
        python3-rpds-py python3-markupsafe python3-Authlib \
        ca-certificates tzdata; \
    dnf clean all; rm -rf /var/cache/dnf; \
    python3 -m venv --system-site-packages /opt/venv; \
    unzip -q -o /tmp/maturin.whl -d /opt/venv/lib/python3.11/site-packages; \
    install -m 0755 /opt/venv/lib/python3.11/site-packages/maturin-1.15.0.data/scripts/maturin /opt/venv/bin/maturin; \
    . /opt/venv/bin/activate; \
    pip install -U 'setuptools>=77' wheel; \
    pip install pybind11; \
    pip install --no-build-isolation uuid-utils==0.14.0; \
    pip install --no-build-isolation pycrdt==0.14.8; \
    pip install --no-build-isolation google-re2==1.1.20251105; \
    pip install --no-build-isolation -r /tmp/requirements-lite.txt; \
    pip install --no-deps /tmp/open_webui.whl; \
    pip install --no-deps joserfc==1.7.4; \
    dnf remove -y python3-devel gcc gcc-c++ make cmake ninja-build \
        pkgconf-pkg-config rust cargo re2-devel abseil-cpp-devel; \
    dnf install -y python3-numpy findutils; \
    dnf clean all; rm -rf /var/cache/dnf /tmp/* /root/.cargo /root/.cache; \
    find /opt/venv -name '__pycache__' -type d -prune -exec rm -rf '{}' +; \
    mkdir -p /app/backend/data

ENV PATH=/opt/venv/bin:$PATH

WORKDIR /app/backend/data
EXPOSE 8080
VOLUME ["/app/backend/data"]

# open-webui serve sets FROM_INIT_PY=true; the wheel's bundled frontend is used.
ENTRYPOINT ["open-webui", "serve", "--host", "0.0.0.0", "--port", "8080"]
