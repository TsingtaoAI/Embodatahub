# -------------------------- development 开发阶段 ---------------------------
FROM python:3.12-slim AS development

# 设置国内 pip 镜像
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖文件
COPY robot-data-studio/pyproject.toml ./robot-data-studio/
COPY robot-data-studio/packages/robot_data_studio/ ./robot-data-studio/packages/robot_data_studio/

# 安装 Python 依赖
RUN cd robot-data-studio && pip install --upgrade pip && \
    pip install -e '.[dev]'

# 开发模式使用热重载
WORKDIR /app/robot-data-studio
CMD ["uvicorn", "apps.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]


# -------------------------- production 生产阶段 ---------------------------
FROM python:3.12-slim AS production

# 设置国内 pip 镜像
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 只复制生产需要的内容
COPY robot-data-studio/pyproject.toml ./robot-data-studio/
COPY robot-data-studio/packages/robot_data_studio/ ./robot-data-studio/packages/robot_data_studio/
COPY robot-data-studio/apps/api/ ./robot-data-studio/apps/api/

RUN cd robot-data-studio && \
    pip install --upgrade pip && \
    pip install -e '.' && \
    rm -rf /root/.cache/pip

EXPOSE 8000

WORKDIR /app/robot-data-studio
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
