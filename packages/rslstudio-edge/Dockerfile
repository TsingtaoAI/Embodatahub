# RSLStudio Edge Agent — 边缘采集容器
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY rslstudio_edge/ ./rslstudio_edge/

RUN pip install --no-cache-dir -e .

EXPOSE 9091
HEALTHCHECK --interval=15s --timeout=5s \
    CMD curl -f http://localhost:9091/health || exit 1

ENTRYPOINT ["rslstudio-edge"]
CMD ["--config", "/etc/rslstudio-edge/config.yaml"]
