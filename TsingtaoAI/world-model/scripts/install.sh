#!/usr/bin/env bash
# ============================================================================
# world-model 训练环境一键安装脚本
# ============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "============================================"
echo "  world-model 训练环境安装"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# 1. 创建虚拟环境（推荐）
if [ ! -d ".venv" ]; then
    echo "[1/4] 创建虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2. 升级 pip
echo "[2/4] 升级 pip..."
pip install --upgrade pip setuptools wheel

# 3. 安装 PyTorch（根据 CUDA 版本选择）
echo "[3/4] 安装 PyTorch + CUDA 支持..."
# 先检测 CUDA 版本
CUDA_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1)
echo "  CUDA Driver: $CUDA_VER"

# 安装 PyTorch（使用最新稳定版）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

# 4. 安装项目依赖
echo "[4/4] 安装 world-model 依赖..."
pip install -e '.[train,dev]'

echo ""
echo "============================================"
echo "  ✅ 安装完成！"
echo "  激活环境: source .venv/bin/activate"
echo "  运行训练: python pipelines/gs_train.py --config configs/train_default.yaml"
echo "============================================"
