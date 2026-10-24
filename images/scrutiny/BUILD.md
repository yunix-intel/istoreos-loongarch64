# Scrutiny 0.9.5 + SQLite 补丁（loong64）

## 结论

- 镜像：`yunixintel/scrutiny:loong64` / `:24.10-la5`
- 大小：约 242MB（Hub 压缩 145MB）
- digest：`sha256:72885303da5ea5943f5885af60ba4452c52a213a058f829a73d1fb7ca8e2db71`
- 版本：Scrutiny 0.9.5 + SQLite metrics 补丁
- 验证（原生 loong64，A 机）：
  - `/web/` 200、`/api/health` `{"success":true}`、健康检查 healthy
  - collector 扫描 `/dev/nvme0`，读到 `ZHITAI PC005 256GB`、温度 43°C、通电 347h
  - `/api/summary` 返回设备与 SMART 摘要
  - x86_64 侧已跑通真实 SATA 盘、月/年历史聚合、设备删除和单元测试

## 为什么需要补丁

Scrutiny 0.8/0.9 的 Web 端启动时强制连接 InfluxDB 2.x。InfluxDB 2.8 在 loong64 上：

- `bbolt v1.3.6` 缺 loongarch64 的 `maxMapSize`/`maxAllocSize`（v1.3.11 已加 `bolt_loong64.go`）；
- `flux v0.196.1` 无条件依赖 `libflux`（Rust/C），没有纯 Go 构建标签。

所以不走 InfluxDB，改 SQLite：

- Scrutiny 已经依赖 `glebarez/sqlite`（纯 Go、无 CGO）；
- 只改 4 个与 InfluxDB 交互的文件，新增 `smart_metrics`、`temp_metrics` 两张表；
- 按 `(scrutiny_uuid,date)` upsert，查询时做 10m/1h/24h 聚合；
- API/前端契约不变；设备删除同时清两张表。

补丁：`scrutiny-sqlite.patch`（sha256 `73380f81…d03c`）。  
构建脚本：`scrutiny-build.sh`（sha256 `cf2542e5…105b`）。

## 构建链路

1. `git clone --depth 1 -b v0.9.5 https://github.com/AnalogJ/scrutiny.git`
2. `git apply scrutiny-sqlite.patch`
3. 后端（CGO=0，纯 Go SQLite）：
   `go build -trimpath -ldflags "-s -w"` 编 `webapp/backend/cmd/scrutiny` 与
   `collector/cmd/collector-metrics`。
4. 前端：Node 20，`npm ci`，`ng build --configuration production`；产物在 `dist/`。
5. 运行阶段 openEuler 24.03 + `smartmontools libstdc++ libgcc curl tzdata`。
   **必须带 `libstdc++`/`libgcc_s`**，否则 smartctl 报 exit 127。
6. 二进制 `/opt/scrutiny/bin`，前端 `/opt/scrutiny/web`，数据 `/opt/scrutiny/config`。

## 运行

```bash
docker run -d --name scrutiny -p 8080:8080 \
  --cap-add SYS_RAWIO --cap-add SYS_ADMIN \
  -v /run/udev:/run/udev:ro \
  --device /dev/nvme0:/dev/nvme0 \
  --device /dev/nvme0n1:/dev/nvme0n1 \
  -v scrutiny-config:/opt/scrutiny/config \
  yunixintel/scrutiny:loong64
```

- Web：`http://<host>:8080/web/`；健康 `/api/health`。
- 采集一次：

```bash
docker exec scrutiny /opt/scrutiny/bin/scrutiny-collector-metrics run
```

- 定时采集用宿主 cron 或 `docker exec` 包装；镜像默认只跑 Web。
- SATA 盘把 `--device` 换成 `/dev/sdX`；NVMe 需要 `/dev/nvme0` 和 `/dev/nvme0n1`。
- 不建议 `-v /dev:/dev`；按盘逐个 `--device`。
- 数据 `/opt/scrutiny/config/scrutiny.db` 必须持久化。

## 限制

- 不迁移旧 InfluxDB 历史；已有设备元数据可迁移，旧指标留在 InfluxDB。
- 没有保留/降采样任务；`temp_metrics` 约每设备每分钟一行，查询时聚合。
- collector 调度是外部的；镜像不内置 cron。
- `web.influxdb.*` 配置键仍存在但被忽略。
- 若只需要 Prometheus 指标，`smartctl-exporter` 更轻量；Scrutiny 提供完整历史 UI。
