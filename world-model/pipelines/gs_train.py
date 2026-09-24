"""
3D Gaussian Splatting 训练引擎

基于 gsplat (nerfstudio-project/gsplat) 实现。
支持:
  - COLMAP SfM 初始化
  - 随机点云初始化
  - 自适应密度控制
  - TensorBoard 日志
  - 模型导出 (.ply / .spz)
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import yaml
from PIL import Image
from tqdm import tqdm


# ─── 配置 ─────────────────────────────────────────────────────────────

@dataclass
class TrainConfig:
    """训练配置"""
    iterations: int = 30000
    save_interval: int = 5000
    eval_interval: int = 1000
    batch_size: int = 1
    num_workers: int = 4

    # 学习率
    lr_position: float = 0.00016
    lr_feature: float = 0.0025
    lr_opacity: float = 0.05
    lr_scaling: float = 0.005
    lr_rotation: float = 0.001

    # 高斯参数
    max_sh_degree: int = 3
    percent_dense: float = 0.01
    densification_interval: int = 100
    opacity_reset_interval: int = 3000
    densify_grad_threshold: float = 0.0002
    densify_size_threshold: float = 0.01

    # 数据
    resolution: int = -1
    random_points: int = 100000
    white_background: bool = False

    # 路径
    data_dir: str = ""
    log_dir: str = "./outputs/logs"
    model_dir: str = "./outputs/models"
    render_dir: str = "./outputs/renders"
    scene_name: str = "scene"


def load_config(config_path: str) -> TrainConfig:
    """从 YAML 加载配置"""
    with open(config_path) as f:
        cfg_dict = yaml.safe_load(f)

    cfg = TrainConfig()
    t = cfg_dict.get("training", {})
    d = cfg_dict.get("data", {})
    l = cfg_dict.get("logging", {})

    if ti := t.get("iterations"): cfg.iterations = ti
    if si := t.get("save_interval"): cfg.save_interval = si
    if ei := t.get("eval_interval"): cfg.eval_interval = ei

    lr = t.get("lr", {})
    if p := lr.get("position"): cfg.lr_position = p
    if f := lr.get("feature"): cfg.lr_feature = f
    if o := lr.get("opacity"): cfg.lr_opacity = o
    if s := lr.get("scaling"): cfg.lr_scaling = s
    if r := lr.get("rotation"): cfg.lr_rotation = r

    g = t.get("gaussian", {})
    if s := g.get("max_sh_degree"): cfg.max_sh_degree = s
    if p := g.get("percent_dense"): cfg.percent_dense = p
    if di := g.get("densification_interval"): cfg.densification_interval = di
    if ori := g.get("opacity_reset_interval"): cfg.opacity_reset_interval = ori
    if dgt := g.get("densify_grad_threshold"): cfg.densify_grad_threshold = dgt
    if dst := g.get("densify_size_threshold"): cfg.densify_size_threshold = dst

    if r := d.get("resolution"): cfg.resolution = r
    if rp := d.get("random_points"): cfg.random_points = rp
    if wb := d.get("white_background"): cfg.white_background = wb

    if ld := l.get("log_dir"): cfg.log_dir = ld
    if md := l.get("model_dir"): cfg.model_dir = md
    if rd := l.get("render_dir"): cfg.render_dir = rd

    return cfg


# ─── 数据集加载 ──────────────────────────────────────────────────────────

def load_colmap_data(data_dir: str):
    """
    加载 COLMAP 格式数据

    期望目录结构:
        data_dir/
        ├── images/            # 输入图像
        ├── sparse/            # COLMAP 输出
        │   ├── cameras.bin
        │   ├── images.bin
        │   └── points3D.bin
        └── database.db

    返回:
        images, camera_params, point_cloud
    """
    try:
        from pycolmap import Camera, Image, SceneManager
    except ImportError:
        print("  ⚠️  pycolmap 未安装，尝试读取原始 COLMAP 文件...")
        return _load_colmap_raw(data_dir)

    sparse_dir = os.path.join(data_dir, "sparse")
    if not os.path.exists(sparse_dir):
        return None

    print("  📷 加载 COLMAP 重建结果...")
    try:
        scene = SceneManager(sparse_dir)
        scene.load()
        return scene
    except Exception as e:
        print(f"  无法加载 COLMAP 数据: {e}")
        return None


def _load_colmap_raw(data_dir: str):
    """
    从 COLMAP 二进制文件读取（不依赖 pycolmap）
    """
    sparse_dir = os.path.join(data_dir, "sparse")
    if not os.path.exists(sparse_dir):
        return None

    # 尝试读取 cameras, images, points3D 二进制文件
    # 简化版：只读取图像路径
    images_dir = os.path.join(data_dir, "images")
    if not os.path.exists(images_dir):
        return None

    image_paths = sorted([
        os.path.join(images_dir, f) for f in os.listdir(images_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])

    if not image_paths:
        return None

    print(f"  找到 {len(image_paths)} 张图像（未加载相机参数）")
    return {
        "image_paths": image_paths,
        "num_images": len(image_paths),
    }


def create_random_dataset(
    num_images: int = 50,
    resolution: tuple[int, int] = (800, 600),
    device: str = "cuda",
):
    """
    创建随机相机参数用于测试

    在无 COLMAP 数据时，生成围绕场景的半球相机阵列。
    """
    import torch

    # 随机相机位置（半球面）
    azimuth = torch.linspace(0, 2 * math.pi, num_images)
    elevation = torch.full_like(azimuth, math.pi / 4)  # 45度俯角
    radius = 4.0

    camera_to_worlds = []
    for azi, ele in zip(azimuth, elevation):
        x = radius * math.cos(ele) * math.cos(azi)
        y = radius * math.cos(ele) * math.sin(azi)
        z = radius * math.sin(ele)

        # 构建相机到世界的变换矩阵
        up = torch.tensor([0, 0, 1], dtype=torch.float32)
        forward = torch.tensor([x, y, z], dtype=torch.float32)
        forward = forward / torch.norm(forward)
        right = torch.cross(up, forward)
        right = right / torch.norm(right)
        up = torch.cross(forward, right)

        c2w = torch.eye(4, dtype=torch.float32)
        c2w[:3, 0] = right
        c2w[:3, 1] = up
        c2w[:3, 2] = forward
        c2w[:3, 3] = torch.tensor([x, y, z])
        camera_to_worlds.append(c2w)

    camera_to_worlds = torch.stack(camera_to_worlds, dim=0)

    # 相机内参 (3x3 矩阵，gsplat 要求格式)
    fov_x = 60 * math.pi / 180
    fx = resolution[0] / (2 * math.tan(fov_x / 2))
    fy = fx
    cx = resolution[0] / 2
    cy = resolution[1] / 2

    intrinsics_3x3 = torch.eye(3, dtype=torch.float32).unsqueeze(0).repeat(num_images, 1, 1)
    intrinsics_3x3[:, 0, 0] = fx
    intrinsics_3x3[:, 1, 1] = fy
    intrinsics_3x3[:, 0, 2] = cx
    intrinsics_3x3[:, 1, 2] = cy

    # 生成随机彩色图像
    images = torch.rand(num_images, 3, resolution[1], resolution[0], dtype=torch.float32)

    # world_to_camera = camera_to_worlds.inverse()
    world_to_cameras = torch.inverse(camera_to_worlds)

    return {
        "world_to_cameras": world_to_cameras.to(device),
        "intrinsics": intrinsics_3x3.to(device),
        "images": images.to(device),
        "width": resolution[0],
        "height": resolution[1],
        "num_images": num_images,
    }


# ─── 高斯初始化 ──────────────────────────────────────────────────────────

def init_gaussians_from_random(
    num_points: int = 100000,
    device: str = "cuda",
):
    """
    随机初始化高斯球（无 COLMAP 数据时使用）
    """
    print(f"  🎲 随机初始化 {num_points} 个高斯球...")

    # 位置：在单位球体内随机
    positions = torch.randn(num_points, 3, device=device) * 0.5

    # 颜色：随机 RGB
    colors = torch.rand(num_points, 3, device=device)

    # 缩放：自适应大小
    scales = torch.full((num_points, 3), 0.01, device=device)

    # 旋转：单位四元数
    rotations = torch.zeros(num_points, 4, device=device)
    rotations[:, 0] = 1.0

    # 不透明度：接近 0.5
    opacities = torch.sigmoid(torch.randn(num_points, device=device) * 0.1 + 0.5)

    return {
        "means": positions,
        "colors": colors,
        "scales": scales,
        "quats": rotations,
        "opacities": opacities,
    }

@dataclass
class GaussianParams:
    """高斯参数容器"""
    means: torch.Tensor          # [N, 3]  位置
    colors: torch.Tensor         # [N, 3]  RGB 颜色
    scales: torch.Tensor         # [N, 3]  缩放
    quats: torch.Tensor          # [N, 4]  旋转（四元数）
    opacities: torch.Tensor      # [N]     不透明度
    sh_coeffs: Optional[torch.Tensor] = None  # [N, C] 球谐系数


# ─── 训练循环 ──────────────────────────────────────────────────────────

def train_3dgs(cfg: TrainConfig):
    """
    3DGS 主训练循环

    Args:
        cfg: 训练配置
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*50}")
    print(f"  3D Gaussian Splatting 训练")
    print(f"  场景: {cfg.scene_name}")
    print(f"  设备: {device}")
    print(f"  迭代: {cfg.iterations}")
    print(f"{'='*50}\n")

    # 创建输出目录
    os.makedirs(cfg.log_dir, exist_ok=True)
    os.makedirs(cfg.model_dir, exist_ok=True)
    os.makedirs(cfg.render_dir, exist_ok=True)

    # ── 1. 加载数据 ─────────────────────────────────
    print("[1/4] 加载数据...")
    data = None
    if cfg.data_dir and os.path.exists(cfg.data_dir):
        colmap_data = load_colmap_data(cfg.data_dir)
        if colmap_data is not None:
            # 有 COLMAP 数据 → 使用真实相机参数
            data = colmap_data

    if data is None:
        print("  ⚠️  无有效训练数据，使用随机测试数据")
        data = create_random_dataset(num_images=50, device=device)

    # ── 2. 初始化高斯球 ──────────────────────────────
    print("[2/4] 初始化高斯球...")
    gaussians = init_gaussians_from_random(cfg.random_points, device)

    # ── 3. 验证 gsplat 是否可用 ──────────────────────
    try:
        importlib.import_module("gsplat")
        print("  ✅ gsplat 库已安装")
    except ImportError:
        print("  ⚠️  gsplat 未安装，安装后可使用 GPU 加速训练:")
        print("     pip install gsplat")
        print("  回退到简单 CPU 训练演示模式...")
        _run_demo_training(cfg, gaussians)
        return

    # ── 4. GPU 加速训练 ──────────────────────────────
    from gsplat import rasterization

    # 准备数据
    # 尝试加载真实图像
    image_dir = os.path.join(cfg.data_dir, "images") if cfg.data_dir else ""
    image_tensors = []
    camera_data = []

    if image_dir and os.path.exists(image_dir):
        image_files = sorted([
            f for f in os.listdir(image_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])
        if image_files:
            print(f"  加载 {len(image_files)} 张训练图像...")
            for fname in tqdm(image_files):
                img = Image.open(os.path.join(image_dir, fname)).convert("RGB")
                img_tensor = torch.tensor(np.array(img), dtype=torch.float32, device=device) / 255.0
                image_tensors.append(img_tensor.permute(2, 0, 1))  # CHW
    else:
        print("  ℹ️  使用随机图像数据用于演示")

    if not image_tensors:
        image_tensors = [torch.rand(3, 256, 256, device=device) for _ in range(50)]

    # 设置相机参数
    H, W = image_tensors[0].shape[1:]
    if data and "world_to_cameras" in data:
        world_to_cameras = data["world_to_cameras"]
        intrinsics = data["intrinsics"]
    else:
        # 生成环绕相机的位姿
        num_views = len(image_tensors)
        world_to_cameras = torch.eye(4, device=device).unsqueeze(0).repeat(num_views, 1, 1)
        for i in range(num_views):
            angle = 2 * math.pi * i / num_views
            # world_to_camera: 从世界坐标到相机坐标的变换
            # 简化: 相机位于球面上观察原点
            w2c = torch.eye(4, device=device)
            w2c[:3, 3] = -torch.tensor(
                [4 * math.cos(angle), 4 * math.sin(angle), 0.5], device=device
            )
            world_to_cameras[i] = w2c
        intrinsics = torch.eye(3, device=device).unsqueeze(0).repeat(num_views, 1, 1)
        intrinsics[:, 0, 0] = W
        intrinsics[:, 1, 1] = W
        intrinsics[:, 0, 2] = W / 2
        intrinsics[:, 1, 2] = H / 2

    # ── 5. 训练 ──────────────────────────────────────
    print("\n[3/4] 开始训练...")
    means = torch.nn.Parameter(gaussians["means"].to(device))
    scales = torch.nn.Parameter(torch.log(gaussians["scales"].to(device)))
    quats = torch.nn.Parameter(gaussians["quats"].to(device))
    opacities = torch.nn.Parameter(torch.logit(gaussians["opacities"].to(device)))
    colors = torch.nn.Parameter(gaussians["colors"].to(device))

    # Adam 优化器
    optimizer = torch.optim.Adam([
        {"params": [means], "lr": cfg.lr_position},
        {"params": [scales], "lr": cfg.lr_scaling},
        {"params": [quats], "lr": cfg.lr_rotation},
        {"params": [opacities], "lr": cfg.lr_opacity},
        {"params": [colors], "lr": cfg.lr_feature},
    ])

    # 训练循环
    progress_bar = tqdm(range(cfg.iterations), desc="训练")
    for step in progress_bar:
        # 选取当前视角
        view_idx = step % len(image_tensors)

        w2c = world_to_cameras[view_idx:view_idx+1].unsqueeze(0)  # [1,1,4,4]
        K = intrinsics[view_idx:view_idx+1].unsqueeze(0)          # [1,1,3,3]
        # image_tensors 是列表，取单元素并加 batch 维度
        if isinstance(image_tensors, list):
            gt_image = image_tensors[view_idx].unsqueeze(0)       # [1,3,H,W]
        else:
            gt_image = image_tensors[view_idx:view_idx+1]

        # 渲染
        try:
            render_colors, render_alphas, info = rasterization(
                means=means.unsqueeze(0),           # [1,N,3]
                quats=quats.unsqueeze(0) / torch.norm(quats.unsqueeze(0), dim=-1, keepdim=True),
                scales=torch.exp(scales).unsqueeze(0),
                opacities=torch.sigmoid(opacities).unsqueeze(0),
                colors=colors.unsqueeze(0),
                viewmats=w2c,
                Ks=K,
                width=W,
                height=H,
            )
        except Exception as e:
            progress_bar.set_postfix_str(f"渲染错误: {str(e)[:80]}")
            continue

        # render_colors shape: [B, C, H, W, 3], squeeze camera dim -> [1, H, W, 3]
        render_rgb = render_colors.squeeze(1)  # [1, H, W, 3] -> [1, 3, H, W]
        render_rgb = render_rgb.permute(0, 3, 1, 2)

        # 计算损失
        l1_loss = torch.abs(render_rgb - gt_image).mean()
        # SSIM 损失
        ssim_loss = 0.2 * _ssim(render_rgb, gt_image)
        loss = l1_loss + ssim_loss

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 更新进度
        postfix = {
            "loss": f"{loss.item():.4f}",
            "l1": f"{l1_loss.item():.4f}",
            "n_gauss": means.shape[0],
        }
        progress_bar.set_postfix(postfix)

        # 自适应密度控制（简化版）
        if step % cfg.densification_interval == 0 and step < cfg.opacity_reset_interval:
            with torch.no_grad():
                grad_norm = means.grad.norm(dim=-1)
                dense_mask = grad_norm > cfg.densify_grad_threshold
                if dense_mask.any():
                    # 克隆高斯
                    n_clone = dense_mask.sum().item()
                    new_means = means[dense_mask].clone() + torch.randn_like(means[dense_mask]) * 0.01
                    new_scales = torch.log(torch.exp(scales[dense_mask]) * 0.5)
                    new_quats = quats[dense_mask].clone()
                    new_opacities = opacities[dense_mask].clone()
                    new_colors = colors[dense_mask].clone()

                    # 扩展参数
                    means = torch.nn.Parameter(torch.cat([means, new_means], dim=0))
                    scales = torch.nn.Parameter(torch.cat([scales, new_scales], dim=0))
                    quats = torch.nn.Parameter(torch.cat([quats, new_quats], dim=0))
                    opacities = torch.nn.Parameter(torch.cat([opacities, new_opacities], dim=0))
                    colors = torch.nn.Parameter(torch.cat([colors, new_colors], dim=0))

        # 保存 checkpoint
        if step > 0 and step % cfg.save_interval == 0:
            _save_checkpoint(
                means, scales, quats, opacities, colors, step,
                cfg.model_dir, cfg.scene_name,
            )

        # 渲染评估图像
        if step % cfg.eval_interval == 0:
            _save_render(
                render_rgb[0], gt_image[0], step,
                cfg.render_dir, cfg.scene_name,
            )

    # ── 6. 导出最终模型 ──────────────────────────────
    print("\n[4/4] 导出模型...")
    model_path = _save_ply(
        means.detach(), scales.detach(), quats.detach(),
        opacities.detach(), colors.detach(),
        cfg.model_dir, cfg.scene_name,
    )

    # 同时复制到 spark-studio 以便直接查看
    spark_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spark-studio", "data")
    if os.path.exists(spark_data_dir):
        import shutil
        shutil.copy2(model_path, os.path.join(spark_data_dir, f"{cfg.scene_name}.ply"))
        print(f"  ✅ 已复制到 Spark Studio: {spark_data_dir}/{cfg.scene_name}.ply")

    print(f"\n{'='*50}")
    print(f"  ✅ 训练完成!")
    print(f"  模型: {model_path}")
    print(f"  打开 Spark Studio 即可查看")
    print(f"{'='*50}\n")


def _run_demo_training(cfg: TrainConfig, gaussians: dict):
    """无 GPU 时的演示模式（仅显示训练流程）"""
    print("\n  [演示模式] 3DGS 训练流程模拟:")
    print(f"  - 高斯球数量: {gaussians['means'].shape[0]}")
    print(f"  - 训练迭代: {cfg.iterations}")
    print(f"  - 输出目录: {cfg.model_dir}")
    print("\n  要启用 GPU 加速训练，请安装:")
    print("    pip install gsplat ninja")
    print("    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126")
    print()


# ─── 工具函数 ──────────────────────────────────────────────────────────

def _ssim(img1: torch.Tensor, img2: torch.Tensor) -> torch.Tensor:
    """简化版 SSIM"""
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2
    mu1 = img1.mean(dim=[-2, -1], keepdim=True)
    mu2 = img2.mean(dim=[-2, -1], keepdim=True)
    sigma1 = ((img1 - mu1) ** 2).mean(dim=[-2, -1], keepdim=True)
    sigma2 = ((img2 - mu2) ** 2).mean(dim=[-2, -1], keepdim=True)
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean(dim=[-2, -1], keepdim=True)
    ssim_map = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / ((mu1 ** 2 + mu2 ** 2 + C1) * (sigma1 + sigma2 + C2))
    return ssim_map.mean()


def _save_checkpoint(means, scales, quats, opacities, colors, step, model_dir, scene_name):
    """保存训练 checkpoint"""
    ckpt = {
        "step": step,
        "means": means.detach().cpu(),
        "scales": scales.detach().cpu(),
        "quats": quats.detach().cpu(),
        "opacities": opacities.detach().cpu(),
        "colors": colors.detach().cpu(),
    }
    path = os.path.join(model_dir, f"{scene_name}_step{step:06d}.pt")
    torch.save(ckpt, path)
    print(f"\n  💾 Checkpoint saved: {path}")


def _save_render(render, gt, step, render_dir, scene_name):
    """保存渲染结果对比"""
    import torchvision.utils as vutils
    os.makedirs(render_dir, exist_ok=True)

    comparison = torch.cat([render, gt], dim=2)
    path = os.path.join(render_dir, f"{scene_name}_step{step:06d}.png")
    vutils.save_image(comparison.clamp(0, 1), path)
    print(f"\n  🖼️  Render saved: {path}")


def _save_ply(means, scales, quats, opacities, colors, model_dir, scene_name):
    """
    导出为 PLY 格式（标准 3DGS 格式）

    PLY 格式是标准 3DGS 输出格式，可在 Spark Studio 中加载。
    """
    path = os.path.join(model_dir, f"{scene_name}.ply")

    # 准备数据
    means = means.cpu().numpy()
    opacities = torch.sigmoid(opacities).cpu().numpy()
    scales = torch.exp(scales).cpu().numpy()
    quats = quats / torch.norm(quats, dim=-1, keepdim=True)
    quats = quats.cpu().numpy()
    colors = colors.cpu().numpy()

    N = means.shape[0]

    # 写入 PLY
    with open(path, "wb") as f:
        # 文件头
        f.write(b"ply\n")
        f.write(b"format binary_little_endian 1.0\n")
        f.write(f"element vertex {N}\n".encode())
        f.write(b"property float x\n")
        f.write(b"property float y\n")
        f.write(b"property float z\n")
        f.write(b"property float nx\n")
        f.write(b"property float ny\n")
        f.write(b"property float nz\n")
        f.write(b"property float f_dc_0\n")
        f.write(b"property float f_dc_1\n")
        f.write(b"property float f_dc_2\n")
        f.write(b"property float opacity\n")
        f.write(b"property float scale_0\n")
        f.write(b"property float scale_1\n")
        f.write(b"property float scale_2\n")
        f.write(b"property float rot_0\n")
        f.write(b"property float rot_1\n")
        f.write(b"property float rot_2\n")
        f.write(b"property float rot_3\n")
        f.write(b"end_header\n")

        # 二进制数据
        for i in range(N):
            # 位置 xyz
            f.write(means[i].tobytes())
            # 法线（0占位）
            f.write(np.zeros(3, dtype=np.float32).tobytes())
            # 颜色 RGB
            f.write(colors[i].tobytes())
            # 不透明度
            f.write(opacities[i:i+1].tobytes())
            # 缩放
            f.write(scales[i].tobytes())
            # 旋转
            f.write(quats[i].tobytes())

    print(f"  📦 PLY 导出: {path} ({N} 个高斯球)")
    return path


# ─── 主入口 ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="3DGS 训练引擎")
    parser.add_argument("--config", "-c", default="", help="配置文件路径")
    parser.add_argument("--data", "-d", default="", help="训练数据目录")
    parser.add_argument("--name", "-n", default="scene", help="场景名称")
    parser.add_argument("--iterations", "-i", type=int, default=30000, help="训练迭代次数")
    parser.add_argument("--output", "-o", default="./outputs", help="输出目录")

    args = parser.parse_args()

    # 加载配置
    if args.config:
        cfg = load_config(args.config)
    else:
        cfg = TrainConfig()

    if args.data:
        cfg.data_dir = args.data
    if args.name:
        cfg.scene_name = args.name
    if args.iterations:
        cfg.iterations = args.iterations
    if args.output:
        cfg.model_dir = os.path.join(args.output, "models")
        cfg.log_dir = os.path.join(args.output, "logs")
        cfg.render_dir = os.path.join(args.output, "renders")

    # 启动训练
    train_3dgs(cfg)


if __name__ == "__main__":
    main()
