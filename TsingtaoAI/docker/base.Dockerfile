# -------------------------- build 构建阶段（修复网络+编译依赖）--------------------------
FROM node:22-slim AS build
# 最顶部注入国内镜像环境变量，corepack/pnpm优先读取
ENV COREPACK_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_DISTURL=https://npmmirror.com/dist
ENV PNPM_FETCH_TIMEOUT=300000

WORKDIR /app

# 安装编译依赖：python3/gcc/g++/make 解决node-gyp编译better-sqlite3报错
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/* \
    # 软链接python3为python，node-gyp自动识别
    && ln -s /usr/bin/python3 /usr/bin/python

# corepack启用并使用国内镜像下载pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate
# 强制pnpm写入国内镜像配置（双重保险）
RUN pnpm config set registry https://registry.npmmirror.com \
    && pnpm config set disturl https://npmmirror.com \
    && pnpm config set fetch-timeout 300000

COPY pnpm-lock.yaml ./
RUN pnpm fetch
COPY . .
RUN pnpm install -r

# Build packages and backend
RUN pnpm --filter @kleinkram/shared build
RUN pnpm --filter @kleinkram/validation build
RUN pnpm --filter @kleinkram/api-dto build
RUN pnpm --filter @kleinkram/backend-common build
RUN NODE_ENV=production pnpm --filter kleinkram-backend build
RUN pnpm deploy --filter=kleinkram-backend --prod --legacy /prod/backend

# -------------------------- 开发环境阶段（复用基础镜像）--------------------------
FROM kleinkram-base AS development
# Install runtime dependencies for Python (rosbags)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install rosbags --break-system-packages --no-cache-dir
USER node
WORKDIR /app/backend
CMD ["./entrypoint.sh"]

# -------------------------- 生产运行阶段（distroless轻量镜像）--------------------------
FROM gcr.io/distroless/nodejs22-debian12 AS production
WORKDIR /app
COPY --from=build /app/backend/dist/main.js ./backend/dist/main.js
COPY --from=build /app/backend/package.json ./backend/package.json
COPY --from=build /app/backend/assets/favicon.png ./backend/assets/favicon.png
WORKDIR /app/backend
CMD ["dist/main.js"]

