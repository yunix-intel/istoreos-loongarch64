# Mealie 3.29.0 (loong64) 构建记录

## 结论

- 镜像：`yunixintel/mealie:loong64` / `:24.10-la5`
- 大小：2.17GB，`linux/loong64`
- digest：`sha256:807d90256bb64cf52103323e9c88199c9f215a0979002d8b5e0ada3e2ed6e673`
- 版本：Mealie 3.29.0 / Python 3.14.8 / Nuxt 3 静态前端
- 验证：`/` 200、`/api/app/about` 返回 version 3.29.0、SQLite 数据目录初始化、
  健康检查 healthy。

## 构建链路

Mealie 3.29.0 要求 Python `>=3.14,<3.15`，openEuler 24.03 只有 3.11，因此分三步：

### 1. Python 3.14.8（loong64 源码）

使用 `Python-3.14.8.tgz` 在 openEuler 容器内：

```bash
./configure --prefix=/usr/local --with-ensurepip=install \
  --enable-loadable-sqlite-extensions
make -j8 && make install
```

构建依赖包含 `libffi-devel openssl-devel readline-devel sqlite-devel xz-devel
zlib-devel ncurses-devel libuuid-devel gdbm-devel libpq-devel libwebp-devel
openldap-devel cyrus-sasl-devel ffmpeg`。

### 2. 前端（x86_64 WSL2）

```bash
export PATH=$HOME/node22/bin:$PATH
npm install -g pnpm@11.23.0
cd frontend
pnpm install --frozen-lockfile
pnpm generate
```

产物在 `frontend/.output/public`，拷到源码的 `mealie/frontend/`，供 Python 包
`include-package-data` 打包进 wheel。前端约 13MB（含 527 个 PWA 预缓存文件）。

### 3. Python 包与原生依赖

```bash
python3 -m pip install /mealie-src
```

需要额外工具链：

- **Rust 1.99.1**：`orjson`、`pydantic-core`、`curl-cffi` 从源码编译。
- `cmake`：`pycares`、`numpy` 的构建后端。
- `autoconf automake libtool patch`：`numpy` 构建依赖的 `patchelf` 需要
  `autoreconf`。
- `libxml2-devel libxslt-devel`：`lxml`。
- `libcurl-devel`：`curl-cffi`。

上游源码的 `mealie/__init__.py` 在 git checkout 里是 `__version__ = "develop"`；
本镜像改为 `3.29.0`，UI/API 版本串才正确。

## HEIF 限制

Mealie 依赖 `pillow-heif==1.8.1`，但 openEuler 24.03（含 EPOL）没有 `libheif-devel`，
loong64 也没有 PyPI 预编译 wheel。本镜像安装了一个最小 `pillow-heif` 占位包：

```python
def register_heif_opener(*args, **kwargs):
    return None
```

因此 **HEIC/HEIF 图片不会注册到 Pillow，相关图片可能无法处理**；JPEG/PNG/WebP 正常。
这是当前 loong64 的已知功能缺口，已在镜像说明和 catalog 标注。

## 运行

```bash
docker run -d --name mealie -p 9000:9000 \
  -v mealie-data:/app/data yunixintel/mealie:loong64
```

- Web UI：`http://<host>:9000/`。
- 健康检查：`/api/app/about`。
- 数据目录 `/app/data`（SQLite、recipes、users、backups、日志）；挂宿主目录需
  `chown -R 911:911`。
- 容器以 UID 911（`abc`）运行。
- 默认环境：
  - `PRODUCTION=true`
  - `DATA_DIR=/app/data`
  - `MEALIE_HOME=/app`
  - `TZ=Etc/UTC`

## 注意

- 镜像较大（2.17GB），主要来自 Python 3.14 + 全部原生依赖 + ffmpeg。
- 无内置 TLS；公网必须放在 Caddy/Nginx 反向代理后。
- 首次访问完成管理员/家庭组初始化；`allowSignup` 默认为 false。
- 备份整个 `/app/data`，不要只备份 `mealie.db`（recipes/users/backups 也在里面）。
- SQLite 单实例，不适合多副本同时写 `/app/data`。
- **HEIF/HEIC 不支持**（见上），需要该功能时必须先为 loong64 构建 libheif/pillow-heif。

## 验证命令

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9000/
curl -fsS http://127.0.0.1:9000/api/app/about
docker exec mealie ls -la /app/data
docker exec mealie /usr/local/bin/python3 -c 'import mealie; print(mealie.__version__)'
docker restart mealie
```
