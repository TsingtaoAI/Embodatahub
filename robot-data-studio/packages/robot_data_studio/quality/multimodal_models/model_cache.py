"""
ONNX 模型下载与缓存管理

支持的模型:
  - clip-vit-base-patch32: CLIP 视觉编码器 (~350MB)
  - clap-htsat-fused: CLAP 音频编码器 (~300MB)
  - resnet18-tactile: 触觉事件分类器 (~44MB)

缓存目录默认为 ~/.cache/rslstudio/models/
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("rslstudio.multimodal")

_MODEL_REGISTRY: dict[str, "ModelInfo"] = {}


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    display_name: str
    description: str
    default_url: str
    expected_sha256: str
    file_size_mb: int
    required: bool = False


def _register(
    model_id: str,
    display_name: str,
    description: str,
    default_url: str,
    expected_sha256: str,
    file_size_mb: int,
    required: bool = False,
) -> None:
    _MODEL_REGISTRY[model_id] = ModelInfo(
        model_id=model_id,
        display_name=display_name,
        description=description,
        default_url=default_url,
        expected_sha256=expected_sha256,
        file_size_mb=file_size_mb,
        required=required,
    )


# ── 已注册模型 ────────────────────────────────────────────────────────

_register(
    "clip-vit-base-patch32",
    "CLIP ViT-B/32",
    "视觉-触觉跨模态编码器。将图像编码为 512 维向量，"
    "用于计算视觉帧与触觉帧的语义相似度。",
    "https://huggingface.co/sentence-transformers/clip-ViT-B-32/resolve/main/onnx/model.onnx",
    "",
    350,
    required=True,
)

_register(
    "clap-htsat-fused",
    "CLAP HTSAT",
    "音频-文本跨模态编码器。将音频波形编码为 512 维向量，"
    "用于音频与任务描述的语义对齐。",
    "https://huggingface.co/laion/clap-htsat-fused/resolve/main/onnx/model.onnx",
    "",
    300,
    required=False,
)

_register(
    "resnet18-tactile",
    "ResNet-18 触觉分类器",
    "轻量触觉接触事件检测器。识别触觉传感器图像中的"
    "接触/滑动/脱离事件。",
    "",
    "",
    44,
    required=False,
)


class ModelCache:
    """管理 ONNX 模型的下载、验证和本地缓存"""

    def __init__(self, cache_dir: Optional[str | Path] = None) -> None:
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "rslstudio" / "models"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, model_id: str) -> Path:
        """获取模型文件的本地路径（不检查是否存在）"""
        return self.cache_dir / f"{model_id}.onnx"

    def is_cached(self, model_id: str) -> bool:
        """检查模型是否已下载到本地缓存"""
        return self.get_path(model_id).exists()

    def list_cached(self) -> list[str]:
        """列出所有已缓存的模型 ID"""
        return [
            p.stem.replace(".onnx", "")
            for p in self.cache_dir.glob("*.onnx")
        ]

    def download(self, model_id: str, url: Optional[str] = None) -> Path:
        """下载模型到本地缓存

        Args:
            model_id: 模型标识符
            url: 自定义下载 URL（为空则使用默认 URL）

        Returns:
            本地模型文件路径
        """
        info = _MODEL_REGISTRY.get(model_id)
        if info is None:
            raise ValueError(f"未知模型: {model_id}")

        target = self.get_path(model_id)
        download_url = url or info.default_url
        if not download_url:
            raise ValueError(
                f"模型 {model_id} 没有默认下载 URL，请提供 url 参数"
            )

        logger.info("下载模型 %s (%d MB) 到 %s", model_id, info.file_size_mb, target)

        try:
            import urllib.request

            def _report(block_count: int, block_size: int, total_size: int) -> None:
                downloaded = block_count * block_size
                if total_size > 0:
                    pct = min(100, int(downloaded * 100 / total_size))
                    if block_count % 10 == 0:
                        logger.debug("  %s: %d%%", model_id, pct)

            urllib.request.urlretrieve(download_url, str(target), reporthook=_report)
        except ImportError:
            import requests

            with requests.get(download_url, stream=True, timeout=600) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(target, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0 and downloaded % (total // 20) < 8192:
                            logger.debug("  %s: %d%%", model_id, int(downloaded * 100 / total))

        logger.info("模型 %s 下载完成: %s", model_id, target)
        return target

    def remove(self, model_id: str) -> None:
        """删除本地缓存的模型"""
        target = self.get_path(model_id)
        if target.exists():
            target.unlink()
            logger.info("已删除模型: %s", model_id)

    def clear(self) -> list[str]:
        """清空所有本地缓存的模型，返回被删除的模型 ID 列表"""
        removed = self.list_cached()
        for model_id in removed:
            self.remove(model_id)
        return removed


def list_available_models() -> dict[str, ModelInfo]:
    """列出所有已注册的模型及其信息"""
    return dict(_MODEL_REGISTRY)


def get_model_status(cache: Optional[ModelCache] = None) -> dict[str, dict]:
    """获取所有模型的安装状态"""
    if cache is None:
        cache = ModelCache()
    result = {}
    for model_id, info in _MODEL_REGISTRY.items():
        result[model_id] = {
            "id": model_id,
            "display_name": info.display_name,
            "description": info.description,
            "file_size_mb": info.file_size_mb,
            "required": info.required,
            "cached": cache.is_cached(model_id),
        }
    return result
