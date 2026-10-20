# EasyTier / mihomo（loong64 容器与固件）

这两个网络组件在固件和容器里都有部署形态。**真实配置含组网 UUID、节点地址和代理节点，
只放在私有库/构建机本地，不提交公开仓库。**

## 1. 材料位置

- 私有库 `deploy/loong64-sidecar/`：
  - `docker-compose.yml`、`up.sh`、`down.sh`
  - `mihomo/Dockerfile`、`easytier/Dockerfile`（scratch 三行）
  - `config.yaml.example`、`network.toml.example`（真值不入库）
- 公开固件：`feeds-pkg/easytier/`（OpenWrt 服务脚本与 init）
- 二进制/GeoIP 数据不入 git：mihomo、easytier 从上游 loong64 release 取，
  GeoIP 从 MetaCubeX/meta-rules-dat 取。

## 2. 容器形态

```bash
# 在私有库 deploy/loong64-sidecar 下
cp config.yaml.example config.yaml
cp network.toml.example network.toml
# 填入自己的节点/组网信息后：
./up.sh
```

mihomo：

```bash
docker run -d --name mihomo --network=host --privileged \
  -v /srv/mihomo:/etc/mihomo \
  yunixintel/mihomo:loong64 -d /etc/mihomo
```

easytier：

```bash
docker run -d --name easytier --network=host --privileged \
  -v /srv/easytier/network.toml:/etc/easytier/network.toml:ro \
  yunixintel/easytier:loong64 --config-file /etc/easytier/network.toml
```

配置中的 `instance_id` 必须是合法 UUID；早期用过的短 ID 会导致启动失败。
私人组网使用独立网段，具体地址只保存在私有库/构建机，不写入公开文档。

## 3. 固件形态

la5/p1 固件内置 EasyTier/OpenClash 相关 feed 包；EasyTier 的 init/conf 模板在
`feeds-pkg/easytier/files/`，首次启动后在 LuCI 中填节点信息。
OpenClash 使用 `RULE-SET cn-ip` 而不是 `GEOIP,CN`，避免缺 GeoIP 数据时规则不生效。

## 4. 已知限制 / 验证结论

- **mihomo 在 LoongArch 上拒绝加载 mmdb**：公开镜像只带二进制，不带 GeoIP；
  私人配置走 `RULE-SET` 规则绕过。需要 mmdb 的场景要单独验证数据文件兼容性。
- 三种形态（固件直装、sidecar 单容器、全系统镜像）已做过延迟/吞吐/稳定性对比；
  结论见 [BUILDLOG.md](BUILDLOG.md) 中 “三形态性能对比”。
- EasyTier sidecar 与全系统镜像都做过稳定性测试；节点地址/密钥不入公开文档。
- 容器用 `--network=host`，否则组网/透明代理的广播和 TUN 行为不完整。
