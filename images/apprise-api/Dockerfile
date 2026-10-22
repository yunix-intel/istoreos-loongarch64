FROM openeuler/openeuler:24.03
RUN dnf install -y --disablerepo=debuginfo --disablerepo=EPOL --disablerepo=source --disablerepo=update-source \
        --setopt=retries=1 --setopt=timeout=15 --setopt=install_weak_deps=False \
        python3 python3-pip python3-devel python3-cryptography python3-gevent \
        gcc gcc-c++ make cmake libffi-devel openssl-devel \
        nginx shadow util-linux ca-certificates tzdata curl sed grep && \
    dnf clean all && rm -rf /var/cache/dnf
COPY requirements.txt constraints.txt /tmp/
RUN pip3 install --no-cache-dir -c /tmp/constraints.txt \
        -r /tmp/requirements.txt gunicorn supervisor && \
    pip3 install --no-cache-dir polib && \
    rm -rf /root/.cache/pip
COPY apprise_api /opt/apprise/webapp
COPY apprise_api/static /usr/share/nginx/html/s/
WORKDIR /opt/apprise
RUN python3 webapp/apprise_translations.py && \
    pip3 uninstall --yes -q polib && \
    chmod 0755 webapp/supervisord-startup && \
    mkdir -p /config/store /attach /plugin /tmp/apprise && \
    chmod 1777 /tmp/apprise && chmod 777 /config /config/store /attach /plugin &&     mkdir -p /var/log/nginx && chmod 777 /var/log/nginx &&     touch /etc/nginx/server-override.conf /etc/nginx/location-override.conf &&     chmod 666 /etc/nginx/server-override.conf /etc/nginx/location-override.conf
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APPRISE_CONFIG_DIR=/config \
    APPRISE_ATTACH_DIR=/attach \
    APPRISE_PLUGIN_PATHS=/plugin \
    TZ=Etc/UTC
VOLUME ["/config", "/attach", "/plugin"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=8 \
    CMD curl -fsS http://127.0.0.1:8000/ >/dev/null || exit 1
ENTRYPOINT ["/opt/apprise/webapp/supervisord-startup"]
