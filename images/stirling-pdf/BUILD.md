# stirling-pdf (loong64) 构建记录

## 结论

- 镜像：`yunixintel/stirling-pdf:loong64` / `:24.10-la5`
- 大小：1.17GB，架构 `linux/loong64`
- 验证：200
- 说明：v3.2.0；官方 jar + Java 25；精简版未装 LibreOffice/OCR，相关端点自动禁用；8080

## 构建

构建入口：[Dockerfile](Dockerfile)

```bash
docker build -t stirling-pdf:loong64 .
docker tag stirling-pdf:loong64 yunixintel/stirling-pdf:loong64
docker tag stirling-pdf:loong64 yunixintel/stirling-pdf:24.10-la5
docker push yunixintel/stirling-pdf:loong64
docker push yunixintel/stirling-pdf:24.10-la5
```

- 基础镜像：`openeuler/openeuler:24.03`
- 暴露端口：`8080`
- 卷：`["/configs"]`
- 默认环境：`JDK_JAVA_OPTIONS="--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED"     HOME=/app     STIRLING_TEMPFILES_DIRECTORY=/tmp/stirling-pdf     TMPDIR=/tmp/stirling-pdf`
- 启动：`["java","-XX:+ExitOnOutOfMemoryError","-Djava.awt.headless=true","-jar","/app/Stirling-PDF.jar"]`

Dockerfile 的上下文依赖：

- `COPY Stirling-PDF.jar /app/Stirling-PDF.jar`

上游版本、工具链和特殊补丁见 [../IMAGE-BUILD.md](../../docs/IMAGE-BUILD.md) 与 [../BUILDLOG.md](../../docs/BUILDLOG.md)。

## 运行

端口/挂载：`8080`；详细启动参数见 [RUNBOOK.md](../../docs/RUNBOOK.md) 的端口索引。

## 注意

v3.2.0；官方 jar + Java 25；精简版未装 LibreOffice/OCR，相关端点自动禁用；8080

## 验证

```bash
docker inspect yunixintel/stirling-pdf:loong64 --format "{{.Architecture}} {{.Os}}"
docker run --rm yunixintel/stirling-pdf:loong64 --help 2>/dev/null || true
```
