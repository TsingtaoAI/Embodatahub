"""
多模态对齐专用模型管理

提供 ONNX 模型的下载、缓存和推理接口。
支持 CLIP (视觉-触觉对齐)、CLAP (音频对齐) 等模型。

使用方式:
    from robot_data_studio.quality.multimodal_models import (
        get_clip_encoder,
        get_clap_encoder,
        ModelCache,
        list_available_models,
    )
"""

from .clip_encoder import CLIPEncoder, get_clip_encoder
from .model_cache import ModelCache, list_available_models

__all__ = [
    "CLIPEncoder",
    "get_clip_encoder",
    "list_available_models",
    "ModelCache",
]
