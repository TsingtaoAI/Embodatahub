FROM tsintaorsl-base AS development
# Install runtime dependencies for Python (rosbags)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install rosbags --break-system-packages --no-cache-dir
USER node
WORKDIR /app/backend
CMD ["./entrypoint.sh"]

FROM node:22-slim AS build
# 全局配置国内镜像，解决corepack/pnpm拉取境外源超时
ENV COREPACK_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_DISTURL=https://npmmirror.com/dist
ENV PNPM_FETCH_TIMEOUT=300000

WORKDIR /app
# 安装编译依赖，解决better-sqlite3 node-gyp缺失Python/gcc报错
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3 /usr/bin/python

# corepack 使用国内镜像安装pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate
# 强制写入pnpm国内镜像配置，双重兜底
RUN pnpm config set registry https://registry.npmmirror.com \
    && pnpm config set disturl https://npmmirror.com \
    && pnpm config set fetch-timeout 300000

COPY pnpm-lock.yaml ./
RUN pnpm fetch
COPY . .
RUN pnpm install -r

# Build packages and backend
RUN pnpm --filter @tsintaorsl/shared build
RUN pnpm --filter @tsintaorsl/validation build
RUN pnpm --filter @tsintaorsl/api-dto build
RUN pnpm --filter @tsintaorsl/backend-common build
RUN NODE_ENV=production pnpm --filter tsintaorsl-backend build
RUN pnpm deploy --filter=tsintaorsl-backend --prod --legacy /prod/backend

# 替换国内百度镜像，解决gcr.io境外地址超时
FROM mirror.baidubce.com/gcr/distroless/nodejs22-debian12 AS production
WORKDIR /app
COPY --from=build /app/backend/dist/main.js ./backend/dist/main.js
COPY --from=build /app/backend/package.json ./backend/package.json
COPY --from=build /app/backend/assets/favicon.png ./backend/assets/favicon.png
WORKDIR /app/backend
CMD ["dist/main.js"]

