FROM openeuler/openeuler:24.03

LABEL org.opencontainers.image.title="Tautulli" \
      org.opencontainers.image.version="v2.18.2" \
      org.opencontainers.image.source="https://github.com/Tautulli/Tautulli"

ENV TZ=UTC \
    PYTHONUNBUFFERED=1 \
    TAUTULLI_DOCKER=True

RUN dnf install -y python3 python3-pip shadow-utils \
    && dnf clean all \
    && rm -rf /var/cache/dnf

WORKDIR /app
COPY src/ /app/

# Tautulli vendors pure-Python deps in ./lib; pip install keeps the image
# reproducible and provides the documented pip-based install path.
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r /app/requirements.txt

RUN groupadd -g 1000 tautulli \
    && useradd -u 1000 -g 1000 -M -s /sbin/nologin tautulli \
    && mkdir -p /config \
    && chown -R 1000:1000 /config \
    && printf 'v2.18.2\n' > /app/version.txt \
    && printf 'master\n' > /app/branch.txt

VOLUME /config
EXPOSE 8181

USER 1000:1000
ENTRYPOINT ["python3", "Tautulli.py", "--datadir", "/config", "--nolaunch"]
CMD ["--quiet"]
