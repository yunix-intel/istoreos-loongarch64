# Node-RED 5.0.8 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/node-red:loong64` / `:24.10-la5`
- 大小：498MB，`linux/loong64`
- digest：`sha256:6ccc5ada9277aee4eae1cf4a66c504012e227311fd3bda0d3b536661231a6f11`
- 版本：Node-RED 5.0.8 / Node.js 22.23.3
- 验证：`/` 200、标题 `Node-RED`、`node-red --version` 5.0.8、`/data` 首次生成
  `settings.js`/`flows.json`、容器重启后仍 200、健康检查 healthy。

## Node 22 运行时

openEuler 24.03 仓库只有 Node 20，因此先用 unofficial-builds 的
`node-v22.23.3-linux-loong64.tar.xz` 构建基础镜像 `yunixintel/node:22.23.3`
（见 [../node/BUILD.md](../node/BUILD.md)）。

Node 22 的 npm 全局前缀是 `/opt/node22`，不是 `/usr/local`：

```text
npm root -g   -> /opt/node22/lib/node_modules
npm prefix -g -> /opt/node22
```

## 构建

```bash
docker build -t node-red:loong64 .
docker tag node-red:loong64 yunixintel/node-red:loong64
docker tag node-red:loong64 yunixintel/node-red:24.10-la5
docker push yunixintel/node-red:loong64
docker push yunixintel/node-red:24.10-la5
```

多阶段构建：

- `build` 阶段 `FROM node:22.23.3-loong64`，执行
  `npm install -g --unsafe-perm --omit=dev node-red@5.0.8`。
- 运行阶段基于 openEuler，只复制 `/opt/node22/bin` 与 `/opt/node22/lib`
  （不带头文件和 share），再复制
  `/opt/node22/lib/node_modules/node-red`。
- 保留 npm 是为了让 Node-RED 编辑器的 palette manager 能继续安装节点。
- 运行阶段重新创建 CLI 符号链接：
  `ln -s ../lib/node_modules/node-red/red.js /opt/node22/bin/node-red`。

## 运行

```bash
docker run -d --name node-red -p 1880:1880 \
  -v node-red-data:/data yunixintel/node-red:loong64
```

- 编辑器：`http://<host>:1880/`；数据目录 `/data`。
- 容器以 UID/GID 1001（`nodered`）运行，命名卷自动继承属主；挂宿主目录需
  `chown -R 1001:1001 <dir>`。
- 首次启动会把
  `/opt/node22/lib/node_modules/node-red/settings.js` 复制到 `/data/settings.js`，
  之后以它为准；修改 `uiPort`、`credentialSecret`、`contextStorage` 等都在该文件。
- 默认 `uiPort` 读取 `PORT` 环境变量，未设置时是 1880。映射其他端口时同时设
  `PORT` 或改 settings.js，否则编辑器仍监听 1880。
- `flows.json`、`flows_cred.json`、`.config.*` 都在 `/data`，备份整个目录即可。

## 注意

- 首次启动日志会提示“credentials 使用系统生成密钥”；生产应在
  `/data/settings.js` 设置固定的 `credentialSecret`。
- Projects 默认关闭（`editorTheme.projects.enabled=false`），需要 Git 集成时自行打开。
- 安装带原生依赖的 palette 节点时，运行镜像没有 gcc/make；应选择纯 JS 节点，
  或基于本 Dockerfile 的 build 阶段自建带编译器的变体。
- Node-RED 5.x 要求 Node ≥22.9；本镜像使用 Node 22 LTS 线。

## 验证命令

```bash
curl -fsS http://127.0.0.1:1880/ | grep -o '<title>[^<]*'
docker exec node-red /opt/node22/bin/node-red --version
docker exec node-red ls -la /data
docker restart node-red
```
