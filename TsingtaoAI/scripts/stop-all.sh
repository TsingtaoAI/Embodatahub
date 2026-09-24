#!/usr/bin/env bash
# ============================================================================
# TsingtaoAI 全服务一键停止脚本
# ============================================================================

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  停止所有服务${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ── 1. 停止前端/后端 Node 进程 ──────────────────────────
info "停止 Node.js 服务..."

PORTS=(8880 3000 5173 5174)
for PORT in "${PORTS[@]}"; do
    PID=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$PID" ]; then
        kill "$PID" 2>/dev/null
        ok "端口 $PORT 进程 (PID $PID) 已停止"
    else
        info "端口 $PORT 无运行进程"
    fi
done

# ── 2. 停止 Python 服务 ─────────────────────────────────
info "停止 Python 服务..."

PY_PORTS=(8000 8004)
for PORT in "${PY_PORTS[@]}"; do
    PID=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$PID" ]; then
        kill "$PID" 2>/dev/null
        ok "端口 $PORT (PID $PID) 已停止"
    fi
done

# ── 3. 停止 Docker 基础设施 ──────────────────────────────
info "停止 Docker 基础设施..."
docker compose stop database seaweedfs redis 2>/dev/null
docker stop rslstudio-public 2>/dev/null || true
ok "Docker 服务已停止"

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo ""
