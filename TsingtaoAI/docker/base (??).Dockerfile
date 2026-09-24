FROM node:22-slim AS base

RUN corepack enable && corepack prepare pnpm@latest --activate
RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*


ARG USER_ID=1000
ARG GROUP_ID=1000

RUN if [ ${USER_ID} -ne 1000 ]; then \
    deluser --remove-home node && \
    addgroup -g ${GROUP_ID} node && \
    adduser -u ${USER_ID} -G node -s /bin/sh -D node; \
    fi

WORKDIR /app
RUN chown node:node /app
USER node

# Install dependencies using pnpm fetch for caching
COPY --chown=node:node pnpm-lock.yaml ./
# 切换国内淘宝镜像，解决国外源超时
RUN pnpm config set registry https://registry.npmmirror.com
# 延长下载超时到2分钟
RUN pnpm config set fetch-timeout 120000
# 二进制包镜像代理，避免esbuild/swc/sass等二进制下载失败
ENV ESBUILD_BINARY_HOST=https://npmmirror.com/mirrors/esbuild
ENV SWC_BINARY_HOST=https://npmmirror.com/mirrors/sass
ENV SASS_BINARY_SITE=https://npmmirror.com/mirrors/sass
RUN pnpm fetch

# Only copy manifest files needed for installation, NOT source code
COPY --chown=node:node package.json pnpm-workspace.yaml tsconfig.base.json ./
COPY --chown=node:node packages/shared/package.json ./packages/shared/
COPY --chown=node:node packages/validation/package.json ./packages/validation/
COPY --chown=node:node packages/api-dto/package.json ./packages/api-dto/
COPY --chown=node:node packages/backend-common/package.json ./packages/backend-common/
COPY --chown=node:node backend/package.json ./backend/
COPY --chown=node:node queueConsumer/package.json ./queueConsumer/
COPY --chown=node:node frontend/package.json ./frontend/
COPY --chown=node:node frontend/create_build_info.sh ./frontend/

RUN pnpm install -r
