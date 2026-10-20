FROM scratch
COPY data /data
COPY tmp /tmp
COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY dozzle /dozzle
EXPOSE 8080
ENTRYPOINT ["/dozzle"]
