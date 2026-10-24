# go2rtc 1.9.14 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/go2rtc:loong64` / `:24.10-la5`
- 大小：约 111MB（Hub 压缩）
- digest：`sha256:03aa04222ebfcab4fb17d72073f69973ee6945157f831b2df592351ffe353def`
- 版本：go2rtc 1.9.14（commit `b5948cf`）
- 验证：API `/` 200、`/api/streams` 返回 `{}`、RTSP 8554/WebRTC 8555 监听、健康检查 healthy
- 未配置真实摄像头流；播放/转码未测

## 构建链路

1. `AlexxIT/go2rtc` v1.9.14。
2. Go 1.27.2，`CGO_ENABLED=0 go build -trimpath -ldflags "-s -w"`。
3. 运行阶段 openEuler + `curl tzdata shadow util-linux procps-ng`；
   二进制 `/usr/local/bin/go2rtc`，配置 `/config/go2rtc.yaml`。
4. 运行用户 `go2rtc` UID/GID 1109，端口 1984/8554/8555。

## 运行

```bash
docker run -d --name go2rtc \
  -p 1984:1984 -p 8554:8554 -p 8555:8555 \
  -v go2rtc-config:/config \
  yunixintel/go2rtc:loong64
```

- Web/API：`http://<host>:1984/`。
- RTSP 服务：`rtsp://<host>:8554/<stream>`。
- WebRTC：8555/tcp+udp；跨 NAT 时需在 `go2rtc.yaml` 配 `webrtc.candidates` 或反代。
- 默认 `go2rtc.yaml` 只开端口，不含摄像头地址；流配置由用户添加。
- API 默认无认证；公网必须加反代认证或 `api.username/password`。
- 不需要 ffmpeg 即可做 RTSP/WebRTC 转发；转码/硬件加速另配。
