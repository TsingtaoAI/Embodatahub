#!/usr/bin/env bash
# ============================================================================
# world-model 训练启动脚本
# ============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 默认参数
CONFIG="${1:-configs/train_default.yaml}"
DATA="${2:-}"
NAME="${3:-my_scene}"
ITERATIONS="${4:-30000}"

CMD="python pipelines/gs_train.py"

if [ -f "$CONFIG" ]; then
    CMD="$CMD --config $CONFIG"
fi
if [ -n "$DATA" ]; then
    CMD="$CMD --data $DATA"
fi
CMD="$CMD --name $NAME --iterations $ITERATIONS"

echo "============================================"
echo "  world-model 训练"
echo "  场景: $NAME"
echo "  迭代: $ITERATIONS"
echo "  配置: $CONFIG"
echo "============================================"
echo ""
echo "> $CMD"
echo ""
eval "$CMD"
