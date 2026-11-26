FROM eclipse-temurin:21-jdk-alpine
RUN adduser -D -u 1000 judge
COPY src /runner/src
RUN mkdir -p /runner/classes \
 && javac -d /runner/classes $(find /runner/src -name '*.java')
USER judge
WORKDIR /tmp
ENTRYPOINT ["java", "-XX:-UsePerfData", "-XX:+UseSerialGC", "-Xshare:auto", "-cp", "/runner/classes", "designdojo.runner.Runner"]
