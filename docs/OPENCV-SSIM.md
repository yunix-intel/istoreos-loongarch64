# OpenCV / SSIM 能力（loong64）

当前使用方：`yunixintel/changedetection`（`image_ssim_diff` 处理器）。
其它 Python 应用如需 `cv2`，按同一配方即可，不需要为 OpenCV 单独做一套镜像。

## 配方（openEuler 24.03 + Python 3.11 venv）

```dockerfile
# 1) openEuler 的 opencv 4.5.2 包自带 cv2（python3.11 / loongarch64）
RUN dnf install -y --setopt=install_weak_deps=False opencv && \
    dnf clean all && rm -rf /var/cache/dnf

# 2) cv2 4.5.2 是 numpy 1.x ABI；numpy 2.x 会报
#    "numpy.core.multiarray failed to import"
RUN /opt/venv/bin/pip install --no-cache-dir --prefer-binary \
        -i https://lpypi.loongnix.cn/loongson/pypi/+simple \
        --extra-index-url https://pypi.org/simple \
        --trusted-host lpypi.loongnix.cn \
        "numpy==1.26.4"

# 3) venv 默认看不到系统 site-packages，必须把 cv2 复制进去
RUN SP=$(/opt/venv/bin/python -c "import site; print(site.getsitepackages()[0])") && \
    cp -a /usr/lib/python3.11/site-packages/cv2 "$SP/"
```

changedetection 还需要启用默认关闭的 SSIM 处理器：

```dockerfile
ENV DISABLED_PROCESSORS=""
```

## 验证

```bash
/opt/venv/bin/python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
# 4.5.2 1.26.4
```

changedetection 中：

- 处理器列表应包含 `Visual / Image screenshot change detection`
- 首次检查保存 baseline 截图
- 第二次截图未变时日志出现 `Screenshot MD5 unchanged ... skipping comparison`
- 如出现 `numpy.core.multiarray failed to import`，说明 numpy 被升到了 2.x

## 注意

- 这套 cv2 是 4.5.2，功能足够做截图缩放/差分；不要期望最新 OpenCV 特性。
- 若应用同时依赖 scipy/scikit-learn，先用 numpy 1.26.4 做导入验证；changedetection 当前不依赖 scipy。
- `image_ssim_diff` 在 changedetection API 的 OpenAPI enum 里没有暴露；用 UI 选择，或直接改 watch.json。
