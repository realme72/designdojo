FROM python:3.12-alpine
RUN adduser -D -u 1000 judge
COPY runner.py /runner/runner.py
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONHASHSEED=0
USER judge
WORKDIR /tmp
ENTRYPOINT ["python", "-I", "-B", "/runner/runner.py"]
