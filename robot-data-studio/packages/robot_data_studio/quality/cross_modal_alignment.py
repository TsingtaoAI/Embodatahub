"""
跨模态语义对齐 — 使用 CLIP/DTW 实现不同模态数据的语义关联

将视觉帧、触觉图像、关节数据等不同模态的数据进行语义对齐，
输出跨模态相似度矩阵和对齐路径。

使用方式:
    aligner = CrossModalAligner(config)
    result = aligner.align_vision_tactile(video_frames, tactile_frames)
    # result.similarity_matrix: (T_vis, T_tac) 余弦相似度
    # result.alignment_path: DTW 最优路径
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import numpy.typing as npt

logger = logging.getLogger("rslstudio.multimodal.cross_modal")


@dataclass
class CrossModalConfig:
    """跨模态对齐配置"""

    enable_vision_tactile: bool = True
    """启用视觉-触觉对齐"""
    enable_audio_text: bool = False
    """启用音频-文本对齐"""
    enable_action_vision: bool = True
    """启用动作-视觉时序一致性"""

    similarity_threshold: float = 0.6
    """相似度阈值 [0, 1]"""
    dtw_radius: int = 10
    """DTW 搜索半径 (Sakoe-Chiba band)"""

    device: str = "cpu"
    """推理设备"""


@dataclass
class AlignmentPath:
    """DTW 对齐路径"""

    indices: list[tuple[int, int]]
    """对齐索引对 [(i, j), ...]"""
    total_cost: float
    normalized_cost: float
    """归一化代价 [0, 1]"""


@dataclass
class CrossModalResult:
    """跨模态对齐结果"""

    modality_pair: str
    """模态对名称，如 "vision_tactile" """
    source_count: int
    target_count: int

    similarity_matrix: npt.NDArray[np.float32]
    """源-目标余弦相似度矩阵 (N, M)"""
    alignment_path: Optional[AlignmentPath] = None
    """DTW 最优对齐路径"""
    mean_similarity: float = 0.0
    """平均相似度"""
    alignment_score: float = 0.0
    """对齐质量得分 [0, 1]"""

    matched_pairs: list[dict] = field(default_factory=list)
    """匹配对详情 [{source_idx, target_idx, similarity, is_aligned}, ...]"""


@dataclass
class MultiModalAlignmentReport:
    """多模态对齐综合报告"""

    episode_index: int
    modality_pairs: list[str]
    results: dict[str, CrossModalResult]
    overall_score: float
    """综合对齐得分 [0, 1]"""
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class CrossModalAligner:
    """跨模态语义对齐器"""

    def __init__(self, config: Optional[CrossModalConfig] = None) -> None:
        self.config = config or CrossModalConfig()
        self._clip_encoder = None

    @property
    def clip_encoder(self):
        if self._clip_encoder is None:
            from .multimodal_models.clip_encoder import get_clip_encoder

            self._clip_encoder = get_clip_encoder(device=self.config.device)
        return self._clip_encoder

    def align_vision_tactile(
        self,
        video_frames: npt.NDArray[np.uint8],
        tactile_frames: npt.NDArray[np.uint8],
        video_timestamps: Optional[list[float]] = None,
        tactile_timestamps: Optional[list[float]] = None,
    ) -> CrossModalResult:
        """对齐视觉帧与触觉帧

        Args:
            video_frames: (T_vis, H, W, 3) 视频帧
            tactile_frames: (T_tac, H_t, W_t, 3) 触觉图像
            video_timestamps: 可选视频时间戳
            tactile_timestamps: 可选触觉时间戳

        Returns:
            跨模态对齐结果
        """
        n_vis = len(video_frames)
        n_tac = len(tactile_frames)

        if n_vis == 0 or n_tac == 0:
            return CrossModalResult(
                modality_pair="vision_tactile",
                source_count=n_vis,
                target_count=n_tac,
                similarity_matrix=np.zeros((max(n_vis, 1), max(n_tac, 1)), dtype=np.float32),
                issues=["视频帧或触觉帧为空，无法对齐"],
            )

        # 编码
        logger.info("编码 %d 视觉帧...", n_vis)
        vis_emb = self.clip_encoder.encode(video_frames)  # (T_vis, 512)
        logger.info("编码 %d 触觉帧...", n_tac)
        tac_emb = self.clip_encoder.encode(tactile_frames)  # (T_tac, 512)

        # 余弦相似度矩阵
        similarity = vis_emb @ tac_emb.T  # (T_vis, T_tac)

        # DTW 最优路径
        path = _compute_dtw_path(similarity, radius=self.config.dtw_radius)

        # 匹配对
        mean_sim = float(np.mean(np.max(similarity, axis=1)))
        alignment_score = _compute_alignment_score(similarity, path)

        matched_pairs = _extract_matched_pairs(
            similarity, path, threshold=self.config.similarity_threshold
        )

        # 检测问题
        issues: list[str] = []
        if mean_sim < self.config.similarity_threshold:
            issues.append(
                f"视觉-触觉平均相似度 {mean_sim:.2f} 低于阈值 "
                f"{self.config.similarity_threshold}"
            )

        return CrossModalResult(
            modality_pair="vision_tactile",
            source_count=n_vis,
            target_count=n_tac,
            similarity_matrix=similarity,
            alignment_path=path,
            mean_similarity=mean_sim,
            alignment_score=alignment_score,
            matched_pairs=matched_pairs,
        )

    def align_action_vision(
        self,
        joint_positions: npt.NDArray[np.float32],
        video_timestamps: list[float],
        joint_timestamps: list[float],
    ) -> CrossModalResult:
        """对齐关节轨迹与视频帧时序

        使用 DTW 直接对齐时序数据，无需模型推理。

        Args:
            joint_positions: (T_joint, D) 关节位置
            video_timestamps: 视频帧时间戳
            joint_timestamps: 关节数据时间戳

        Returns:
            对齐结果
        """
        n_vis = len(video_timestamps)
        n_joint = len(joint_timestamps)

        if n_vis < 2 or n_joint < 2:
            return CrossModalResult(
                modality_pair="action_vision",
                source_count=n_joint,
                target_count=n_vis,
                similarity_matrix=np.zeros((max(n_joint, 1), max(n_vis, 1)), dtype=np.float32),
                issues=["数据点不足，无法对齐"],
            )

        # 计算关节速度 (一阶差分)
        velocities = np.diff(joint_positions, axis=0)
        vel_magnitude = np.linalg.norm(velocities, axis=1)

        # 插值关节速度到视频时间戳
        from scipy.interpolate import interp1d

        joint_mid_ts = (np.array(joint_timestamps[:-1]) + np.array(joint_timestamps[1:])) / 2
        try:
            interp = interp1d(
                joint_mid_ts, vel_magnitude,
                kind="linear", bounds_error=False, fill_value=0.0,
            )
            vis_vel = interp(np.array(video_timestamps))
        except ValueError:
            vis_vel = np.zeros(n_vis)

        # 构建"相似度"矩阵：关节速度接近 → 高相似度
        # 实际用 1 / (1 + |v_joint - v_vis|) 量化
        similarity = np.zeros((n_joint, n_vis), dtype=np.float32)
        for i in range(n_joint):
            jv = float(vel_magnitude[min(i, len(vel_magnitude) - 1)])
            similarity[i, :] = 1.0 / (1.0 + np.abs(np.full(n_vis, jv) - vis_vel))

        path = _compute_dtw_path(similarity, radius=self.config.dtw_radius)
        mean_sim = float(np.mean(np.max(similarity, axis=1)))
        alignment_score = _compute_alignment_score(similarity, path)

        return CrossModalResult(
            modality_pair="action_vision",
            source_count=n_joint,
            target_count=n_vis,
            similarity_matrix=similarity,
            alignment_path=path,
            mean_similarity=mean_sim,
            alignment_score=alignment_score,
        )

    def run_full_alignment(
        self,
        episode_index: int,
        video_frames: Optional[npt.NDArray[np.uint8]] = None,
        tactile_frames: Optional[npt.NDArray[np.uint8]] = None,
        joint_positions: Optional[npt.NDArray[np.float32]] = None,
        video_timestamps: Optional[list[float]] = None,
        tactile_timestamps: Optional[list[float]] = None,
        joint_timestamps: Optional[list[float]] = None,
    ) -> MultiModalAlignmentReport:
        """运行完整的多模态对齐流程

        Returns:
            综合对齐报告
        """
        results: dict[str, CrossModalResult] = {}
        issues: list[str] = []
        recommendations: list[str] = []
        modality_pairs: list[str] = []

        # ── 视觉-触觉对齐 ──
        if (
            self.config.enable_vision_tactile
            and video_frames is not None
            and tactile_frames is not None
            and len(video_frames) > 0
            and len(tactile_frames) > 0
        ):
            try:
                result = self.align_vision_tactile(
                    video_frames, tactile_frames,
                    video_timestamps, tactile_timestamps,
                )
                results["vision_tactile"] = result
                modality_pairs.append("vision_tactile")

                if result.alignment_score < 0.5:
                    issues.append(f"视觉-触觉对齐度低 ({result.alignment_score:.2f})")
                    recommendations.append(
                        "建议检查触觉传感器安装位置，或增加标定数据"
                    )
            except Exception as exc:
                logger.error("视觉-触觉对齐失败: %s", exc)
                issues.append(f"视觉-触觉对齐失败: {exc}")

        # ── 动作-视觉对齐 ──
        if (
            self.config.enable_action_vision
            and joint_positions is not None
            and video_timestamps is not None
            and joint_timestamps is not None
            and len(video_timestamps) > 1
            and len(joint_timestamps) > 1
        ):
            try:
                result = self.align_action_vision(
                    joint_positions, video_timestamps, joint_timestamps,
                )
                results["action_vision"] = result
                modality_pairs.append("action_vision")

                if result.alignment_score < 0.5:
                    issues.append(f"动作-视觉对齐度低 ({result.alignment_score:.2f})")
                    recommendations.append(
                        "建议检查机器人关节编码器与相机的时钟同步"
                    )
            except Exception as exc:
                logger.error("动作-视觉对齐失败: %s", exc)
                issues.append(f"动作-视觉对齐失败: {exc}")

        # ── 综合评分 ──
        scores = [r.alignment_score for r in results.values()]
        overall_score = float(np.mean(scores)) if scores else 0.0

        return MultiModalAlignmentReport(
            episode_index=episode_index,
            modality_pairs=modality_pairs,
            results=results,
            overall_score=overall_score,
            issues=issues,
            recommendations=recommendations,
        )


# ── 内部函数 ────────────────────────────────────────────────────────────

def _compute_dtw_path(
    similarity: npt.NDArray[np.float32],
    radius: int = 10,
) -> AlignmentPath:
    """使用 DTW 计算最优对齐路径

    将余弦相似度转换为距离矩阵后运行 DTW。
    """
    try:
        from dtaidistance import dtw
        # 距离 = 1 - 相似度
        distance = 1.0 - similarity.astype(np.float64)
        dtw_path = dtw.warping_path(distance, window=radius)
        indices = [(int(i), int(j)) for i, j in dtw_path]
        total_cost = sum(float(distance[i, j]) for i, j in indices)
        normalized_cost = total_cost / max(len(indices), 1)
        return AlignmentPath(
            indices=indices,
            total_cost=total_cost,
            normalized_cost=normalized_cost,
        )
    except ImportError:
        pass

    # 无 dtaidistance 时的简化实现
    n, m = similarity.shape
    # 贪心路径: 每行取最大值所在列
    simple_path: list[tuple[int, int]] = []
    for i in range(n):
        j = int(np.argmax(similarity[i]))
        simple_path.append((i, j))
    total_cost = float(np.sum(1.0 - similarity[i, j] for i, j in simple_path))
    return AlignmentPath(
        indices=simple_path,
        total_cost=total_cost,
        normalized_cost=total_cost / max(len(simple_path), 1),
    )


def _compute_alignment_score(
    similarity: npt.NDArray[np.float32],
    path: AlignmentPath,
) -> float:
    """综合计算对齐质量得分"""
    # 1 - 归一化 DTW 代价
    dtw_score = max(0.0, 1.0 - path.normalized_cost)
    # 平均最大相似度
    avg_max_sim = float(np.mean(np.max(similarity, axis=1)))
    # 综合
    return round(float(0.5 * dtw_score + 0.5 * avg_max_sim), 4)


def _extract_matched_pairs(
    similarity: npt.NDArray[np.float32],
    path: AlignmentPath,
    threshold: float = 0.6,
) -> list[dict]:
    """从对齐路径中提取匹配对"""
    pairs = []
    for i, j in path.indices:
        sim = float(similarity[i, j])
        pairs.append({
            "source_idx": i,
            "target_idx": j,
            "similarity": round(sim, 4),
            "is_aligned": sim >= threshold,
        })
    return pairs
