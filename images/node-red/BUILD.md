# Node-RED 4.1.16 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/node-red:loong64` / `:24.10-la5`
- 大小：439MB，`linux/loong64`
- digest：`sha256:0c548174a78f25579ec169180cf6de476d146a5a079d4dc8003ca186b0c89bf8`
- 版本：Node-RED 4.1.16 / Node.js 20.18.2（openEuler 24.03 SP4）
- 验证：`/` 200、标题 `Node-RED`、`node-red --version` 正常、`/data` 首次生成
  `settings.js`/`flows.json`、容器重启后仍 200、健康检查 healthy。

## 为什么用 Node-RED 4.x

Node-RED 5.x 要求 Node.js ≥22.9，而 openEuler 24.03 只提供 Node.js 20.18。
4.1.16 是 v4 维护线的最新版，要求 Node ≥18，功能完整，因此选择 4.x 并在文档中
明确版本边界。需要 5.x 时得先自行提供 loong64 Node 22 运行时。

## 构建

```bash
docker build -t node-red:loong64 .
docker tag node-red:loong64 yunixintel/node-red:loong64
docker tag node-red:loong64 yunixintel/node-red:24.10-la5
docker push yunixintel/node-red:loong64
docker push yunixintel/node-red:24.10-la5
```

多阶段构建：

- `build` 阶段安装 `nodejs npm gcc-c++ make python3`，执行
  `npm install -g --unsafe-perm --omit=dev node-red@4.1.16`，把编译工具留在构建层。
- 运行阶段只保留 `nodejs npm shadow util-linux ca-certificates tzdata curl`，
  从构建阶段复制 `/usr/local/lib/node_modules/node-red`。
- 保留 `npm` 是为了让 Node-RED 编辑器的 palette manager 能继续安装节点。

## 运行

```bash
docker run -d --name node-red -p 1880:1880 \
  -v node-red-data:/data yunixintel/node-red:loong64
```

- 编辑器：`http://<host>:1880/`；数据目录 `/data`。
- 容器以 UID/GID 1001（`nodered`）运行，命名卷自动继承属主；挂宿主目录需
  `chown -R 1001:1001 <dir>`。
- 首次启动会把包内 `settings.js` 复制到 `/data/settings.js`，之后以它为准；
  修改 `uiPort`、`credentialSecret`、`contextStorage` 等都在该文件。
- 默认 `uiPort` 读取 `PORT` 环境变量，未设置时是 1880。映射其他端口时同时设
  `PORT` 或改 settings.js，否则编辑器仍监听 1880。
- `flows.json`、`flows_cred.json`、`.config.*` 都在 `/data`，备份整个目录即可。

## 注意

- 首次启动日志会提示“credentials 使用系统生成密钥”；生产应在
  `/data/settings.js` 设置固定的 `credentialSecret`。
- Projects 默认关闭（`editorTheme.projects.enabled=false`），需要 Git 集成时自行打开。
- 安装带原生依赖的 palette 节点时，运行镜像没有 gcc/make；应选择纯 JS 节点，
  或基于本 Dockerfile 的 build 阶段自建带编译器的变体。
- Node-RED 4.x 不是最新大版本；升级 5.x 必须先解决 Node 22 loong64 运行时。

## 验证命令

```bash
curl -fsS http://127.0.0.1:1880/ | grep -o '<title>[^<]*'
docker exec node-red runuser -u nodered -- node-red --version
docker exec node-red ls -la /data
docker restart node-red
```
