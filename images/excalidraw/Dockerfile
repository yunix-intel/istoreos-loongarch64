FROM openeuler/openeuler:24.03

RUN dnf install -y nginx \
 && dnf clean all \
 && rm -rf /usr/share/nginx/html/* \
 && ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log

COPY nginx.conf /etc/nginx/nginx.conf
COPY build/ /usr/share/nginx/html/

EXPOSE 8080
STOPSIGNAL SIGQUIT
CMD ["nginx", "-g", "daemon off;"]
