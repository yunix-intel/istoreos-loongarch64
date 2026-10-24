# MediaMTX (loong64) 构建记录

## 结论

- 镜像：`yunixintel/mediamtx:loong64` / `:24.10-la5`
- 大小：约 108MB（Hub 压缩；本地 313MB）
- digest：`sha256:20d0edcb144a043ef8b52fbdeb82a770dae8053cd6ac30c1e97f59d23f7c26bb`
- 版本：MediaMTX `1.9.3`（commit `6cd7487`）
- 验证：
  - RTSP 发布 `ffmpeg testsrc` → 路径 `test` ready，H264
  - HLS `/test/index.m3u8` 200（含 `video1_stream.m3u8`）
  - WebRTC 页面 `/test/` 200；API `/v3/paths/list` 容器内 200
  - Docker health `healthy`

## 构建链路

1. Go 1.27.2，`CGO_ENABLED=0`，单二进制约 22MB。
2. 构建前需要两个被 gitignore 的生成文件：
   - `internal/core/VERSION`：直接写 `1.9.3`（shallow clone 下 versiongetter 不可靠）；
   - `internal/servers/hls/hls.min.js`：`go generate ./internal/servers/hls`
     下载 hls.js 1.5.17 release.zip 并校验 SHA256。
3. 运行阶段 openEuler + `ca-certificates tzdata curl bash shadow util-linux`；
   非 root 用户 `mediamtx` UID/GID 1115。
4. `mediamtx.yml` 取自上游 v1.9.3，唯一改动：`api: yes`（上游默认 `no`）。

## 运行时契约

- 端口：
  | 端口 | 用途 |
  |---|---|
  | 8554/tcp | RTSP |
  | 8000-8001/udp | RTSP RTP/RTCP（UDP 传输时需要） |
  | 1935/tcp | RTMP |
  | 8888/tcp | HLS |
  | 8889/tcp | WebRTC HTTP |
  | 8189/udp | WebRTC ICE |
  | 8890/udp | SRT |
  | 9997/tcp | API |
- 无持久化卷；配置在镜像内 `/mediamtx.yml`，需要定制时挂载覆盖并改 entrypoint 参数。
- 默认 `authInternalUsers` 只允许 `127.0.0.1`/`::1` 访问 API；从宿主机映射端口访问会得到 401，
  需要 API 时在配置中加用户或允许网段。
- WebRTC 在 NAT 后需要设置 `webrtcAdditionalHosts` 或 `webrtcICEServers`，否则只能局域网。
- `runOnInit` 等路径级命令等于容器内命令执行，启用前必须确认来源可信。

## 遇到的问题

- **生成文件缺失**：直接 `go build` 报 `pattern VERSION / hls.min.js: no matching files found`；
  必须先写 VERSION 并跑 `go generate`。
- **API 默认关闭**：1.9.3 的 `mediamtx.yml` 是 `api: no`，不打开时 9997 不监听；
  镜像默认改为 `api: yes`。
- **健康检查来源**：端口映射后 API 请求源地址是 Docker 网关，不在默认白名单，返回 401；
  健康检查在容器内访问 127.0.0.1，正常 200。
- **shallow clone 无 tag**：versiongetter 拿不到 `v1.9.3`，手工写 VERSION 文件。

## 限制

- 未验证 RTMP/SRT 推流与 WebRTC 跨 NAT 播放。
- 与 go2rtc 功能重叠；二选一部署。
- 未启用 metrics/pprof（默认关闭）。

## 运行

```bash
docker run -d --name mediamtx \
  -p 8554:8554 -p 1935:1935 -p 8888:8888 -p 8889:8889 \
  -p 8189:8189/udp -p 8890:8890/udp -p 9997:9997 \
  yunixintel/mediamtx:loong64
```

推流示例：`ffmpeg -re -i input.mp4 -c copy -f rtsp rtsp://<host>:8554/live`；
播放：`http://<host>:8888/live/`（HLS）、`http://<host>:8889/live/`（WebRTC）。
