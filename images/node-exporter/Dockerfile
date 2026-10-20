FROM scratch
COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY node_exporter /bin/node_exporter
EXPOSE 9100
ENTRYPOINT ["/bin/node_exporter"]
