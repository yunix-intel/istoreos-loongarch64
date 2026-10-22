# Hermes (loong64) 构建记录

## 结论

- 镜像：`yunixintel/hermes:loong64` / `:24.10-la5`
- 大小：3.68GB（Hub 压缩约 1.23GB）
- digest：`sha256:b6661bf644e290bbd6d64e55cf4687a7e92ee32c55344f67400be84953e2cc75`
- 版本：Hermes agent + webui master（2026-10 快照）
- 验证：`/` 200、`/health` 200、网关与 WebUI 双进程运行、健康检查 healthy

## 构建链路

Hermes 的 `pyproject.toml` 把所有核心依赖都标成
`python_version >= '3.14'`。用 openEuler 自带的 Python 3.11 会得到空依赖集，
因此必须提供 Python 3.14：

1. 复用为 Mealie 构建的 Python 3.14.8 前缀（`/usr/local`），
   删除 `site-packages`、`test`、`idlelib`、`tkinter` 后复制进镜像。
   Python 的前缀由可执行文件位置推导，复制到 `/usr/local` 即可正常工作。
2. 重新 bootstrap pip（`get-pip.py`），因为剥离 `site-packages` 时把 pip 一起删了。
3. 安装 agent：`pip install --no-deps /opt/hermes-agent`；
   webui：`pip install -r /opt/hermes-webui/requirements.txt`。
4. 运行阶段基于 `openeuler/openeuler:24.03`，构建依赖包含
   `gcc gcc-c++ make rust cargo`、`openssl/libffi/zlib/bzip2/xz/sqlite/ncurses/
   readline/libxml2/libxslt/libjpeg/libtiff/freetype` 的 `-devel` 包。
5. entrypoint 同时启动：
   - `hermes gateway run`（UID 1000）
   - `python3 /opt/hermes-webui/server.py`（监听 8787）

## 遇到的问题

- **pip 依赖冲突**：Hermes 要 `Pillow==13.0.0`，`browser-harness` 精确要
  `pillow==12.3.0`，pip 报 `ResolutionImpossible`。解决：

  ```bash
  pip install --no-deps browser-harness==0.1.13 cryptography==50.0.1 "pynacl>=1.6,<1.7"
  pip install --no-deps /opt/hermes-agent
  python3 gen-requirements.py   # 从 metadata 生成顶层依赖，跳过冲突包
  pip install -r /tmp/hermes-reqs.txt
  ```

- **wheel 保护**：直接 `pip install /opt/hermes-agent` 报
  “Building wheels or sdists for hermes-agent is not supported”。
  必须 `HERMES_NIX_BUILD=1 pip install --no-deps`。
- **`pillow-heif` 编译失败**：需要 `libheif-devel`，openEuler 无此包。
  Hermes 对它是软依赖，跳过；HEIC/HEIF 图片不可用，JPEG/PNG/WebP 正常。
- **`packaging` 缺失**：剥离 site-packages 后 `importlib.metadata` 可用，
  但生成依赖的脚本需要 `packaging`，单独 `pip install packaging`。
- **基础镜像被 Docker 镜像清理误删**：`docker image prune -a` 会删掉未运行容器
  引用的基础镜像；重建前先用 `crane pull --platform linux/loong64` 恢复。

- **`computer_use` 工具日志 `unsupported architecture: loongarch64`**：
  这是 Hermes 的 cua-driver 安装器不认识 LoongArch，属于工具探测失败，
  不影响网关和 WebUI；控制台使用等功能不可用。
- **镜像较大（3.68GB）**：保留了 gcc/rust 工具链，便于运行期安装需要编译的
  skill/plugin；如需瘦身可改为多阶段构建。
- **WebUI 默认无密码**：绑定 `0.0.0.0` 时会警告。对外暴露前设置
  `HERMES_WEBUI_PASSWORD`，或在反向代理层加认证。

## 运行

```bash
docker run -d --name hermes -p 8787:8787 \
  -v hermes-data:/data/.hermes \
  -v hermes-workspace:/workspace \
  yunixintel/hermes:loong64
```

- WebUI：`http://<host>:8787/`，健康检查 `/health`。
- `/data/.hermes` 保存配置、会话、技能与网关状态；`/workspace` 是 agent 工作目录。
- 首次使用需要在 WebUI/配置里填模型 API key；镜像不内置任何凭据。
- 容器内同时跑网关与 WebUI；任一进程退出，entrypoint 会清理另一个。
- 该镜像**不包含** HEIC/HEIF 解码；需要时自行安装 `libheif` 并重编
  `pillow-heif`。
