# Zigbee2MQTT 2.14.2 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/zigbee2mqtt:loong64` / `:24.10-la5`
- 大小：649MB（Hub 压缩约 217MB）
- digest：`sha256:8d9989969581666b711251d4b2ceee99bf8249c8c9e94ac314603e1d5f6039e2`
- 版本：Zigbee2MQTT 2.14.2（commit `2b485a98` tag）
- 验证：
  - onboarding UI `HTTP 200`，健康检查 healthy
  - `udevadm --version` = 255
  - `@serialport/bindings-cpp` 的 loong64 `bindings.node` 可加载
  - 容器内 `mqtt` 客户端连接 Mosquitto 成功（`MQTT OK`）
  - **无真实 Zigbee 协调器**，配对/设备识别未验证

## 构建链路

上游用 Alpine + Node，本仓库改成 glibc 的 Node 24 多阶段构建：

1. **build-base**：`yunixintel/node:24.22.1` + `make gcc gcc-c++ python3 findutils`，安装 `pnpm@11.26.0`。
2. **build**：`pnpm install --frozen-lockfile`，`pnpm run build`（`tsc && node index.js writehash`）。
3. **prod-deps**：`pnpm install --frozen-lockfile --prod --no-optional`，删除
   `@serialport/bindings-cpp/prebuilds`，再 `pnpm rebuild @serialport/bindings-cpp`，
   生成 loong64 `build/Release/bindings.node`。
4. **runtime**：`yunixintel/node:24.22.1` + `curl tzdata shadow util-linux systemd-udev`；
   复制 `dist`、生产 `node_modules`、`package.json`、`index.js`、示例配置。
5. 运行用户 `zigbee2mqtt` UID/GID 1101，数据 `/app/data`，端口 8080。

## 遇到的问题

- **`npm ci` 不可用**：上游只有 `pnpm-lock.yaml`（`packageManager: pnpm@11.26.0`），
  `npm ci` 会报 EUSAGE。必须用 pnpm。
- **缺 `udevadm`**：首次启动报
  `USB adapter discovery error (spawn udevadm ENOENT)`。运行阶段补
  `systemd-udev` 后解决。
- **serialport 预编译包**：上游 npm 包只带 x86/ARM 的 `prebuilds`，没有 loongarch64。
  必须删除 `prebuilds` 并 `pnpm rebuild`，否则运行期可能加载错架构的 `.node`。
- **UI 不需要单独构建**：`zigbee2mqtt-frontend` / `windfront` 是 npm 依赖，
  `pnpm run build` 只编 TypeScript，不需要 x86 前端构建。
- **无适配器时程序会退出**：上游行为是 adapter discovery 失败即退出；测试 UI 可用
  `Z2M_ONBOARD_FORCE_RUN=true` 进入 onboarding 页面。

## 运行

```bash
docker run -d --name zigbee2mqtt \
  -p 8080:8080 \
  --device /dev/ttyACM0:/dev/ttyACM0 \
  --group-add dialout \
  -e MQTT_SERVER=mqtt://mosquitto:1883 \
  -e MQTT_USER=zigbee2mqtt \
  -e MQTT_PASSWORD='change-me' \
  -v zigbee2mqtt-data:/app/data \
  yunixintel/zigbee2mqtt:loong64
```

- Web UI：`http://<host>:8080/`。
- 首次启动如果 `/app/data/configuration.yaml` 不存在，会从示例复制并进入 onboarding。
- `MQTT_SERVER` / `MQTT_USER` / `MQTT_PASSWORD` 是便利变量；也可以直接用
  `ZIGBEE2MQTT_CONFIG_MQTT_SERVER` 等上游环境变量。
- 协调器路径优先用 `/dev/serial/by-id/...`，避免 `/dev/ttyUSB*` 编号变化。
- 需要把 `dialout` 组映射到容器；不同宿主 GID 可能不同，可用 `--group-add $(getent group dialout | cut -d: -f3)`。
- 无协调器时容器会退出，这是上游预期行为；不是镜像故障。
- 该镜像不包含任何设备配置、网络密钥或 MQTT 凭据。
