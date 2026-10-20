FROM openeuler/openeuler:24.03

RUN dnf install -y java-25-openjdk-headless findutils shadow-utils  && dnf clean all && rm -rf /var/cache/dnf

RUN groupadd -r stirling && useradd -r -g stirling -d /app -s /sbin/nologin stirling

WORKDIR /app
COPY Stirling-PDF.jar /app/Stirling-PDF.jar

RUN mkdir -p /configs /logs /customFiles /pipeline /storage /tmp/stirling-pdf  && ln -s /configs /app/configs  && ln -s /logs /app/logs  && ln -s /customFiles /app/customFiles  && ln -s /pipeline /app/pipeline  && ln -s /storage /app/storage  && chown -R stirling:stirling /app /configs /logs /customFiles /pipeline /storage /tmp/stirling-pdf

ENV JDK_JAVA_OPTIONS="--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED"     HOME=/app     STIRLING_TEMPFILES_DIRECTORY=/tmp/stirling-pdf     TMPDIR=/tmp/stirling-pdf

USER stirling
EXPOSE 8080
STOPSIGNAL SIGTERM
ENTRYPOINT ["java","-XX:+ExitOnOutOfMemoryError","-Djava.awt.headless=true","-jar","/app/Stirling-PDF.jar"]

VOLUME ["/configs"]
