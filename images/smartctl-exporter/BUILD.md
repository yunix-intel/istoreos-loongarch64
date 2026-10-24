# smartctl_exporter v0.15.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/smartctl-exporter:loong64` / `:24.10-la5`
- 大小：约 123MB（Hub 压缩）
- digest：`sha256:be3f0b58aca96fa08e1907137b9dc460058f23c69299c39ab7a3019c9ff5fbda`
- 版本：prometheus-community/smartctl_exporter v0.15.0
- 验证：`/metrics` 200；NVMe `/dev/nvme0` 的型号、固件、序列号和 SMART 指标可读；健康检查 healthy

## 为什么不是 Scrutiny

Scrutiny 0.8/0.9 的 Web 端在启动时强制连接 InfluxDB 2.x（`InfluxSetupComplete`），
SQLite 只存设备元数据，SMART 历史在 InfluxDB。InfluxDB 2.8 在 loong64 上又卡在：

- `go.etcd.io/bbolt v1.3.6` 的 `maxMapSize`/`maxAllocSize` 没有 loongarch64 定义；
- `github.com/influxdata/flux` 的 `libflux` C/Rust 库未构建。

把 Scrutiny 改成纯 SQLite 涉及 28 个接口方法、166 处 Influx 引用，不适合 P1 阶段。
因此改用 `smartctl_exporter`：它只暴露 Prometheus 指标，直接接现有的
Prometheus + Grafana，不引入 InfluxDB。

## 构建链路

1. `git clone --depth=1 --branch v0.15.0`。
2. Go 1.27.2，`CGO_ENABLED=0 go build -o smartctl_exporter .`。
3. 运行阶段基于 `openeuler/openeuler:24.03`，安装
   `smartmontools curl tzdata procps-ng`。
4. 入口只做 `exec smartctl_exporter --smartctl.path=/usr/sbin/smartctl "$@"`。

## 运行

```bash
docker run -d --name smartctl-exporter -p 9633:9633 \
  --cap-add SYS_RAWIO --cap-add SYS_ADMIN \
  -v /run/udev:/run/udev:ro \
  --device /dev/nvme0:/dev/nvme0 \
  --device /dev/nvme0n1:/dev/nvme0n1 \
  yunixintel/smartctl-exporter:loong64 \
  --smartctl.device=/dev/nvme0
```

- 指标：`http://<host>:9633/metrics`。
- SATA 盘把 `--smartctl.device` 换成 `/dev/sdX`；多盘重复该参数。
- 需要 `SYS_RAWIO`，NVMe 还建议 `SYS_ADMIN` 与 `/run/udev` 只读挂载。
- 不建议 `-v /dev:/dev`；按盘逐个 `--device`。
- 镜像以 root 运行以便 smartctl 执行 ioctl；容器内无 shell 服务，只暴露只读指标。
- Prometheus 抓取示例：

```yaml
scrape_configs:
  - job_name: smartctl
    static_configs:
      - targets: ["192.168.8.8:9633"]
```

- 该镜像不保存历史数据；历史由 Prometheus 保存，图表用现有 Grafana。
- 若只需要一次性 SMART 检查，仍可直接 `docker exec` 或宿主 `smartctl`。
