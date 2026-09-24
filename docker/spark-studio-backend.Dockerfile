# -------------------------- development 开发阶段 ---------------------------
FROM python:3.12-slim AS development

# 设置国内 pip 镜像
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖文件
COPY spark-studio/backend/pyproject.toml ./spark-studio/backend/

# 安装 Python 依赖
RUN cd spark-studio/backend && pip install --upgrade pip && \
    pip install -e '.[dev]'

# 开发模式使用热重载
WORKDIR /app/spark-studio/backend
CMD ["uvicorn", "apps.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8004"]


# -------------------------- production 生产阶段 ---------------------------
FROM python:3.12-slim AS production

# 设置国内 pip 镜像
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制后端源码
COPY spark-studio/backend/pyproject.toml ./spark-studio/backend/
COPY spark-studio/backend/apps/ ./spark-studio/backend/apps/

RUN cd spark-studio/backend && \
    pip install --upgrade pip && \
    pip install -e .

# 创建数据目录
RUN mkdir -p /data/spark-studio

ENV SPARK_DATA_DIR=/data/spark-studio

EXPOSE 8004

WORKDIR /app/spark-studio/backend
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8004"]
