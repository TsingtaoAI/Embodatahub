# -------------------------- build 构建阶段 ---------------------------
FROM node:22-slim AS build

# 国内镜像
ENV COREPACK_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_DISTURL=https://npmmirror.com/dist
ENV PNPM_FETCH_TIMEOUT=300000

WORKDIR /app

# 通过 npm 安装 pnpm（corepack 在国内网络可能下载失败）
RUN npm install -g pnpm@11.7.0 --registry=https://registry.npmmirror.com

# 配置 pnpm 使用国内镜像
RUN pnpm config set registry https://registry.npmmirror.com

# 复制依赖文件
COPY robot-data-studio/package.json robot-data-studio/pnpm-workspace.yaml ./
COPY robot-data-studio/apps/web/package.json apps/web/
COPY robot-data-studio/pnpm-lock.yaml ./

# 安装依赖
RUN pnpm fetch

# 复制源码
COPY robot-data-studio/ .

# 构建（CI=true 防止 TTY 交互提示）
ENV CI=true
RUN pnpm install --offline && \
    pnpm build:web


# -------------------------- production 生产阶段 ---------------------------
FROM debian:bookworm-slim AS production

# 安装 nginx
RUN apt-get update && \
    apt-get install -y nginx && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /etc/nginx/sites-enabled/default && \
    # 配置非 root 运行
    sed -i 's/user www-data;//g' /etc/nginx/nginx.conf && \
    sed -i 's/pid \/run\/nginx.pid;/pid \/tmp\/nginx.pid;/g' /etc/nginx/nginx.conf && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir -p /var/lib/nginx/body /var/lib/nginx/fastcgi /var/lib/nginx/proxy /var/lib/nginx/scgi /var/lib/nginx/uwsgi && \
    chmod -R 777 /var/lib/nginx /var/log/nginx

# 复制构建产物
COPY --from=build /app/apps/web/dist /usr/share/nginx/html

# nginx 配置
RUN echo 'server { \
    listen 80 default_server; \
    gzip on; \
    gzip_min_length 1000; \
    gzip_types text/plain text/xml application/javascript text/css; \
    root /usr/share/nginx/html; \
    location / { \
        add_header Cache-Control "no-store"; \
        try_files $uri $uri/index.html /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

USER 65532:65532

EXPOSE 80

ENTRYPOINT ["/usr/sbin/nginx", "-g", "daemon off;"]
