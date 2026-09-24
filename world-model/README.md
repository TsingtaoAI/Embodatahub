# world-model — 具身智能世界模型训练模块

将机器人/自动驾驶采集数据训练为 3D 模型，配合 Spark Studio 实现"采集 → 训练 → 可视化"闭环。

## 快速开始

### 1. 安装环境

```bash
cd world-model
bash scripts/install.sh
```

### 2. 从视频提取训练数据

```bash
source .venv/bin/activate
python pipelines/data_prep.py /path/to/video.mp4 --name my_scene
```

### 3. 训练 3DGS 模型

```bash
python pipelines/gs_train.py --data ./data/my_scene/train_data --name my_scene --iterations 30000
```

### 4. 查看结果

训练完成后模型会自动复制到 `spark-studio/data/`，打开主平台 → 「3D场景可视化」即可查看。

## 目录结构

```
world-model/
├── configs/            # 训练配置文件
│   └── train_default.yaml
├── pipelines/          # 训练流水线
│   ├── data_prep.py    # 数据预处理（视频抽帧/ROS bag 提取）
│   ├── gs_train.py     # 3DGS 训练引擎
│   └── eval.py         # 模型评估
├── scripts/            # 工具脚本
│   ├── install.sh      # 环境安装
│   └── train.sh        # 训练启动
├── data/               # 训练数据（共享数据请放在 ../spark-studio/data/）
├── models/             # 训练好的模型
├── outputs/            # 训练输出
├── requirements.txt
└── pyproject.toml
```

## 技术架构

| 组件 | 技术 |
|------|------|
| 深度学习框架 | PyTorch 2.6+ |
| 3DGS 渲染 | gsplat (nerfstudio) |
| 数据预处理 | OpenCV |
| 日志监控 | TensorBoard |
| SfM 初始化 | COLMAP（可选） |
| 模型格式 | .ply → .spz |

## 硬件要求

- **GPU**: NVIDIA GPU with CUDA (建议 8GB+ VRAM)
- **存储**: 每个场景约 5-20GB
- **当前环境**: RTX 4000 Ada (12GB) ✅
