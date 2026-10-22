# MyMind (loong64) 构建记录

## 结论

- 镜像：`yunixintel/mymind:loong64` / `:24.10-la5`
- Hub 压缩大小：约 130MB
- digest：`sha256:0db902f4ca37d08b51fad9e1de96c1c2bfb78cfbad226291e080bfca3043d5d6`
- 版本：iStore `luci-app-mymind` 内置的 `ondras/my-mind` 静态快照
- 验证：`/` 200、`editor.html` 200、`my-mind.js`、图标、Pell 编辑器资源均 200，
  健康检查 healthy

## 构建链路

MyMind 是纯前端思维导图编辑器，无后端、无数据库：

1. 直接使用 iStore 应用包中的静态站点
   (`luci-app-mymind/root/www/luci-static/mymind/`)，共 32 个文件、约 570KB。
2. 运行阶段基于 `openeuler/openeuler:24.03`，安装 `nginx`，
   站点复制到 `/usr/share/nginx/html`。
3. 使用自定义 `nginx.conf`：监听 80、`try_files` 回退到 `index.html`、
   静态资源缓存、日志走 stdout/stderr。
4. 以 nginx 默认用户运行 worker，容器内不跑 systemd。

## 说明

- 这是**单用户本地工具**：导图数据保存在浏览器 LocalStorage/文件导出中，
  服务端不保存任何内容。
- 不需要挂载卷；升级镜像不会影响用户的浏览器数据。
- 若需要多人共享，需要自行加反向代理认证；应用本身没有账号体系。
- 因为完全是静态文件，镜像与 CPU 架构无关，但仍按仓库规范只发布 loong64。

## 运行

```bash
docker run -d --name mymind -p 8080:80 yunixintel/mymind:loong64
```

浏览器打开 `http://<host>:8080/`，或直接访问 `/editor.html`。
