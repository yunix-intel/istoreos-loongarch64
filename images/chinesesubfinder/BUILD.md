# ChineseSubFinder v0.55.2 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/chinesesubfinder:loong64` / `:24.10-la5`
- Hub 压缩大小：约 385MB（本地镜像 1.04GB）
- digest：`sha256:5b6367a36bde0b695c5244a654cf2c474e0b7cfe34e1423c7a628303aa8e809a`
- 版本：ChineseSubFinder v0.55.2，Lite 模式（`LITE_MODE=true`）
- 验证：UI `HTTP 200`、健康检查 healthy、`/config` 与 `/media` 可写

## 构建链路

1. 取 v0.55.2 源码与官方前端。
2. 前端是 Quasar SPA。在 x86_64 WSL2 的 Node 22 下执行
   `npm ci && npm run build`，把 `dist/spa` 放到 `frontend/dist/spa`
   （Go 后端用 `go:embed` 打包，产物本身与架构无关）。
3. 龙芯本机用 Go 编译：

   ```bash
   go mod tidy
   go build -ldflags "-s -w -X main.AppVersion=v0.55.2 -X main.LiteMode=true" \
     -o chinesesubfinder ./cmd/chinesesubfinder
   ```

4. 运行阶段基于 `openeuler/openeuler:24.03`，安装 `ffmpeg`、`curl`、
   `ca-certificates`、`tzdata`，创建 UID 1026 的 `csf` 用户。

## 遇到的问题

- **Go 工具链不在容器内**：构建容器没有 `go`，把宿主
  `/home/yunix/go/pkg/mod/golang.org/toolchain@...` 挂到 `/toolchain` 后使用。
- **`go.sum` 缺条目**：源码 tag 未带完整校验和，先 `go mod tidy`。
- **缺少 `frontend/dist/spa`**：上游仓库不提交前端产物，必须先在 x86 上构建；
  否则 `go:embed` 直接失败。
- **`go-webrtcvad` 不认识 LoongArch**：`arch.h` 只列了 x86/ARM/PPC。
  增加：

  ```c
  #elif defined(__loongarch__) || defined(__loongarch64__)
  #define WEBRTC_ARCH_64_BITS
  #define WEBRTC_ARCH_LITTLE_ENDIAN
  ```

- **启动时 `mkdir Logs: permission denied`**：程序按当前工作目录写 `Logs/`。
  镜像设置 `WORKDIR /config`，entrypoint 再 `cd /config` 后降权执行。

## 运行

```bash
docker run -d --name chinesesubfinder -p 19035:19035 \
  -v csf-config:/config -v /path/to/media:/media \
  yunixintel/chinesesubfinder:loong64
```

- `/config`：配置、数据库、日志。
- `/media`：需要扫描的影视目录。
- 首次启动后在 Web UI 配置字幕站点与媒体路径。
- 镜像内置 `ffmpeg`，用于字幕时间轴/视频信息处理。
- 默认 `TZ=Asia/Shanghai`、`LITE_MODE=true`。
