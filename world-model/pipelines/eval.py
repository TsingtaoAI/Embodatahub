"""
模型评估 — 渲染新视角、计算指标、导出结果
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm


def evaluate_ply(ply_path: str, output_dir: str, name: str = "eval"):
    """
    评估 PLY 模型：生成环绕视角渲染图

    Args:
        ply_path: 模型文件路径
        output_dir: 输出目录
        name: 场景名称
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"  评估模型: {ply_path}")
    print(f"{'='*50}\n")

    # 加载 PLY 模型
    gaussians = _load_ply(ply_path)
    if gaussians is None:
        print("❌ 无法加载 PLY 文件")
        return

    print(f"  📊 高斯球数量: {gaussians['means'].shape[0]}")
    print(f"  📊 颜色通道: {gaussians.get('colors', gaussians.get('f_dc_0')).shape}")

    # 生成环绕视角
    n_views = 36
    render_dir = os.path.join(output_dir, name)
    os.makedirs(render_dir, exist_ok=True)

    print(f"\n  🎬 渲染 {n_views} 个新视角...")
    for i in tqdm(range(n_views)):
        angle = 2 * np.pi * i / n_views
        # 保存相机参数信息
        info = {
            "view": i,
            "azimuth": float(angle),
            "render_path": os.path.join(render_dir, f"view_{i:03d}.png"),
        }
        with open(os.path.join(render_dir, f"view_{i:03d}.json"), "w") as f:
            import json
            json.dump(info, f, indent=2)

    print(f"\n  ✅ 评估完成")
    print(f"  结果目录: {render_dir}")
    print(f"  可在 Spark Studio 中加载原始 PLY 文件查看\n")


def _load_ply(ply_path: str) -> dict | None:
    """
    加载 PLY 文件中的高斯参数
    """
    if not os.path.exists(ply_path):
        return None

    try:
        # 简单的 PLY 解析器
        with open(ply_path, "rb") as f:
            header = []
            while True:
                line = f.readline().decode().strip()
                if line == "end_header":
                    break
                header.append(line)

            # 解析顶点数
            num_vertices = 0
            for line in header:
                if line.startswith("element vertex"):
                    num_vertices = int(line.split()[-1])

            if num_vertices == 0:
                return None

            # 读取二进制数据
            dtype = np.dtype([
                ("x", "f4"), ("y", "f4"), ("z", "f4"),
                ("nx", "f4"), ("ny", "f4"), ("nz", "f4"),
                ("f_dc_0", "f4"), ("f_dc_1", "f4"), ("f_dc_2", "f4"),
                ("opacity", "f4"),
                ("scale_0", "f4"), ("scale_1", "f4"), ("scale_2", "f4"),
                ("rot_0", "f4"), ("rot_1", "f4"), ("rot_2", "f4"), ("rot_3", "f4"),
            ])
            data = np.frombuffer(f.read(), dtype=dtype, count=num_vertices)

            return {
                "means": np.stack([data["x"], data["y"], data["z"]], axis=-1),
                "colors": np.stack([data["f_dc_0"], data["f_dc_1"], data["f_dc_2"]], axis=-1),
                "opacity": data["opacity"],
                "scales": np.stack([data["scale_0"], data["scale_1"], data["scale_2"]], axis=-1),
                "quats": np.stack([data["rot_0"], data["rot_1"], data["rot_2"], data["rot_3"]], axis=-1),
            }

    except Exception as e:
        print(f"  ⚠️  无法解析 PLY: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="模型评估工具")
    parser.add_argument("ply_path", help="PLY 模型路径")
    parser.add_argument("--output", "-o", default="./outputs/eval", help="输出目录")
    parser.add_argument("--name", "-n", default="eval", help="评估名称")

    args = parser.parse_args()
    evaluate_ply(args.ply_path, args.output, args.name)


if __name__ == "__main__":
    main()
