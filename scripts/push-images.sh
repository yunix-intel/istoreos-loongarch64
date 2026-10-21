#!/bin/bash
# 把龙芯应用镜像推到 Docker Hub（在龙芯盒子上跑）
# 用法：
#   docker login -u <你的DockerHub用户名>
#   DOCKER_USER=<你的DockerHub用户名> ./push-images.sh
# 说明：镜像已在盒子本地构建好，push 只是上传层，任意架构机器都能推。
#       本地 tag 名需与 Docker Hub 仓库名一致（例如 code-server、one-api、
#       nginx-proxy-manager、paperless-ngx）；不一致时先 docker tag 成 <name>:loong64。
set -euo pipefail

: "${DOCKER_USER:?请先设置 DOCKER_USER（Docker Hub 用户名）}"
TAG_LOCAL="loong64"
TAG_RELEASE="${RELEASE:-24.10-la5}"   # 与 GitHub Release 对齐，可覆盖

IMAGES=(
  adguardhome
  alertmanager
  audiobookshelf
  bazarr
  caddy
  calibre-web
  changedetection
  code-server
  dashy
  dpanel
  dozzle
  drawio
  easytier
  excalidraw
  filebrowser
  firefly-iii
  freshrss
  gatus
  gitea
  gogs
  gotify
  grafana
  heimdall
  homarr
  homeassistant
  homer
  it-tools
  jackett
  jellyfin
  jellyseerr
  jellystat
  kodexplorer
  kopia
  linkding
  mariadb
  memcached
  memos
  mihomo
  miniflux
  mosquitto
  navidrome
  nextcloud
  nginx-proxy-manager
  node-exporter
  node-red
  ntfy
  one-api
  openwebui
  paperless-ngx
  phpmyadmin
  pihole
  portainer
  postgres
  prometheus
  prowlarr
  qbittorrent-ee
  radarr
  redis
  shiori
  sonarr
  stirling-pdf
  syncthing
  tautulli
  typecho
  uptimekuma
  vaultwarden
  wallabag
  watchtower
  wizarr
  xteve
)

for img in "${IMAGES[@]}"; do
  src="${img}:${TAG_LOCAL}"
  if ! docker image inspect "$src" >/dev/null 2>&1; then
    echo "SKIP  $src 不存在"
    continue
  fi
  docker tag "$src" "${DOCKER_USER}/${img}:${TAG_LOCAL}"
  docker tag "$src" "${DOCKER_USER}/${img}:${TAG_RELEASE}"
  docker push "${DOCKER_USER}/${img}:${TAG_LOCAL}"
  docker push "${DOCKER_USER}/${img}:${TAG_RELEASE}"
  echo "OK    ${DOCKER_USER}/${img}:{${TAG_LOCAL},${TAG_RELEASE}}"
done

# istore 全系统镜像（可选，体积 847MB；私人预置版不建议公开推送）
# docker tag istore:personal-new "${DOCKER_USER}/istore:${TAG_RELEASE}"
# docker push "${DOCKER_USER}/istore:${TAG_RELEASE}"
