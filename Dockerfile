FROM python:3.12-slim
WORKDIR /app
COPY cyberops /app/cyberops
ENV PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
ENTRYPOINT ["python", "-m", "cyberops.swarms.simulate"]
