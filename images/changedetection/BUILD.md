# changedetection (loong64) 构建记录

## 结论

- 镜像：`yunixintel/changedetection:loong64` / `:24.10-la5`
- 大小：3.51GB，架构 `linux/loong64`
- 验证：HTTP 200；Firefox 截图落盘；`image_ssim_diff` baseline/二次比对通过；Selenium 4 步表单（输入/点击）执行成功
- 说明：0.60.9；SQLite；内置 Firefox 140.11ESR + geckodriver 0.37.1；Selenium 步骤适配层支持 Goto/点击/输入/等待/选择/按键/滚动/JS/复选框等（不再依赖 Playwright）；OpenCV 4.5.2 + numpy 1.26.4，SSIM 可用；Chrome 远程仍可 `WEBDRIVER_BROWSER=chrome` + `WEBDRIVER_URL`；5000

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t changedetection:loong64 .
docker tag changedetection:loong64 yunixintel/changedetection:loong64
docker tag changedetection:loong64 yunixintel/changedetection:24.10-la5
docker push yunixintel/changedetection:loong64
docker push yunixintel/changedetection:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`5000`
- 卷：`["/datastore"]`
- 默认环境：`LANG=C.UTF-8 \`
- 启动：`["/opt/venv/bin/python", "./changedetection.py", "-d", "/datastore"]`

Dockerfile 的上下文依赖：

- `COPY wheels /wheels`
- `COPY geckodriver /usr/bin/geckodriver`
- `COPY requirements.txt /tmp/requirements.txt`
- `COPY . /app`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`5000`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

0.60.9；SQLite；内置 Firefox 140.11ESR + geckodriver 0.37.1；Selenium 步骤适配层支持 Goto/点击/输入/等待/选择/按键/滚动/JS/复选框等（不再依赖 Playwright）；OpenCV 4.5.2 + numpy 1.26.4，SSIM 可用；Chrome 远程仍可 `WEBDRIVER_BROWSER=chrome` + `WEBDRIVER_URL`；5000

## 验证

```bash
docker inspect yunixintel/changedetection:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/changedetection:loong64 --help 2>/dev/null || true
```
