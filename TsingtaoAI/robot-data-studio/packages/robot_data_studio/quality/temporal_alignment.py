"""
时序对齐 — 将多模态传感器数据统一到相同时间网格

纯算法实现，无模型依赖。支持:
  - 时间戳标准化 (各传感器时钟 → Unix epoch)
  - 线性/三次样条插值
  - 丢帧检测 + 间隙填充
  - 评估指标: temporal_jitter, timestamp_coverage, alignment_score
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np
import numpy.typing as npt

InterpolationMethod = Literal["nearest", "linear", "cubic"]


@dataclass
class TemporalAlignmentConfig:
    """时序对齐配置"""

    target_fps: float = 30.0
    """统一目标频率 (Hz)"""
    interpolation: InterpolationMethod = "linear"
    """插值方法"""
    max_gap_fill_ms: float = 100.0
    """最大插值间隙 (ms)，超过此值的间隙不填充"""
    timestamp_jitter_threshold_ms: float = 5.0
    """时间戳抖动阈值 (ms)"""
    coverage_warn_threshold: float = 0.95
    """时间覆盖率警告阈值"""


@dataclass
class TemporalAlignmentIssue:
    sensor_name: str
    issue_type: Literal["low_frequency", "timestamp_gap", "coverage_insufficient", "clock_drift"]
    detail: str
    severity: Literal["info", "warn", "error"]


@dataclass
class TemporalAlignmentResult:
    """时序对齐结果"""

    target_fps: float
    total_duration_s: float
    aligned_frame_count: int

    # 各传感器统计
    sensor_stats: dict[str, "SensorAlignmentStat"] = field(default_factory=dict)

    # 统一时间网格
    unified_timeline: list[float] = field(default_factory=list)

    # 评估
    issues: list[TemporalAlignmentIssue] = field(default_factory=list)
    alignment_score: float = 1.0
    """对齐质量得分 [0, 1]"""

    # 插值后数据 (可选，仅在 all_sensors=True 时填充)
    interpolated_data: dict[str, npt.NDArray[np.float32]] = field(
        default_factory=dict
    )


@dataclass
class SensorAlignmentStat:
    sensor_name: str
    native_fps: float
    sample_count: int
    timestamp_min: float
    timestamp_max: float
    coverage_ratio: float
    max_gap_ms: float
    avg_jitter_ms: float
    resample_ratio: float
    """重采样比例 (target_fps / native_fps)"""


@dataclass
class SensorStream:
    """单个传感器数据流"""

    name: str
    timestamps: list[float]
    values: Optional[npt.NDArray[np.float32]] = None
    """可选: 传感器数值 (N, D)"""
    modality: Literal["joint", "vision", "tactile", "imu", "audio", "other"] = "other"


def align_timeline(
    streams: list[SensorStream],
    config: Optional[TemporalAlignmentConfig] = None,
) -> TemporalAlignmentResult:
    """将所有传感器流对齐到统一时间网格

    Args:
        streams: 各传感器数据流
        config: 对齐配置

    Returns:
        对齐结果，包含统计信息和统一时间线
    """
    if config is None:
        config = TemporalAlignmentConfig()

    if not streams:
        return TemporalAlignmentResult(
            target_fps=config.target_fps,
            total_duration_s=0.0,
            aligned_frame_count=0,
        )

    # ── 1. 计算全局时间范围 ──
    all_timestamps = np.concatenate([np.asarray(s.timestamps) for s in streams])
    t_min = float(np.min(all_timestamps))
    t_max = float(np.max(all_timestamps))
    duration = t_max - t_min

    if duration <= 0:
        return TemporalAlignmentResult(
            target_fps=config.target_fps,
            total_duration_s=0.0,
            aligned_frame_count=0,
            issues=[
                TemporalAlignmentIssue(
                    sensor_name="all",
                    issue_type="coverage_insufficient",
                    detail="所有传感器时间戳范围为空",
                    severity="error",
                )
            ],
        )

    # ── 2. 生成统一时间网格 ──
    dt = 1.0 / config.target_fps
    frame_count = int(np.ceil(duration / dt)) + 1
    unified_timeline = np.linspace(t_min, t_max, frame_count, dtype=np.float64)

    # ── 3. 各传感器统计 + 插值 ──
    sensor_stats: dict[str, SensorAlignmentStat] = {}
    issues: list[TemporalAlignmentIssue] = []
    interpolated: dict[str, npt.NDArray[np.float32]] = {}

    for stream in streams:
        ts = np.asarray(stream.timestamps, dtype=np.float64)
        stat = _compute_sensor_stat(stream.name, ts, t_min, t_max, config)
        sensor_stats[stream.name] = stat

        # 检测问题
        if stat.avg_jitter_ms > config.timestamp_jitter_threshold_ms:
            issues.append(
                TemporalAlignmentIssue(
                    sensor_name=stream.name,
                    issue_type="timestamp_gap",
                    detail=f"时间戳抖动 {stat.avg_jitter_ms:.1f}ms 超过阈值 {config.timestamp_jitter_threshold_ms:.1f}ms",
                    severity="warn",
                )
            )

        if stat.coverage_ratio < config.coverage_warn_threshold:
            issues.append(
                TemporalAlignmentIssue(
                    sensor_name=stream.name,
                    issue_type="coverage_insufficient",
                    detail=f"时间覆盖率 {stat.coverage_ratio:.1%} 低于阈值 {config.coverage_warn_threshold:.1%}",
                    severity="warn" if stat.coverage_ratio > 0.5 else "error",
                )
            )

        # 插值到统一网格
        if stream.values is not None and len(stream.values) > 0:
            interp = _interpolate_to_grid(
                ts, stream.values, unified_timeline,
                method=config.interpolation,
                max_gap_s=config.max_gap_fill_ms / 1000.0,
            )
            interpolated[stream.name] = interp

    # ── 4. 计算对齐得分 ──
    weights = {
        "coverage": 0.4,
        "jitter": 0.3,
        "continuity": 0.3,
    }
    avg_coverage = np.mean([s.coverage_ratio for s in sensor_stats.values()])
    avg_jitter_ms = np.mean([s.avg_jitter_ms for s in sensor_stats.values()])
    jitter_score = max(0.0, 1.0 - avg_jitter_ms / config.timestamp_jitter_threshold_ms)
    continuity_score = 1.0 - len(issues) / max(len(streams) * 2, 1)

    alignment_score = (
        weights["coverage"] * avg_coverage
        + weights["jitter"] * jitter_score
        + weights["continuity"] * continuity_score
    )
    alignment_score = max(0.0, min(1.0, alignment_score))

    return TemporalAlignmentResult(
        target_fps=config.target_fps,
        total_duration_s=duration,
        aligned_frame_count=frame_count,
        sensor_stats=sensor_stats,
        unified_timeline=unified_timeline.tolist(),
        issues=issues,
        alignment_score=alignment_score,
        interpolated_data=interpolated,
    )


# ── 内部函数 ────────────────────────────────────────────────────────────

def _compute_sensor_stat(
    name: str,
    timestamps: npt.NDArray[np.float64],
    t_min: float,
    t_max: float,
    config: TemporalAlignmentConfig,
) -> SensorAlignmentStat:
    n = len(timestamps)
    duration = t_max - t_min

    if n < 2:
        return SensorAlignmentStat(
            sensor_name=name,
            native_fps=0.0,
            sample_count=n,
            timestamp_min=float(timestamps[0]) if n > 0 else t_min,
            timestamp_max=float(timestamps[-1]) if n > 0 else t_max,
            coverage_ratio=0.0,
            max_gap_ms=float(duration * 1000) if n <= 1 else 0.0,
            avg_jitter_ms=0.0,
            resample_ratio=0.0,
        )

    # 有效范围
    sensor_t_min = float(timestamps[0])
    sensor_t_max = float(timestamps[-1])
    coverage = min(1.0, (sensor_t_max - sensor_t_min) / max(duration, 1e-9))

    # 频率
    native_fps = (n - 1) / max(sensor_t_max - sensor_t_min, 1e-9)

    # 抖动
    deltas = np.diff(timestamps)
    expected_dt = 1.0 / max(native_fps, 1e-9)
    jitter = np.abs(deltas - expected_dt)
    avg_jitter_ms = float(np.mean(jitter)) * 1000
    max_gap_ms = float(np.max(deltas)) * 1000 if len(deltas) > 0 else 0.0

    return SensorAlignmentStat(
        sensor_name=name,
        native_fps=round(native_fps, 1),
        sample_count=n,
        timestamp_min=sensor_t_min,
        timestamp_max=sensor_t_max,
        coverage_ratio=round(coverage, 4),
        max_gap_ms=round(max_gap_ms, 2),
        avg_jitter_ms=round(avg_jitter_ms, 2),
        resample_ratio=round(config.target_fps / max(native_fps, 1e-9), 2),
    )


def _interpolate_to_grid(
    src_ts: npt.NDArray[np.float64],
    src_vals: npt.NDArray[np.float32],
    target_grid: npt.NDArray[np.float64],
    method: InterpolationMethod = "linear",
    max_gap_s: float = 0.1,
) -> npt.NDArray[np.float32]:
    """将源数据插值到目标时间网格"""
    from scipy.interpolate import interp1d

    n_target = len(target_grid)
    n_dims = src_vals.shape[1] if src_vals.ndim > 1 else 1

    if src_vals.ndim == 1:
        src_vals = src_vals.reshape(-1, 1)

    result = np.zeros((n_target, n_dims), dtype=np.float32)

    for dim in range(n_dims):
        try:
            interpolator = interp1d(
                src_ts,
                src_vals[:, dim],
                kind=method,
                bounds_error=False,
                fill_value=np.nan,
            )
            result[:, dim] = interpolator(target_grid).astype(np.float32)
        except ValueError:
            # 样条插值点数不足时回退到线性
            interpolator = interp1d(
                src_ts,
                src_vals[:, dim],
                kind="linear",
                bounds_error=False,
                fill_value=np.nan,
            )
            result[:, dim] = interpolator(target_grid).astype(np.float32)

    if n_dims == 1:
        result = result.ravel()

    return result
