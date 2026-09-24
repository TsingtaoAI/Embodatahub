"""
数据预处理 — 从视频/ROS bag 提取训练所需的多视角图像序列

支持:
  - 视频文件 (.mp4, .avi, .mov, .webm) → 帧序列
  - 图像序列目录 (jpg/png) → 整理为训练集
  - ROS bag (.bag, .mcap) → 提取图像话题（需 rosbag 库）
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm


def extract_frames_from_video(
    video_path: str,
    output_dir: str,
    fps: float = 2.0,
    max_frames: int = 300,
    resolution: int = -1,
) -> list[str]:
    """
    从视频中按指定帧率提取帧

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        fps: 目标帧率（帧/秒）
        max_frames: 最大提取帧数
        resolution: 分辨率限制（-1 为原始分辨率）

    Returns:
        图像文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频: {video_path}")

    # 获取视频信息
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps if video_fps > 0 else 0

    print(f"  视频: {Path(video_path).name}")
    print(f"  分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"  帧率: {video_fps:.1f} fps, 时长: {duration:.1f}s, 总帧数: {total_frames}")

    # 计算提取间隔
    frame_interval = max(1, int(video_fps / fps))
    print(f"  提取间隔: 每 {frame_interval} 帧提取一帧")

    saved_frames: list[str] = []
    frame_count = 0
    saved_count = 0

    with tqdm(total=min(total_frames, max_frames * frame_interval), desc="提取帧") as pbar:
        while True:
            ret, frame = cap.read()
            if not ret or saved_count >= max_frames:
                break

            if frame_count % frame_interval == 0:
                # 调整分辨率
                if resolution > 0:
                    h, w = frame.shape[:2]
                    scale = resolution / max(h, w)
                    if scale < 1:
                        new_w, new_h = int(w * scale), int(h * scale)
                        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

                # 保存图像
                filename = f"frame_{saved_count:06d}.png"
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, frame)
                saved_frames.append(filepath)
                saved_count += 1

            frame_count += 1
            pbar.update(1)

    cap.release()
    print(f"  提取完成: {saved_count} 帧 → {output_dir}")
    return saved_frames


def prepare_colmap_like_structure(
    image_dir: str,
    output_dir: str,
) -> str:
    """
    将图像整理为 COLMAP 兼容的目录结构:

    output_dir/
    ├── images/          # 输入图像
    ├── sparse/          # (后续由 COLMAP 生成)
    └── distorted/       # (COLMAP 原始输出)

    Args:
        image_dir: 图像目录
        output_dir: 训练数据目录

    Returns:
        训练数据目录路径
    """
    train_dir = os.path.join(output_dir, "train_data")
    images_out = os.path.join(train_dir, "images")
    os.makedirs(images_out, exist_ok=True)

    # 复制图像（确保连续编号）
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    image_files = sorted(
        [f for f in os.listdir(image_dir)
         if Path(f).suffix.lower() in image_extensions]
    )

    for i, fname in enumerate(image_files):
        src = os.path.join(image_dir, fname)
        dst = os.path.join(images_out, f"{i:06d}.png")
        shutil.copy2(src, dst)

    print(f"  整理完成: {len(image_files)} 张图像 → {images_out}")
    return train_dir


def run_colmap_sfm(
    train_dir: str,
    colmap_path: str = "colmap",
) -> bool:
    """
    运行 COLMAP 稀疏重建（生成相机位姿和稀疏点云）

    这是 3DGS 训练的初始化步骤。如果 COLMAP 不可用或不需要，
    训练脚本会使用随机初始化。

    Args:
        train_dir: 训练数据目录（含 images/ 子目录）
        colmap_path: COLMAP 可执行文件路径

    Returns:
        是否成功运行 COLMAP
    """
    if not shutil.which(colmap_path):
        print("  ⚠️  COLMAP 未安装，跳过 SfM 重建（将使用随机初始化）")
        print(f"  安装: sudo apt install colmap")
        return False

    image_dir = os.path.join(train_dir, "images")
    sparse_dir = os.path.join(train_dir, "sparse")
    distorted_dir = os.path.join(train_dir, "distorted")
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(distorted_dir, exist_ok=True)

    db_path = os.path.join(train_dir, "database.db")

    try:
        print("  [1/3] 特征提取...")
        subprocess.run([
            colmap_path, "feature_extractor",
            "--database_path", db_path,
            "--image_path", image_dir,
            "--ImageReader.single_camera", "1",
            "--SiftExtraction.max_num_features", "8192",
        ], check=True, capture_output=True)

        print("  [2/3] 特征匹配...")
        subprocess.run([
            colmap_path, "exhaustive_matcher",
            "--database_path", db_path,
        ], check=True, capture_output=True)

        print("  [3/3] 稀疏重建...")
        subprocess.run([
            colmap_path, "mapper",
            "--database_path", db_path,
            "--image_path", image_dir,
            "--output_path", distorted_dir,
        ], check=True, capture_output=True)

        # 将结果复制到 sparse/
        # (COLMAP 输出在 distorted_dir/0/ 中)
        colmap_out = os.path.join(distorted_dir, "0")
        if os.path.exists(colmap_out):
            for f in os.listdir(colmap_out):
                shutil.copy2(os.path.join(colmap_out, f), sparse_dir)

        print("  ✅ COLMAP 重建完成")
        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ⚠️  COLMAP 运行失败: {e}")
        print(f"  将使用随机初始化进行训练")
        return False


def main():
    parser = argparse.ArgumentParser(description="数据预处理：从视频/图像提取训练数据")
    parser.add_argument("input", help="输入视频文件或图像目录")
    parser.add_argument("--output", "-o", default="./data", help="输出目录")
    parser.add_argument("--fps", type=float, default=2.0, help="提取帧率")
    parser.add_argument("--max-frames", type=int, default=300, help="最大帧数")
    parser.add_argument("--resolution", type=int, default=-1, help="分辨率限制")
    parser.add_argument("--colmap", action="store_true", help="运行 COLMAP SfM")
    parser.add_argument("--name", "-n", default="scene", help="场景名称")

    args = parser.parse_args()

    input_path = args.input
    output_dir = os.path.join(args.output, args.name)
    os.makedirs(output_dir, exist_ok=True)

    # 判断输入类型
    video_extensions = {".mp4", ".avi", ".mov", ".webm", ".mkv", ".flv"}

    if os.path.isfile(input_path) and Path(input_path).suffix.lower() in video_extensions:
        print(f"\n📹 从视频提取帧: {input_path}")
        frames = extract_frames_from_video(
            input_path,
            os.path.join(output_dir, "raw_frames"),
            fps=args.fps,
            max_frames=args.max_frames,
            resolution=args.resolution,
        )
        image_dir = os.path.join(output_dir, "raw_frames")

    elif os.path.isdir(input_path):
        print(f"\n📁 从目录整理图像: {input_path}")
        image_dir = input_path

    else:
        print(f"❌ 不支持的输入: {input_path}")
        sys.exit(1)

    # 整理为 COLMAP 兼容结构
    train_dir = prepare_colmap_like_structure(image_dir, output_dir)

    # 可选：运行 COLMAP
    if args.colmap:
        run_colmap_sfm(train_dir)

    print(f"\n✅ 数据预处理完成!")
    print(f"  训练数据: {train_dir}")
    print(f"  图像数量: {len(os.listdir(os.path.join(train_dir, 'images')))}")
    print(f"\n  运行训练:")
    print(f"  python pipelines/gs_train.py --data {train_dir} --name {args.name}")
    print()


if __name__ == "__main__":
    main()
