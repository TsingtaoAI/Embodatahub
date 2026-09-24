"""
CLIP 视觉编码器 — 用于跨模态语义对齐

将图像帧编码为 512 维归一化 embedding 向量。
触觉图像 (GelSight) 也通过同一编码器处理，实现视觉-触觉共享嵌入空间。

优先使用 ONNX Runtime 推理，回退到 transformers 库。

使用方式:
    encoder = get_clip_encoder()
    embeddings = encoder.encode(images)  # (N, 512)
    similarity = embeddings @ embeddings.T  # 余弦相似度矩阵
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import numpy.typing as npt

from .model_cache import ModelCache

logger = logging.getLogger("rslstudio.multimodal.clip")

_MODEL_ID = "clip-vit-base-patch32"


class CLIPEncoder:
    """CLIP ViT-B/32 视觉编码器"""

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        device: str = "cpu",
    ) -> None:
        """
        Args:
            model_path: ONNX 模型文件路径（为空则自动下载）
            device: 推理设备 ("cpu" 或 "cuda")
        """
        self.device = device
        self._session = None
        self._processor = None
        self._embedding_dim = 512

        # 解析模型路径
        if model_path is None:
            cache = ModelCache()
            if not cache.is_cached(_MODEL_ID):
                logger.info("CLIP 模型未缓存，尝试自动下载...")
                try:
                    cache.download(_MODEL_ID)
                except Exception as exc:
                    logger.warning("自动下载 CLIP 模型失败: %s", exc)
            model_path = cache.get_path(_MODEL_ID)

        self.model_path = Path(model_path) if model_path else None

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    @property
    def is_ready(self) -> bool:
        """模型是否已加载并可用"""
        return self._session is not None

    def load(self) -> None:
        """加载 ONNX 模型到内存"""
        if self._session is not None:
            return

        if self.model_path and self.model_path.exists():
            self._load_onnx()
        else:
            self._load_fallback()

    def _load_onnx(self) -> None:
        """从 ONNX 文件加载"""
        try:
            import onnxruntime as ort

            providers = (
                ["CUDAExecutionProvider", "CPUExecutionProvider"]
                if self.device == "cuda"
                else ["CPUExecutionProvider"]
            )
            self._session = ort.InferenceSession(
                str(self.model_path), providers=providers
            )
            logger.info("CLIP ONNX 模型已加载: %s", self.model_path)
        except ImportError:
            logger.warning("onnxruntime 未安装，回退到 transformers")
            self._load_fallback()

    def _load_fallback(self) -> None:
        """回退到 HuggingFace transformers"""
        try:
            from transformers import CLIPModel, CLIPProcessor

            model_name = "openai/clip-vit-base-patch32"
            self._hf_model = CLIPModel.from_pretrained(model_name)
            self._processor = CLIPProcessor.from_pretrained(model_name)
            self._session = "transformers"  # 标记为 transformers 模式
            logger.info("CLIP transformers 模型已加载: %s", model_name)
        except ImportError:
            raise RuntimeError(
                "无法加载 CLIP 模型。请安装 onnxruntime 或 transformers:\n"
                "  pip install onnxruntime   # 推荐 (轻量)\n"
                "  pip install transformers  # 备选"
            ) from None

    def encode(
        self,
        images: npt.NDArray[np.uint8],
        batch_size: int = 8,
    ) -> npt.NDArray[np.float32]:
        """将图像批次编码为归一化 embedding 向量

        Args:
            images: (N, H, W, 3) uint8 RGB 图像数组
            batch_size: 批处理大小

        Returns:
            (N, 512) float32 归一化 embedding 矩阵
        """
        if self._session is None:
            self.load()

        n = len(images)
        embeddings = np.zeros((n, self._embedding_dim), dtype=np.float32)

        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            batch = images[start:end]

            if self._session == "transformers":
                emb = self._encode_transformers(batch)
            else:
                emb = self._encode_onnx(batch)

            embeddings[start:end] = emb

        # L2 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-8)
        embeddings = embeddings / norms

        return embeddings

    def _encode_onnx(
        self, batch: npt.NDArray[np.uint8]
    ) -> npt.NDArray[np.float32]:
        """ONNX 推理"""
        # 预处理: resize 到 224x224, 归一化
        processed = self._preprocess_clip(batch)
        outputs = self._session.run(
            None, {"pixel_values": processed.astype(np.float32)}
        )
        return outputs[0].astype(np.float32)

    def _encode_transformers(
        self, batch: npt.NDArray[np.uint8]
    ) -> npt.NDArray[np.float32]:
        """Transformers 推理"""
        from PIL import Image

        pil_images = [Image.fromarray(img) for img in batch]
        inputs = self._processor(
            images=pil_images, return_tensors="pt", padding=True
        )
        outputs = self._hf_model.get_image_features(**inputs)
        return outputs.detach().cpu().numpy().astype(np.float32)

    @staticmethod
    def _preprocess_clip(
        images: npt.NDArray[np.uint8],
        target_size: int = 224,
    ) -> npt.NDArray[np.float32]:
        """CLIP 标准预处理: resize → center crop → normalize"""
        from PIL import Image

        mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
        std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

        n = len(images)
        processed = np.zeros((n, 3, target_size, target_size), dtype=np.float32)

        for i, img in enumerate(images):
            pil_img = Image.fromarray(img).convert("RGB")
            # Resize shortest side to target_size, center crop
            w, h = pil_img.size
            scale = target_size / min(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.BILINEAR)
            # Center crop
            left = (new_w - target_size) // 2
            top = (new_h - target_size) // 2
            pil_img = pil_img.crop((left, top, left + target_size, top + target_size))
            # To numpy and normalize
            arr = np.array(pil_img, dtype=np.float32) / 255.0
            arr = (arr - mean) / std
            processed[i] = arr.transpose(2, 0, 1)

        return processed

    def similarity_matrix(
        self,
        modality_a: npt.NDArray[np.uint8],
        modality_b: npt.NDArray[np.uint8],
    ) -> npt.NDArray[np.float32]:
        """计算两组图像的跨模态余弦相似度矩阵

        Args:
            modality_a: (N, H, W, 3) 模态A 图像
            modality_b: (M, H, W, 3) 模态B 图像

        Returns:
            (N, M) 余弦相似度矩阵
        """
        emb_a = self.encode(modality_a)
        emb_b = self.encode(modality_b)
        return emb_a @ emb_b.T


# ── 全局单例 ──

_encoder: Optional[CLIPEncoder] = None


def get_clip_encoder(
    model_path: Optional[str | Path] = None,
    device: str = "cpu",
) -> CLIPEncoder:
    """获取全局 CLIP 编码器实例（懒加载）"""
    global _encoder
    if _encoder is None:
        _encoder = CLIPEncoder(model_path=model_path, device=device)
    return _encoder
