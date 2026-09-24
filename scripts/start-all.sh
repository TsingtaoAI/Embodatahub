#!/usr/bin/env bash
# ============================================================================
# TsingtaoAI 全服务一键启动脚本
# 在电脑重启后，运行此脚本即可启动所有服务
# ============================================================================
set -e

# ── 配置 ──────────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 加载 .env 文件中的环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# 数据目录（与代码分离，避免安全隐患）
DATA_DIR="${DATA_DIR:-$HOME/rslstudio-data}"
# 若默认路径不存在但备份路径存在，自动使用备份路径
if [ ! -d "$DATA_DIR/datasets" ] && [ -d "$HOME/rslstudio-data.bak/datasets" ]; then
    DATA_DIR="$HOME/rslstudio-data.bak"
fi
RDS_SAMPLES_DIR="${RDS_SAMPLES_DIR:-$DATA_DIR/datasets}"
RDS_ARTIFACT_DIR="${RDS_ARTIFACT_DIR:-$DATA_DIR/rds-artifacts}"

# 日志目录
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# ── 颜色输出 ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $1"; }

# ── 辅助函数 ──────────────────────────────────────────────────────────

# 等待端口可用
wait_for_port() {
    local port=$1
    local service=$2
    local timeout=${3:-30}
    local elapsed=0

    while ! ss -tlnp 2>/dev/null | grep -q ":$port "; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [ "$elapsed" -ge "$timeout" ]; then
            fail "$service 未能启动（超时 ${timeout}s）"
            return 1
        fi
    done
    ok "$service 启动成功 (端口 $port)"
    return 0
}

# 检查命令是否存在
check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        fail "未找到命令: $1，请先安装"
        return 1
    fi
    return 0
}

# ── 正文 ──────────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  TsingtaoAI 全服务一键启动${NC}"
echo -e "${CYAN}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ─── 1. 前置检查 ────────────────────────────────────────
info "检查依赖..."

check_cmd docker     || exit 1
check_cmd pnpm       || exit 1
check_cmd python3    || exit 1
check_cmd node       || exit 1

ok "依赖检查通过"
echo ""

# ─── 2. 生成 HTTPS 证书（如不存在）───────────────────────
CERT_DIR="$PROJECT_DIR/certs"
CERT_KEY="$CERT_DIR/key.pem"
CERT_CRT="$CERT_DIR/cert.pem"

# 采用「本地 CA + 由 CA 签发服务器证书」（等价 mkcert）。
# 切勿改回自签单证书：Firefox 两条路都拒绝 —— CA:TRUE 报
# MOZILLA_PKIX_ERROR_CA_CERT_USED_AS_END_ENTITY；CA:FALSE 则不被认作信任锚。
# 浏览器只需信任 ca-cert.pem 一次，之后所有端口/IP 自动信任。
CA_KEY="$CERT_DIR/ca-key.pem"
CA_CRT="$CERT_DIR/ca-cert.pem"

# SAN：回环 + 本机所有 IPv4（含 Tailscale/Docker）+ 可选 EXTRA_SAN
build_san() {
    local san="DNS:localhost,IP:127.0.0.1"
    local ip
    for ip in $(hostname -I 2>/dev/null); do
        case "$ip" in *:*) continue ;; esac
        san="$san,IP:$ip"
    done
    [ -n "${EXTRA_SAN:-}" ] && san="$san,$EXTRA_SAN"
    printf '%s' "$san"
}

if [ -f "$CERT_KEY" ] && [ -f "$CERT_CRT" ] && [ -f "$CA_CRT" ]; then
    ok "HTTPS 证书已存在"
else
    info "生成本地 CA 与服务器证书..."
    mkdir -p "$CERT_DIR"

    if [ ! -f "$CA_KEY" ] || [ ! -f "$CA_CRT" ]; then
        openssl req -x509 -newkey rsa:2048 -keyout "$CA_KEY" -out "$CA_CRT" \
            -days 3650 -nodes -subj "/CN=rslstudio-local-ca/O=rslstudio" \
            -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
            -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null
        warn "已新建 CA：$CA_CRT —— 需要在浏览器中信任该 CA 一次"
    fi

    SAN="$(build_san)"
    openssl req -newkey rsa:2048 -keyout "$CERT_KEY" -out "$CERT_DIR/.server.csr" \
        -nodes -subj "/CN=rslstudio" 2>/dev/null
    cat > "$CERT_DIR/.ext.cnf" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=$SAN
EOF
    openssl x509 -req -in "$CERT_DIR/.server.csr" -CA "$CA_CRT" -CAkey "$CA_KEY" \
        -CAcreateserial -out "$CERT_CRT" -days 3650 \
        -extfile "$CERT_DIR/.ext.cnf" 2>/dev/null
    rm -f "$CERT_DIR/.server.csr" "$CERT_DIR/.ext.cnf"
    ok "HTTPS 证书已生成（SAN: $SAN）"
fi
echo ""

# ─── 3. 启动 Docker 基础设施 ─────────────────────────────
info "启动 Docker 基础设施 (PostgreSQL, Redis, SeaweedFS)..."

if docker compose ps 2>/dev/null | grep -q "Up"; then
    ok "Docker 服务已在运行"
else
    docker compose up -d database seaweedfs redis fake-oauth 2>&1 | sed 's/^/  /'
    ok "Docker 基础设施已启动"
fi
echo ""

# ─── 4. 等待基础设施就绪 ─────────────────────────────────
info "等待数据库就绪..."
sleep 3

# ─── 5. 启动主后端 (NestJS, 端口 3000) ───────────────────
info "启动主后端 (NestJS, 端口 3000)..."

if ss -tlnp 2>/dev/null | grep -q ":3000 "; then
    ok "主后端已在运行"
else
    nohup pnpm --filter rslstudio-backend run start:dev \
        > "$LOG_DIR/backend.log" 2>&1 &
    echo "  PID: $!"
    wait_for_port 3000 "主后端" 60
fi
echo ""

# ─── 6. 启动主前端 (Quasar, 端口 8880) ───────────────────
info "启动主前端 (Quasar, 端口 8880)..."

if ss -tlnp 2>/dev/null | grep -q ":8880 "; then
    ok "主前端已在运行"
else
    nohup env CHOKIDAR_USEPOLLING=1 CHOKIDAR_INTERVAL=1000 \
        pnpm --filter rslstudio-frontend run start:dev \
        > "$LOG_DIR/frontend.log" 2>&1 &
    echo "  PID: $!"
    wait_for_port 8880 "主前端" 60
fi
echo ""

# ─── 7. 安装 RDS 依赖 ─────────────────────────────────────
RDS_DIR="$PROJECT_DIR/robot-data-studio"
# RDS 后端运行环境：quadruped conda 环境（原 .venv 系旧机迁移残留、shebang 失效，已弃用为 *.bak-oldserver）
RDS_PYTHON="${RDS_PYTHON:-/data/mashideng/miniconda3/envs/quadruped/bin/python}"

info "检查 RDS Python 依赖..."
if "$RDS_PYTHON" -c "import robot_data_studio" 2>/dev/null; then
    ok "RDS Python 包已安装"
else
    warn "安装 RDS Python 依赖（首次启动需要几分钟）..."
    "$RDS_PYTHON" -m pip install -e "$RDS_DIR" 2>&1 | tail -1
    # 确保关键依赖已安装
    for pkg in pyarrow h5py zarr rerun-sdk imageio-ffmpeg pin numcodecs; do
        "$RDS_PYTHON" -c "import $pkg" 2>/dev/null || \
            "$RDS_PYTHON" -m pip install "$pkg" 2>&1 | tail -1
    done
    ok "RDS Python 依赖安装完成"
fi

info "检查 RDS 前端依赖..."
if [ -d "$RDS_DIR/node_modules" ]; then
    ok "RDS 前端依赖已安装"
else
    warn "安装 RDS 前端依赖..."
    cd "$RDS_DIR" && pnpm install 2>&1 | tail -1
    ok "RDS 前端依赖安装完成"
fi

# 确保 HTTPS 证书就位
if [ ! -f "$RDS_DIR/certs/key.pem" ]; then
    mkdir -p "$RDS_DIR/certs"
    cp "$CERT_KEY" "$CERT_CRT" "$RDS_DIR/certs/"
    ok "RDS HTTPS 证书已配置"
fi

# ─── 8. 启动 RDS 后端 (FastAPI, 端口 8005) ───────────────
info "启动 RDS 后端 (FastAPI, 端口 8005)..."

if ss -tlnp 2>/dev/null | grep -q ":8005 "; then
    ok "RDS 后端已在运行"
else
    mkdir -p "$RDS_SAMPLES_DIR" "$RDS_ARTIFACT_DIR"
    cd "$RDS_DIR"
    # RDS 后端运行环境：quadruped conda 环境（原 .venv 系旧机迁移残留、shebang 失效，已弃用为 *.bak-oldserver）
    RDS_PYTHON="${RDS_PYTHON:-/data/mashideng/miniconda3/envs/quadruped/bin/python}"
    nohup env PYTHONPATH="$RDS_DIR:$RDS_DIR/packages:$PYTHONPATH" \
        RDS_SAMPLES_DIR="$RDS_SAMPLES_DIR" \
        RDS_ARTIFACT_DIR="$RDS_ARTIFACT_DIR" \
        "$RDS_PYTHON" -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8005 \
        > "$LOG_DIR/rds-backend.log" 2>&1 &
    echo "  PID: $!"
    cd "$PROJECT_DIR"
    wait_for_port 8005 "RDS 后端" 30
fi
echo ""

# ─── 9. 启动 RDS 前端 (Vite, 端口 5173, HTTPS) ───────────
info "启动 RDS 前端 (Vite, 端口 5173, HTTPS)..."

if ss -tlnp 2>/dev/null | grep -q ":5173 "; then
    ok "RDS 前端已在运行"
else
    cd "$RDS_DIR/apps/web"
    nohup env CHOKIDAR_USEPOLLING=1 CHOKIDAR_INTERVAL=1000 \
        ./node_modules/.bin/vite --host 0.0.0.0 --port 5173 --strictPort \
        > "$LOG_DIR/rds-frontend.log" 2>&1 &
    echo "  PID: $!"
    cd "$PROJECT_DIR"
    wait_for_port 5173 "RDS 前端" 30
fi
echo ""

# ─── 9. 启动 Spark Studio 后端 (FastAPI, 端口 8004) ─────
info "启动 Spark Studio 后端 (FastAPI, 端口 8004)..."

if ss -tlnp 2>/dev/null | grep -q ":8004 "; then
    ok "Spark Studio 后端已在运行"
else
    SPARK_VENV="$PROJECT_DIR/spark-studio/backend/.venv"
    if [ -x "$SPARK_VENV/bin/uvicorn" ]; then
        nohup "$SPARK_VENV/bin/uvicorn" apps.api.main:app --host 0.0.0.0 --port 8004 \
            > "$LOG_DIR/spark-backend.log" 2>&1 &
        echo "  PID: $!"
    else
        warn "Spark venv 不可用（$SPARK_VENV），跳过；如需启用请重建该 venv"
    fi
    # 容错：Spark 失败不得中断后续服务（本段之后还有 queue consumer 与 Spark 前端）
    wait_for_port 8004 "Spark Studio 后端" 30 || warn "Spark Studio 后端 未启动，继续后续服务"
fi
echo ""

# ─── 10. 启动 Queue Consumer（端口 3001，注册本机为 worker）─
info "启动 Queue Consumer（端口 3001）..."

if ss -tlnp 2>/dev/null | grep -q ":3001 "; then
    ok "Queue Consumer 已在运行"
else
    nohup npx dotenv -e .env -- pnpm --filter rslstudio-queue-consumer run start:dev \
        > "$LOG_DIR/queue-consumer.log" 2>&1 &
    echo "  PID: $!"
    wait_for_port 3001 "Queue Consumer" 90
fi
echo ""

# ─── 11. 启动 Spark Studio 前端 (Vite, 端口 5174) ────────
info "启动 Spark Studio 前端 (Vite, 端口 5174)..."

if ss -tlnp 2>/dev/null | grep -q ":5174 "; then
    ok "Spark Studio 前端已在运行"
else
    cd spark-studio/frontend
    nohup env CHOKIDAR_USEPOLLING=1 CHOKIDAR_INTERVAL=1000 \
        node node_modules/vite/bin/vite.js --port 5174 --host 0.0.0.0 \
        > "$LOG_DIR/spark-frontend.log" 2>&1 &
    echo "  PID: $!"
    cd "$PROJECT_DIR"
    wait_for_port 5174 "Spark Studio 前端" 30
fi
echo ""

# ─── 完成 ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🎉 所有服务启动完毕！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  主前端:       ${CYAN}https://localhost:8003${NC}"
echo -e "  后端 API:     ${CYAN}http://localhost:3000${NC}"
echo -e "  Queue Worker: ${CYAN}http://localhost:3001${NC}"
echo -e "  RDS 前端:     ${CYAN}https://localhost:5173${NC}"
echo -e "  RDS 后端:     ${CYAN}http://localhost:8005${NC}"
echo -e "  Spark 前端:   ${CYAN}http://localhost:5174${NC}"
echo -e "  Spark 后端:   ${CYAN}http://localhost:8004${NC}"
echo -e "  world-model:  ${CYAN}cd world-model && source .venv/bin/activate${NC}"
echo ""
echo -e "  训练启动:     ${YELLOW}bash world-model/scripts/train.sh [config] [data_dir] [name] [iterations]${NC}"
echo -e "  数据预处理:   ${YELLOW}python world-model/pipelines/data_prep.py <video> --name <scene>${NC}"
echo ""
echo -e "  日志目录:     ${YELLOW}$LOG_DIR${NC}"
echo -e "  停止服务:     ${YELLOW}scripts/stop-all.sh${NC}"
echo ""
