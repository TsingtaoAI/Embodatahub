/**
 * 多模态数据对齐页面
 *
 * 提供三层对齐能力:
 *   1. 时序对齐 — 统一传感器时间戳到公共时间网格
 *   2. 跨模态对齐 — 使用 CLIP + DTW 进行语义对齐
 *   3. 模型管理 — 下载/管理 ONNX 模型
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { Translation } from "./i18n";
import { apiUrl, fetchWithAuth } from "./api";

// ── API helpers ──────────────────────────────────────────────────────────

interface ModelStatus {
  id: string;
  display_name: string;
  description: string;
  file_size_mb: number;
  required: boolean;
  cached: boolean;
}

interface AlignmentConfig {
  temporal: Record<string, unknown>;
  cross_modal: Record<string, unknown>;
  multimodal: Record<string, unknown>;
}

async function fetchModels(): Promise<Record<string, ModelStatus>> {
  const resp = await fetchWithAuth(apiUrl("/api/alignment/models"));
  if (!resp.ok) throw new Error("Failed to fetch models");
  const data = await resp.json();
  return data.models as Record<string, ModelStatus>;
}

async function downloadModel(modelId: string): Promise<void> {
  const resp = await fetchWithAuth(apiUrl(`/api/alignment/models/${modelId}/download`), { method: "POST" });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error((err as { detail?: string }).detail ?? "Download failed");
  }
}

async function removeModel(modelId: string): Promise<void> {
  const resp = await fetchWithAuth(apiUrl(`/api/alignment/models/${modelId}/remove`), { method: "POST" });
  if (!resp.ok) throw new Error("Remove failed");
}

async function fetchConfig(): Promise<AlignmentConfig> {
  const resp = await fetchWithAuth(apiUrl("/api/alignment/config"));
  if (!resp.ok) throw new Error("Failed to fetch config");
  return resp.json() as Promise<AlignmentConfig>;
}

async function runTemporalAlignment(request: unknown): Promise<unknown> {
  const resp = await fetchWithAuth(apiUrl("/api/alignment/temporal"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!resp.ok) throw new Error("Temporal alignment failed");
  return resp.json();
}

// ── Component ────────────────────────────────────────────────────────────

interface Props {
  copy: Translation;
  projectId: string | null;
}

export default function AlignmentPage({ copy, projectId: _projectId }: Props) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"temporal" | "cross-modal" | "models">("temporal");

  // Config
  const [targetFps, setTargetFps] = useState(30);
  const [interpolation, setInterpolation] = useState<string>("linear");
  const [maxGapFill, setMaxGapFill] = useState(100);
  const [jitterThreshold, setJitterThreshold] = useState(5);
  const [enableVisionTactile, setEnableVisionTactile] = useState(true);
  const [enableActionVision, setEnableActionVision] = useState(true);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.6);
  const [dtwRadius, setDtwRadius] = useState(10);
  const [device, setDevice] = useState<string>("cpu");

  // Demo timestamps
  const [demoStreams, setDemoStreams] = useState(() => {
    const t = Array.from({ length: 100 }, (_, i) => i / 200); // 200Hz joint
    const v = Array.from({ length: 30 }, (_, i) => i / 30); // 30Hz camera
    const tac = Array.from({ length: 60 }, (_, i) => i / 500 + 0.002); // 500Hz tactile
    return JSON.stringify([
      { name: "robot_joints", timestamps: t, modality: "joint" },
      { name: "camera_rgb", timestamps: v, modality: "vision" },
      { name: "tactile_gelsight", timestamps: tac, modality: "tactile" },
    ], null, 2);
  });

  // Queries
  const modelsQuery = useQuery({
    queryKey: ["alignment-models"],
    queryFn: fetchModels,
    enabled: activeTab === "models",
  });

  const configQuery = useQuery({
    queryKey: ["alignment-config"],
    queryFn: fetchConfig,
  });

  // Mutations
  const downloadMutation = useMutation({
    mutationFn: downloadModel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alignment-models"] }),
  });

  const removeMutation = useMutation({
    mutationFn: removeModel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alignment-models"] }),
  });

  const [alignmentResult, setAlignmentResult] = useState<Record<string, unknown> | null>(null);
  const [alignmentError, setAlignmentError] = useState<string | null>(null);

  const runAlignment = async () => {
    setAlignmentError(null);
    setAlignmentResult(null);
    try {
      let streams: unknown[];
      try {
        streams = JSON.parse(demoStreams) as unknown[];
      } catch {
        setAlignmentError("JSON 格式无效，请检查传感器数据");
        return;
      }
      const request = {
        streams,
        config: { target_fps: targetFps, interpolation, max_gap_fill_ms: maxGapFill, timestamp_jitter_threshold_ms: jitterThreshold },
      };
      const result = await runTemporalAlignment(request);
      setAlignmentResult(result as Record<string, unknown>);
    } catch (err) {
      setAlignmentError(err instanceof Error ? err.message : "对齐失败");
    }
  };

  const alignmentLabel = copy.alignment;

  return (
    <section className="alignment-page" style={{ padding: "1.5rem", overflow: "auto", height: "100%" }}>
      <div style={{ marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, fontSize: "1.4rem" }}>{alignmentLabel.title}</h2>
        <p style={{ color: "#64748B", margin: "0.25rem 0 0" }}>{alignmentLabel.description}</p>
      </div>

      {/* ── Tabs ── */}
      <nav role="tablist" style={{ display: "flex", gap: 0, marginBottom: "1.25rem", borderBottom: "2px solid #E2E8F0" }}>
        {(["temporal", "cross-modal", "models"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "0.6rem 1.2rem",
              border: "none",
              background: "none",
              cursor: "pointer",
              fontWeight: activeTab === tab ? 700 : 400,
              color: activeTab === tab ? "#2563EB" : "#64748B",
              borderBottom: activeTab === tab ? "2px solid #2563EB" : "2px solid transparent",
              marginBottom: "-2px",
              fontSize: "0.95rem",
            }}
          >
            {tab === "temporal" ? alignmentLabel.temporal : tab === "cross-modal" ? alignmentLabel.crossModal : alignmentLabel.models}
          </button>
        ))}
      </nav>

      {/* ── Temporal Tab ── */}
      {activeTab === "temporal" && (
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem" }}>
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <label style={labelStyle}>
                <span>{alignmentLabel.targetFps}</span>
                <input type="number" value={targetFps} min={1} max={200} onChange={(e) => setTargetFps(Number(e.target.value))} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                <span>{alignmentLabel.interpolation}</span>
                <select value={interpolation} onChange={(e) => setInterpolation(e.target.value)} style={inputStyle}>
                  <option value="nearest">Nearest</option>
                  <option value="linear">Linear</option>
                  <option value="cubic">Cubic</option>
                </select>
              </label>
              <label style={labelStyle}>
                <span>{alignmentLabel.maxGapFill}</span>
                <input type="number" value={maxGapFill} min={0} max={5000} onChange={(e) => setMaxGapFill(Number(e.target.value))} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                <span>{alignmentLabel.jitterThreshold}</span>
                <input type="number" value={jitterThreshold} min={0} max={100} step={0.5} onChange={(e) => setJitterThreshold(Number(e.target.value))} style={inputStyle} />
              </label>
            </div>

            <label style={labelStyle}>
              <span>Demo Streams (JSON)</span>
              <textarea
                value={demoStreams}
                onChange={(e) => setDemoStreams(e.target.value)}
                rows={10}
                style={{ ...inputStyle, fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </label>

            {/* ── 清洗流水线集成提示 ── */}
            <div style={{
              marginTop: "1rem",
              padding: "0.75rem 1rem",
              background: "#EFF6FF",
              border: "1px solid #BFDBFE",
              borderLeft: "4px solid #3B82F6",
              borderRadius: "6px",
              fontSize: "0.85rem",
              color: "#1E40AF",
              lineHeight: 1.6,
            }}>
              <strong style={{ fontSize: "0.9rem" }}>💡 在清洗流水线中的使用</strong>
              <p style={{ margin: "0.4rem 0 0", color: "#1E293B" }}>
                在数据集质检页面点击<strong>「开始清洗」</strong>时，如果启用了 <code style={{
                  background: "#DBEAFE", padding: "0.1rem 0.3rem", borderRadius: "3px",
                  fontSize: "0.82rem", fontWeight: 600,
                }}>multimodal_alignment</code> 过滤阶段，系统将自动：
              </p>
              <ol style={{ margin: "0.4rem 0 0", paddingLeft: "1.3rem", color: "#334155" }}>
                <li><strong>时序对齐</strong> → 统一所有传感器到 {targetFps}Hz 网格</li>
                <li><strong>跨模态对齐</strong> → CLIP 编码 + DTW 匹配视觉-触觉帧</li>
                <li>结果纳入<strong>质检报告</strong> (passed / review / excluded)</li>
              </ol>
            </div>

            <button
              type="button"
              onClick={runAlignment}
              style={{
                marginTop: "1rem",
                padding: "0.6rem 1.5rem",
                background: "#2563EB",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.95rem",
              }}
            >
              {alignmentLabel.runAlignment}
            </button>

            {alignmentError && (
              <div style={{ marginTop: "1rem", padding: "0.75rem", background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "6px", color: "#DC2626", fontSize: "0.9rem" }}>
                {alignmentError}
              </div>
            )}
          </div>

          <div>
            <h3 style={{ fontSize: "1.1rem", margin: "0 0 0.75rem" }}>{alignmentLabel.results}</h3>
            {alignmentResult ? (
              /* eslint-disable @typescript-eslint/no-explicit-any */
              <div style={{ fontSize: "0.9rem" }}>
                <div style={statRow}><strong>{alignmentLabel.overallScore}:</strong> <span style={{ color: "#2563EB", fontWeight: 700 }}>{((alignmentResult as any).alignment_score as number)?.toFixed(4)}</span></div>
                <div style={statRow}><strong>Duration:</strong> {((alignmentResult as any).total_duration_s as number)?.toFixed(2)}s</div>
                <div style={statRow}><strong>Frames:</strong> {String((alignmentResult as any).aligned_frame_count)}</div>
                {(alignmentResult as any).sensor_stats && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <strong>Sensor Stats:</strong>
                    {Object.entries((alignmentResult as any).sensor_stats as Record<string, any>).map(([name, stats]: [string, any]) => (
                      <div key={name} style={{ marginLeft: "0.5rem", marginTop: "0.25rem", padding: "0.4rem", background: "#F8FAFC", borderRadius: "4px", fontSize: "0.82rem" }}>
                        <strong>{name}</strong>: {String(stats.native_fps)}Hz, {String(stats.sample_count)} samples, coverage {((stats.coverage_ratio as number) * 100).toFixed(1)}%
                      </div>
                    ))}
                  </div>
                )}
                {Array.isArray((alignmentResult as any).issues) && ((alignmentResult as any).issues as any[]).length > 0 && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <strong style={{ color: "#DC2626" }}>{alignmentLabel.issues}:</strong>
                    {((alignmentResult as any).issues as any[]).map((issue: any, i: number) => (
                      <div key={i} style={{ fontSize: "0.8rem", color: "#DC2626" }}>• [{issue.severity}] {issue.sensor}: {issue.detail}</div>
                    ))}
                  </div>
                )}
              /* eslint-enable @typescript-eslint/no-explicit-any */
              </div>
            ) : (
              <p style={{ color: "#94A3B8", fontSize: "0.9rem" }}>{alignmentLabel.notRun}</p>
            )}
          </div>
        </div>
      )}

      {/* ── Cross-Modal Tab ── */}
      {activeTab === "cross-modal" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
          <div>
            <div style={{ display: "grid", gap: "1rem" }}>
              <label style={{ ...labelStyle, flexDirection: "row", alignItems: "center", gap: "0.5rem" }}>
                <input type="checkbox" checked={enableVisionTactile} onChange={(e) => setEnableVisionTactile(e.target.checked)} />
                {alignmentLabel.enableVisionTactile}
              </label>
              <label style={{ ...labelStyle, flexDirection: "row", alignItems: "center", gap: "0.5rem" }}>
                <input type="checkbox" checked={enableActionVision} onChange={(e) => setEnableActionVision(e.target.checked)} />
                {alignmentLabel.enableActionVision}
              </label>
              <label style={labelStyle}>
                <span>{alignmentLabel.similarityThreshold}</span>
                <input type="range" min={0} max={1} step={0.05} value={similarityThreshold} onChange={(e) => setSimilarityThreshold(Number(e.target.value))} />
                <span style={{ fontSize: "0.85rem", color: "#64748B" }}>{similarityThreshold.toFixed(2)}</span>
              </label>
              <label style={labelStyle}>
                <span>{alignmentLabel.dtwRadius}</span>
                <input type="number" value={dtwRadius} min={1} max={100} onChange={(e) => setDtwRadius(Number(e.target.value))} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                <span>{alignmentLabel.device}</span>
                <select value={device} onChange={(e) => setDevice(e.target.value)} style={inputStyle}>
                  <option value="cpu">CPU</option>
                  <option value="cuda">CUDA (GPU)</option>
                </select>
              </label>
            </div>
            <p style={{ marginTop: "1rem", fontSize: "0.85rem", color: "#64748B" }}>
              {alignmentLabel.crossModalDesc}
            </p>
            <p style={{ fontSize: "0.8rem", color: "#94A3B8" }}>
              Requires CLIP ONNX model. Go to <strong>Models</strong> tab to download.
            </p>
          </div>
          <div>
            <h3 style={{ fontSize: "1.1rem", margin: "0 0 0.75rem" }}>{alignmentLabel.results}</h3>
            <p style={{ color: "#94A3B8", fontSize: "0.9rem" }}>
              Cross-modal alignment runs as part of the Dataset QC pipeline.<br />
              Enable <strong>multimodal_alignment</strong> in filter stages and run cleaning to see results.
            </p>
          </div>
        </div>
      )}

      {/* ── Models Tab ── */}
      {activeTab === "models" && (
        <div>
          <p style={{ color: "#64748B", fontSize: "0.9rem", marginBottom: "1rem" }}>{alignmentLabel.modelsDesc}</p>
          {modelsQuery.isLoading && <p>Loading models...</p>}
          {modelsQuery.data && (
            <div style={{ display: "grid", gap: "1rem" }}>
              {Object.entries(modelsQuery.data).map(([id, model]) => (
                <div
                  key={id}
                  style={{
                    padding: "1rem",
                    background: model.cached ? "#F0FDF4" : "#F8FAFC",
                    border: `1px solid ${model.cached ? "#86EFAC" : "#E2E8F0"}`,
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <strong>{model.display_name}</strong>
                      <span style={{
                        fontSize: "0.7rem",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "4px",
                        background: model.required ? "#FEF3C7" : "#E2E8F0",
                        color: model.required ? "#92400E" : "#64748B",
                      }}>
                        {model.required ? alignmentLabel.required : alignmentLabel.optional}
                      </span>
                      <span style={{
                        fontSize: "0.7rem",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "4px",
                        background: model.cached ? "#DCFCE7" : "#F1F5F9",
                        color: model.cached ? "#166534" : "#94A3B8",
                      }}>
                        {model.cached ? alignmentLabel.cached : alignmentLabel.notCached}
                      </span>
                    </div>
                    <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "#64748B" }}>{model.description}</p>
                    <p style={{ margin: "0.25rem 0 0", fontSize: "0.75rem", color: "#94A3B8" }}>{model.file_size_mb} MB</p>
                  </div>
                  <div>
                    {model.cached ? (
                      <button
                        type="button"
                        onClick={() => removeMutation.mutate(id)}
                        disabled={removeMutation.isPending}
                        style={{ ...actionBtn, background: "#EF4444" }}
                      >
                        {removeMutation.isPending ? "..." : "Remove"}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => downloadMutation.mutate(id)}
                        disabled={downloadMutation.isPending}
                        style={{ ...actionBtn, background: "#2563EB" }}
                      >
                        {downloadMutation.isPending ? alignmentLabel.downloading : "Download"}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────

const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column" as const,
  gap: "0.3rem",
  fontSize: "0.85rem",
  fontWeight: 500,
  color: "#334155",
};

const inputStyle: React.CSSProperties = {
  padding: "0.4rem 0.6rem",
  border: "1px solid #CBD5E1",
  borderRadius: "4px",
  fontSize: "0.9rem",
};

const statRow: React.CSSProperties = {
  padding: "0.3rem 0",
  borderBottom: "1px solid #F1F5F9",
};

const actionBtn: React.CSSProperties = {
  padding: "0.4rem 1rem",
  color: "white",
  border: "none",
  borderRadius: "4px",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: "0.85rem",
};
