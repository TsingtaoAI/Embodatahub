#!/usr/bin/env bash
# 重建对外 nginx 容器 (rslstudio-public)。
# 它服务生产包并挂在 8003;FRP(frpc.ini 的 rslstudio_web)把 8003 经华为云 1.95.73.178 暴露为公网。
# 三个 dist 必须先在各自目录 vite build / quasar build 出来。
#
# ⚠️ 挂载点全是「dist 父目录」而不是 dist 本身 —— vite/quasar build 会替换 dist 目录本身
#    (换 inode),容器若直接挂 dist,重建后仍指向旧 inode => nginx 读不到文件 => 403(不是 404)。
#    挂父目录则重建的只是它下面的子目录(html/spa、html-root/rds-app、rds-holder/rds-app ...),
#    父目录 inode 不变,bind mount 不会被换掉,重建后无需 docker restart。
set -euo pipefail
ROOT=/data/mashideng/rslstudio

docker rm -f rslstudio-public 2>/dev/null || true
docker run -d --name rslstudio-public \
  --network host \
  --restart unless-stopped \
  -v "$ROOT/frontend/dist:/usr/share/nginx/html:ro" \
  -v "$ROOT/robot-data-studio/apps/web/dist:/srv/rds-holder:ro" \
  -v "$ROOT/spark-studio/frontend/dist:/srv/spark-holder:ro" \
  -v "$ROOT/certs:/etc/nginx/certs:ro" \
  -v "$ROOT/deploy/public/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:alpine

sleep 2
docker exec rslstudio-public nginx -t
echo "rslstudio-public 已就绪 → https://<host>:8003/"
