#!/usr/bin/env bash
# 兜底脚本：让 rslstudio-public 重新解析 bind mount。
#
# 历史背景：vite / quasar build 会替换输出目录本身（换掉 inode），容器若直接挂那个目录，
# 重建后仍指向旧 inode ⇒ nginx 读不到文件 ⇒ 全站 403（不是 404）。
#
# 2026-09-21 已「全根治」：三个前端的挂载点全部上提到不可变的 dist 父目录，
# 各自产物落在父目录下的子目录里（见 deploy/public/run-nginx.sh）：
#   /usr/share/nginx/html ← frontend/dist                    （root 指到 spa/）
#   /srv/rds-holder       ← robot-data-studio/apps/web/dist  （root 指到 rds-app/）
#   /srv/spark-holder     ← spark-studio/frontend/dist       （root 指到 spark/）
# ⇒ 重建任何一个前端都【不需要】再跑这个脚本。
#
# 仅在下面这类情况下才需要（会闪断几秒）：
#   - 站点出现 403 且排查指向挂载陈旧
#   - 改了 run-nginx.sh 的挂载点 / default.conf 的 root
set -euo pipefail
docker restart rslstudio-public
sleep 2
docker exec rslstudio-public nginx -t
echo "rslstudio-public 已按当前路径重新挂载 -> https://<host>:8003/"
