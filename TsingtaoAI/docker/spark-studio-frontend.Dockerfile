# -------------------------- build 构建阶段 ---------------------------
FROM node:22-slim AS build

# 国内镜像
ENV COREPACK_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_REGISTRY=https://registry.npmmirror.com
ENV PNPM_CONFIG_DISTURL=https://npmmirror.com/dist
ENV PNPM_FETCH_TIMEOUT=300000

WORKDIR /app

# 通过 npm 安装 pnpm
RUN npm install -g pnpm@11.7.0 --registry=https://registry.npmmirror.com

# 配置 pnpm 使用国内镜像
RUN pnpm config set registry https://registry.npmmirror.com

# TODO: 构建前端 — 但 spark-studio 前端目前是独立 Vite 应用
# 当需要正式构建时取消以下注释
# COPY spark-studio/frontend/package.json spark-studio/frontend/pnpm-lock.yaml ./
# RUN pnpm fetch
# COPY spark-studio/frontend/ .
# ENV CI=true
# RUN pnpm install --offline && pnpm build
RUN mkdir -p /app/dist && echo "Spark Studio Frontend" > /app/dist/index.html


# -------------------------- production 生产阶段 ---------------------------
FROM debian:bookworm-slim AS production

# 安装 nginx
RUN apt-get update && \
    apt-get install -y nginx && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /etc/nginx/sites-enabled/default && \
    sed -i 's/user www-data;//g' /etc/nginx/nginx.conf && \
    sed -i 's/pid \/run\/nginx.pid;/pid \/tmp\/nginx.pid;/g' /etc/nginx/nginx.conf && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir -p /var/lib/nginx/body /var/lib/nginx/fastcgi /var/lib/nginx/proxy /var/lib/nginx/scgi /var/lib/nginx/uwsgi && \
    chmod -R 777 /var/lib/nginx /var/log/nginx

COPY --from=build /app/dist /usr/share/nginx/html

# nginx 配置 — 支持 SPA 路由 + 大文件流式传输
RUN echo 'server { \
    listen 80 default_server; \
    gzip on; \
    gzip_min_length 1000; \
    gzip_types text/plain text/xml application/javascript text/css; \
    # 大文件流式传输支持（用于 .rad 文件） \
    proxy_max_temp_file_size 0; \
    proxy_request_buffering off; \
    root /usr/share/nginx/html; \
    location / { \
        add_header Cache-Control "no-store"; \
        try_files $uri $uri/index.html /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

USER 65532:65532

EXPOSE 80

ENTRYPOINT ["/usr/sbin/nginx", "-g", "daemon off;"]
