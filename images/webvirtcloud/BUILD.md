# WebVirtCloud (loong64) 构建记录

## 结论

- 镜像：`yunixintel/webvirtcloud:loong64` / `:24.10-la5`
- Hub 压缩大小：约 235MB
- digest：`sha256:263e7da54351dbae5e5998924d9ae9789e6ace2aab978205cfb8e2756b8419ab`
- 版本：WebVirtCloud master 快照（Django 4.2 LTS / Python 3.11）
- 验证：登录页 200、静态 CSS/JS 200、数据库迁移完成、novncd/gunicorn/nginx
  三进程运行、健康检查 healthy

## 构建链路

上游镜像基于 `phusion/baseimage` + runit，LoongArch64 没有对应基础镜像，
因此保留应用目录结构，改用普通 shell supervisor：

1. 运行阶段基于 `openeuler/openeuler:24.03`，安装
   `nginx libvirt-client libvirt-libs openldap cyrus-sasl-lib libffi
   libxml2 libxslt openssl-libs`。
2. 在构建容器内用 `python3 -m venv --system-site-packages` 建 venv，
   `pip install -r conf/requirements.txt`。
3. `collectstatic` 用临时 dummy `SECRET_KEY` 执行，完成后删除临时
   `settings.py`。
4. 镜像内复制 `/srv/webvirtcloud`（含 venv 与 `static/`），
   创建 UID/GID 33 的 `www-data`。
5. entrypoint 依次：
   - 从 `settings.py.template` 生成 `settings.py`；
   - 生成/读取持久化 `SECRET_KEY`；
   - 把 SQLite 放到 `/srv/webvirtcloud/data` 并软链；
   - 执行 `manage.py migrate`；
   - 启动 gunicorn（127.0.0.1:8000）、`console/novncd`（6080/6081）、nginx（80）。

## 遇到的问题

- **bcrypt 无 loong64 wheel**：pip 回退源码编译，需要 Rust。
  构建容器安装 `rust cargo` 后通过。
- **cryptography/cffi 源码编译失败**：先装系统
  `python3-cryptography python3-cffi libffi-devel`，让 venv 复用。
- **numpy 被 websockify 拉起**：源码构建 CMake 卡在 `-j1`；
  安装系统 `python3-numpy` 后跳过。
- **GID 33 已存在**：openEuler 的 `tape` 组占用 33。
  用 `groupadd -o -g 33 www-data` 允许重复 GID，保持上游文件权限语义。
- **上游 runit 不存在**：自写 entrypoint，用 `wait -n` 管理三个子进程，
  收到 SIGTERM 时统一清理。
- **静态文件 404**：应用静态目录是 `/srv/webvirtcloud/static`，
  nginx 的 `location /static/` 必须配 `root /srv/webvirtcloud`，
  不是 `alias` 到别的路径。

## 运行

```bash
docker run -d --name webvirtcloud -p 8080:80 \
  -v webvirt-data:/srv/webvirtcloud/data \
  -v webvirt-ssh:/var/www/.ssh \
  yunixintel/webvirtcloud:loong64
```

- Web UI：`8080`。
- 首次启动会自动建管理员账号；登录后到设置里改密码。
- 数据卷 `/srv/webvirtcloud/data` 保存 SQLite 与 `secret_key`，必须持久化。
- `/var/www/.ssh` 保存连接 KVM 宿主用的密钥。
- 连接远程 KVM 主机需要在 Web UI 里填 libvirt 地址（`qemu+ssh://...`），
  并保证容器内 `libvirt-client` 能访问该地址。
- noVNC 控制台走 `/novncd/`、`/websockify`；反代时需允许 WebSocket 升级。
