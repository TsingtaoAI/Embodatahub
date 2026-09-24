#!/usr/bin/env python3
"""生成多模态数据对齐架构图"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc, ConnectionPatch
import numpy as np

plt.rcParams["font.family"] = ["Noto Sans CJK SC", "AR PL UMing CN", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "/data/mashideng/rslstudio/scripts/diagrams"


def make_problem_diagram():
    """图1: 多模态传感器频率差异问题建模"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                     gridspec_kw={"height_ratios": [3, 2]})
    fig.patch.set_facecolor("#FAFBFC")

    # ── 上图：传感器频率对比 ──
    sensors = [
        ("机器人关节\n编码器", 200, "#2563EB", "7-30维\n浮点向量"),
        ("IMU\n惯性测量", 400, "#7C3AED", "四元数\n+加速度"),
        ("触觉传感器\n(GelSight)", 500, "#DC2626", "触觉图像\n480×640"),
        ("麦克风\n阵列", 48000, "#F59E0B", "音频波形\n16bit PCM"),
        ("RGB 相机", 30, "#059669", "1920×1080\nRGB 图像"),
        ("深度相机", 15, "#0891B2", "深度图\n16bit"),
    ]
    names = [s[0] for s in sensors]
    freqs = [s[1] for s in sensors]
    colors = [s[2] for s in sensors]
    descs = [s[3] for s in sensors]

    bars = ax1.barh(names, [np.log10(f) for f in freqs], color=colors, edgecolor="white", linewidth=1.2, height=0.65)
    ax1.set_title("多模态传感器 — 频率差异", fontsize=18, fontweight="bold", pad=18, color="#1E293B")
    ax1.set_xlabel("对数频率 log₁₀(Hz)", fontsize=11, color="#64748B")

    for bar, freq, desc in zip(bars, freqs, descs):
        ax1.text(bar.get_width() + 0.04, bar.get_y() + bar.get_height() / 2,
                 f"{freq:,} Hz", va="center", fontsize=13, fontweight="bold", color="#1E293B")
        ax1.text(bar.get_width() + 0.04, bar.get_y() + bar.get_height() / 2 - 0.28,
                 desc, va="top", fontsize=9, color="#64748B")

    ax1.set_xlim(0, 5.5)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color("#E2E8F0")
    ax1.spines["bottom"].set_color("#E2E8F0")
    ax1.tick_params(colors="#94A3B8", labelsize=10)
    ax1.set_xticklabels([])

    # 目标频率标注
    ax1.axvline(x=np.log10(30), color="#EF4444", linestyle="--", linewidth=2, alpha=0.7)
    ax1.text(np.log10(30) + 0.06, len(sensors) - 0.35, "目标: 30Hz", fontsize=11, color="#EF4444",
             fontweight="bold", bbox=dict(facecolor="#FEF2F2", edgecolor="#FECACA", pad=4))

    # ── 下图：对齐挑战示意 ──
    t = np.linspace(0, 1, 200)
    high_freq = 0.5 * np.sin(2 * np.pi * 50 * t)
    low_freq = 0.8 * np.sin(2 * np.pi * 6 * t + 0.3)
    tactile = 0.6 * np.sin(2 * np.pi * 80 * t + 0.7)

    ax2.plot(t, high_freq + 6, color="#2563EB", linewidth=1.2, alpha=0.8, label="关节位置 (200Hz)")
    ax2.plot(t, low_freq + 3, color="#059669", linewidth=1.2, alpha=0.8, label="视频帧 (30Hz)")
    ax2.plot(t, tactile, color="#DC2626", linewidth=1.2, alpha=0.8, label="触觉信号 (500Hz)")

    # 采样点标记
    for i in range(0, 200, 4):
        ax2.plot(t[i], high_freq[i] + 6, "o", color="#2563EB", markersize=3, alpha=0.5)
    for i in range(0, 200, 33):
        ax2.plot(t[i], low_freq[i] + 3, "s", color="#059669", markersize=4, alpha=0.7)
    for i in range(0, 200, 2):
        ax2.plot(t[i], tactile[i], "d", color="#DC2626", markersize=2, alpha=0.4)

    ax2.set_title("对齐挑战：不同频率信号需统一到相同时间网格", fontsize=16, fontweight="bold", pad=15, color="#1E293B")
    ax2.set_xlabel("时间 (s)", fontsize=11, color="#64748B")
    ax2.set_ylabel("信号幅度", fontsize=11, color="#64748B")
    ax2.legend(loc="upper right", fontsize=9, framealpha=0.9, edgecolor="#E2E8F0")
    ax2.set_ylim(-1.5, 8)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(axis="y", alpha=0.3, color="#CBD5E1")

    # 标注箭头
    ax2.annotate("时间戳插值\n线性/三次样条", xy=(0.48, 4.5), fontsize=11, ha="center",
                 color="#8B5CF6", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#F5F3FF", edgecolor="#C4B5FD"))
    ax2.annotate("重采样至\n统一 30Hz 网格", xy=(0.72, 1.5), fontsize=11, ha="center",
                 color="#EF4444", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF2F2", edgecolor="#FECACA"))

    plt.tight_layout(pad=2)
    fig.savefig(f"{OUT_DIR}/01-problem-modeling.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("✅ 问题建模图已生成")


def make_pipeline_diagram():
    """图2: 多模态对齐数据流管道"""
    fig, ax = plt.subplots(1, 1, figsize=(18, 12))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 14)
    ax.axis("off")
    fig.patch.set_facecolor("#F8FAFC")

    HEADER_FONT = {"fontsize": 20, "fontweight": "bold", "color": "#0F172A"}
    TITLE_FONT = {"fontsize": 13, "fontweight": "bold", "color": "#1E293B"}
    BODY_FONT = {"fontsize": 10, "color": "#475569"}
    SMALL_FONT = {"fontsize": 8.5, "color": "#64748B"}
    LABEL_FONT = {"fontsize": 14, "fontweight": "bold", "color": "white"}

    def draw_box(x, y, w, h, color, label="", subtitle="", edge_color=None, alpha=0.95):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                             facecolor=color, edgecolor=edge_color or color,
                             linewidth=1.5, alpha=alpha, zorder=2)
        ax.add_patch(box)
        if label:
            ax.text(x + w / 2, y + h / 2 + 0.12, label, ha="center", va="center",
                    fontsize=10.5, fontweight="bold", color="white", zorder=3)
        if subtitle:
            ax.text(x + w / 2, y + h / 2 - 0.35, subtitle, ha="center", va="center",
                    fontsize=8, color="#E2E8F0", zorder=3)
        return box

    def draw_arrow(x1, y1, x2, y2, color="#94A3B8", lw=2.5, style="simple",
                   label="", label_offset=(0, 0.15)):
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle="->,head_length=5,head_width=4",
                                color=color, lw=lw, zorder=1)
        ax.add_patch(arrow)
        if label:
            mid_x, mid_y = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
            ax.text(mid_x, mid_y, label, ha="center", va="center", fontsize=8.5,
                    color=color, fontweight="bold", zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1))

    # ── 标题 ──
    ax.text(10, 13.2, "多模态数据对齐 — 端到端数据流管道", ha="center", **HEADER_FONT)

    # ── 第1行：数据输入层 ──
    Y_INPUT = 11
    sensors_in = [
        ("关节编码器\n200Hz", "#2563EB", 0.5, 2.8),
        ("RGB相机\n30Hz", "#059669", 3.8, 2.8),
        ("深度相机\n15Hz", "#0891B2", 7.1, 2.8),
        ("触觉传感器\n500Hz", "#DC2626", 10.4, 2.8),
        ("IMU\n400Hz", "#7C3AED", 13.7, 2.8),
        ("麦克风\n48kHz", "#F59E0B", 17.0, 2.8),
    ]
    for label, color, x, w in sensors_in:
        draw_box(x, Y_INPUT, w, 1.8, color, label, alpha=0.92)

    ax.text(9.7, Y_INPUT - 0.3, "▲ 多模态传感器原始数据  ▲", ha="center", fontsize=12,
            fontweight="bold", color="#334155")

    # ── 第2行：时序对齐层 ──
    Y_T1 = 8.0
    ax.text(0.3, Y_T1 + 1.2, "层 1", fontsize=13, fontweight="bold", color="#8B5CF6")
    draw_box(0.8, Y_T1, 8.4, 2.2, "#7C3AED", "",
             "时序对齐 (Temporal Alignment)\n• 时间戳标准化 → Unix epoch\n• 线性/三次样条插值\n• 丢帧检测 + 间隙填充\n• 统一目标频率: 30Hz", alpha=0.15)
    ax.text(5.0, Y_T1 + 1.2, "① 时序对齐 — 纯算法 (numpy/scipy)", ha="center", **TITLE_FONT)
    ax.text(5.0, Y_T1 + 0.5, "时间戳标准化 → 插值 → 丢帧补偿 → 30Hz 统一网格", ha="center", **BODY_FONT)

    # 模型标注
    draw_box(10.8, Y_T1 + 0.15, 3.8, 1.9, "#8B5CF6", "",
             "本地 Python\nnumpy + scipy\n< 1ms / episode", alpha=0.85)
    ax.text(12.7, Y_T1 + 1.2, "CPU 本地", ha="center", fontsize=9, fontweight="bold", color="white")

    draw_arrow(5.0, Y_T1 + 2.2, 5.0, Y_T1 + 0.25, "#8B5CF6", label="数据流入")

    # ── 第3行：跨模态语义对齐 ──
    Y_T2 = 4.5
    ax.text(0.3, Y_T2 + 1.2, "层 2", fontsize=13, fontweight="bold", color="#2563EB")
    draw_box(0.8, Y_T2, 8.4, 2.2, "#2563EB", "",
             "跨模态语义对齐 (Cross-Modal Alignment)\n• CLIP 编码器: 视觉帧 → 512维 embedding\n• 触觉图像 → 同一嵌入空间 (共享 CLIP)\n• DTW 最优路径匹配\n• 余弦相似度矩阵", alpha=0.15)
    ax.text(5.0, Y_T2 + 1.2, "② 跨模态对齐 — 本地 ONNX 推理", ha="center", **TITLE_FONT)
    ax.text(5.0, Y_T2 + 0.5, "视觉编码 → 触觉编码 → Cosine Similarity → DTW 路径", ha="center", **BODY_FONT)

    draw_box(10.8, Y_T2 + 0.15, 3.8, 1.9, "#3B82F6", "",
             "CLIP ViT-B/32\nONNX Runtime\n~350MB / 2-5s ep", alpha=0.85)
    ax.text(12.7, Y_T2 + 1.2, "GPU 本地推理", ha="center", fontsize=9, fontweight="bold", color="white")

    draw_arrow(5.0, Y_T1, 5.0, Y_T2 + 2.35, "#94A3B8")
    draw_arrow(5.0, Y_T2 + 2.2, 5.0, Y_T2 + 0.25, "#2563EB", label="对齐数据流入")

    # ── 第4行：质量评估 ──
    Y_T3 = 1.0
    ax.text(0.3, Y_T3 + 1.2, "层 3", fontsize=13, fontweight="bold", color="#059669")
    draw_box(0.8, Y_T3, 8.4, 2.2, "#059669", "",
             "对齐质量评估 (Alignment Quality)\n• temporal_jitter_score (时序抖动)\n• cross_modal_similarity (跨模态相似度)\n• alignment_status: passed / review / excluded\n• 接入现有 FilterStage 质检流水线", alpha=0.15)
    ax.text(5.0, Y_T3 + 1.2, "③ 质量评估 — 接入现有 RDS 质检框架", ha="center", **TITLE_FONT)
    ax.text(5.0, Y_T3 + 0.5, "规则引擎 + XGBoost → 综合评分 → 质检报告", ha="center", **BODY_FONT)

    draw_box(10.8, Y_T3 + 0.15, 3.8, 1.9, "#10B981", "",
             "规则引擎\nXGBoost\nFilterStage 集成", alpha=0.85)
    ax.text(12.7, Y_T3 + 1.2, "CPU 本地", ha="center", fontsize=9, fontweight="bold", color="white")

    draw_arrow(5.0, Y_T2, 5.0, Y_T3 + 2.35, "#94A3B8")
    draw_arrow(5.0, Y_T3 + 2.2, 5.0, Y_T3 + 0.25, "#059669")

    # ── 输出 ──
    ax.text(10, -0.5, "📊 质检报告 · 📦 对齐数据 (parquet) · 🏷️ LeRobot 格式兼容", ha="center",
            fontsize=13, fontweight="bold", color="#0F172A",
            bbox=dict(facecolor="#F0FDF4", edgecolor="#86EFAC", boxstyle="round,pad=0.6"))

    # ── 右侧模型列表 ──
    models_x = 15.8
    ax.text(models_x, 12.5, "模型清单", fontsize=12, fontweight="bold", color="#334155")
    model_list = [
        ("时序插值", "numpy/scipy", "#8B5CF6"),
        ("视觉编码器", "CLIP ViT-B/32", "#3B82F6"),
        ("触觉编码器", "CLIP (共享权重)", "#3B82F6"),
        ("音频编码器", "CLAP (可选)", "#6366F1"),
        ("事件检测", "ResNet-18", "#F59E0B"),
        ("综合评分", "XGBoost", "#10B981"),
    ]
    for i, (name, model, color) in enumerate(model_list):
        y_pos = 11.8 - i * 0.55
        draw_box(models_x, y_pos, 3.5, 0.42, color, alpha=0.8)
        ax.text(models_x + 1.75, y_pos + 0.21, f"{name}: {model}", ha="center", va="center",
                fontsize=8, color="white", fontweight="bold")

    plt.tight_layout(pad=1)
    fig.savefig(f"{OUT_DIR}/02-dataflow-pipeline.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("✅ 数据流管道图已生成")


def make_model_selection_diagram():
    """图3: 模型选型与部署方案"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor("#FAFBFC")

    ax.text(8, 8.3, "多模态对齐 — 专用模型选型与部署方案", ha="center", fontsize=20,
            fontweight="bold", color="#0F172A")

    # 表格数据
    headers = ["阶段", "模型/算法", "参数量", "推理速度", "部署方式", "适用场景"]
    rows = [
        ["① 时序对齐", "线性插值 + 三次样条\n+ 轻量 MLP 补偿", "—", "< 1ms/ep", "🐍 Python\nnumpy/scipy", "所有传感器\n统一时间网格"],
        ["② 视觉-触觉\n  跨模态对齐", "CLIP ViT-B/32\n(ONNX 导出)", "~150M", "2-5s / ep", "🖥️ ONNX Runtime\nGPU 本地推理", "视觉帧 ↔ 触觉图像\n语义空间对齐"],
        ["③ 音频-文本\n  对齐", "CLAP HTSAT\n(ONNX 导出)", "~300M", "5-10s / ep", "🖥️ ONNX Runtime\nGPU (可选)", "语音指令 ↔\n任务描述对齐"],
        ["④ 动作-视觉\n  时序一致性", "DTW + VideoMAE\n特征提取", "~85M", "1-3s / ep", "🖥️ ONNX + CPU", "关节轨迹 ↔ 视频帧\n时序对齐验证"],
        ["⑤ 触觉事件\n  关键帧检测", "ResNet-18 微调\n触觉分类器", "~11M", "< 1s / ep", "🖥️ ONNX Runtime\nCPU 即可", "触觉接触事件\n关键帧提取"],
        ["⑥ 对齐质量\n  综合评分", "规则引擎\n+ XGBoost 回归", "—", "< 10ms/ep", "🐍 Python\nCPU 本地", "episode 级\npass/review/exclude"],
    ]

    colors_table = ["#8B5CF6", "#3B82F6", "#6366F1", "#0EA5E9", "#F59E0B", "#10B981"]

    # 绘制表格
    n_rows, n_cols = len(rows), len(headers)
    col_widths = [2.2, 3.0, 1.5, 2.0, 2.8, 3.0]
    x_positions = [0.4]
    for w in col_widths[:-1]:
        x_positions.append(x_positions[-1] + w)
    x_positions.append(15.6)

    row_height = 1.1
    y_start = 6.8

    # 表头
    for j, (header, x) in enumerate(zip(headers, x_positions)):
        w = col_widths[j]
        rect = FancyBboxPatch((x, y_start), w, 0.7, boxstyle="round,pad=0.05",
                              facecolor="#1E293B", edgecolor="#1E293B", linewidth=1)
        ax.add_patch(rect)
        ax.text(x + w / 2, y_start + 0.35, header, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

    # 数据行
    for i, (row, color) in enumerate(zip(rows, colors_table)):
        y = y_start - (i + 1) * row_height
        bg = "#FFFFFF" if i % 2 == 0 else "#F1F5F9"
        rect = FancyBboxPatch((x_positions[0], y), sum(col_widths), row_height,
                              boxstyle="round,pad=0.05", facecolor=bg,
                              edgecolor="#E2E8F0", linewidth=0.8)
        ax.add_patch(rect)

        # 阶段列着色
        tag = FancyBboxPatch((x_positions[0] + 0.08, y + 0.15), 0.12, row_height - 0.3,
                             boxstyle="round,pad=0.03", facecolor=color, edgecolor=color)
        ax.add_patch(tag)

        for j, (cell, x) in enumerate(zip(row, x_positions)):
            w = col_widths[j]
            fontsize = 9 if j > 0 else 9.5
            fontweight = "bold" if j == 0 else "normal"
            ax.text(x + w / 2 + (0.1 if j == 0 else 0), y + row_height / 2,
                    cell, ha="center", va="center", fontsize=fontsize,
                    fontweight=fontweight, color="#1E293B")

    # 底部描述
    ax.text(8, 0.6, "💡 设计原则: ① 本地优先 (ONNX 无需云服务)  ② 渐进式部署 (先上无模型层)  ③ 与现有 RDS FilterStage 架构无缝集成",
            ha="center", fontsize=12, color="#475569",
            bbox=dict(facecolor="#F8FAFC", edgecolor="#CBD5E1", boxstyle="round,pad=0.5"))

    plt.tight_layout(pad=1)
    fig.savefig(f"{OUT_DIR}/03-model-selection.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("✅ 模型选型图已生成")


if __name__ == "__main__":
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    make_problem_diagram()
    make_pipeline_diagram()
    make_model_selection_diagram()
    print(f"\n📁 图片已保存至 {OUT_DIR}/")
