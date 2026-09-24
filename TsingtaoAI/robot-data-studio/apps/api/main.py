import asyncio
import hashlib
import hmac
import json
import os
import shutil
import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse

from robot_data_studio.formats import UnsupportedDatasetFormat
from robot_data_studio.projects.models import CleaningRunRequest, CreateProjectRequest, ExportRequest, Project
from robot_data_studio.projects.service import ProjectService
from robot_data_studio.quality import (
    CleaningRun,
    CleaningSummary,
    CrossModalAligner,
    CrossModalConfig,
    EpisodeDecisionRequest,
    EpisodeQualityResult,
    FilterConfig,
    FilterConfigPatch,
    FilterDetail,
    FilterRun,
    FilterSummary,
    MultiModalAlignmentConfig,
    MultiModalAlignmentReport,
    SensorStream,
    TemporalAlignmentConfig,
    TemporalAlignmentResult,
    VlmSettings,
    align_timeline,
)
from robot_data_studio.reports import ReportSignals
from robot_data_studio.viewer import create_episode_recording


ARTIFACT_URL_TTL_SECONDS = 6 * 3600


def _load_sign_secret(artifact_root: Path) -> bytes:
    """签名密钥: 优先环境变量 RDS_SIGN_SECRET,否则落盘持久化(重启后旧链接不失效)。

    刻意放在产物目录之外 —— 产物目录会被打包进备份,不想再多一份密钥进去。
    """
    env = os.environ.get("RDS_SIGN_SECRET")
    if env:
        return env.encode()
    secret_file = Path(artifact_root).parent / ".rds-sign-secret"
    if secret_file.is_file():
        return secret_file.read_bytes().strip()
    secret = os.urandom(32).hex().encode()
    secret_file.write_bytes(secret)
    secret_file.chmod(0o600)
    return secret


def create_app(artifact_root: str | Path = ".rds-artifacts") -> FastAPI:
    app = FastAPI(title="Robot Data Studio API")

    # CORS: allow the main TsingtaoAI frontend to embed RDS in an iframe
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            os.environ.get("RDS_CORS_ORIGIN", "http://localhost:8003"),
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    service = ProjectService(Path(artifact_root))

    # ── .rrd 产物签名 ──────────────────────────────────────────────────
    # ⚠️ Rerun 的 WASM viewer 在内部自己 fetch .rrd,不携带 cookie(实测: 同一时刻
    #    其它请求 200/201、唯独它 401),所以过不了 nginx 的 auth_request。
    #    改由后端签发限时签名 URL,nginx 对 /rds-app/api/artifacts/ 放行,后端校验。
    sign_secret = _load_sign_secret(Path(artifact_root))

    def _artifact_signature(filename: str, expires: int) -> str:
        return hmac.new(
            sign_secret, f"{filename}\n{expires}".encode(), hashlib.sha256
        ).hexdigest()

    def _artifact_url(filename: str) -> str:
        expires = int(time.time()) + ARTIFACT_URL_TTL_SECONDS
        return (
            f"/api/artifacts/{filename}"
            f"?exp={expires}&sig={_artifact_signature(filename, expires)}"
        )

    samples_dir = os.environ.get(
        "RDS_SAMPLES_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "data" / "samples"),
    )
    upload_dir = Path(samples_dir) / ".uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/formats")
    def formats():
        return service.formats()

    @app.get("/api/dataset-paths")
    def dataset_paths() -> list[str]:
        root = Path(samples_dir).expanduser().resolve()
        if not root.is_dir():
            return []
        paths: list[str] = []
        try:
            for entry in sorted(root.iterdir()):
                if not (entry.is_dir() or entry.is_symlink()):
                    continue
                if service.probe_dataset(str(entry)):
                    paths.append(str(entry.resolve()))
        except PermissionError:
            pass
        return paths

    @app.post("/api/datasets/upload")
    async def upload_dataset(file: UploadFile = File(...)):
        if not file.filename:
            raise HTTPException(status_code=400, detail="未选择文件")

        # 允许的扩展名
        allowed = {".zip", ".tar.gz", ".tgz", ".hdf5", ".h5", ".zarr.zip"}
        name_lower = file.filename.lower()
        is_archive = any(name_lower.endswith(ext) for ext in {".zip", ".tar.gz", ".tgz", ".zarr.zip"})
        is_single = any(name_lower.endswith(ext) for ext in {".hdf5", ".h5"})
        if not (is_archive or is_single):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持: {', '.join(sorted(allowed))}",
            )

        # 去重：文件名已存在则加时间戳
        dest = upload_dir / file.filename
        if dest.exists():
            stem, ext = os.path.splitext(file.filename)
            dest = upload_dir / f"{stem}_{int(time.time())}{ext}"

        # 写入上传文件
        try:
            content = await file.read()
            dest.write_bytes(content)
        except OSError as error:
            raise HTTPException(status_code=500, detail=f"保存文件失败: {error}") from error

        # 如果是归档文件，解压到 samples_dir
        if is_archive:
            dataset_name = dest.stem
            if dataset_name.endswith(".tar"):
                dataset_name = dataset_name[:-4]
            if dataset_name.endswith(".zarr"):
                dataset_name = dataset_name[:-5]
            extract_to = Path(samples_dir).expanduser().resolve() / dataset_name
            try:
                shutil.unpack_archive(str(dest), str(extract_to))
            except (shutil.ReadError, ValueError, OSError) as error:
                raise HTTPException(
                    status_code=400,
                    detail=f"归档文件无法解压: {error}",
                ) from error
            return {
                "path": str(extract_to.resolve()),
                "filename": file.filename,
                "extracted": True,
                "format_hint": None,
            }

        # 单文件直接使用
        return {
            "path": str(dest.resolve()),
            "filename": file.filename,
            "extracted": False,
            "format_hint": None,
        }

    @app.post("/api/datasets/upload-folder")
    async def upload_folder(files: list[UploadFile] = File(...)):
        if not files or all(not f.filename for f in files):
            raise HTTPException(status_code=400, detail="未选择文件或文件夹")

        # 第一个文件的顶级目录名作为数据集名
        first_path = files[0].filename or "dataset"
        top_name = first_path.split("/")[0]
        # 去重
        dest_root = Path(samples_dir).expanduser().resolve() / top_name
        if dest_root.exists():
            dest_root = Path(samples_dir).expanduser().resolve() / f"{top_name}_{int(time.time())}"

        errors: list[str] = []
        saved = 0
        for f in files:
            if not f.filename:
                continue
            # filename 形如 "topFolder/subdir/file.txt" — 去掉顶级前缀
            parts = f.filename.split("/")
            rel = "/".join(parts[1:]) if len(parts) > 1 and parts[0] == top_name else f.filename
            file_dest = dest_root / rel if rel else dest_root
            file_dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                content = await f.read()
                file_dest.write_bytes(content)
                saved += 1
            except OSError as error:
                errors.append(f"{rel}: {error}")

        if errors and saved == 0:
            raise HTTPException(status_code=500, detail=f"所有文件写入失败: {'; '.join(errors[:3])}")

        return {
            "path": str(dest_root.resolve()),
            "filename": top_name,
            "extracted": False,
            "folder": True,
            "files_saved": saved,
            "errors": errors if errors else None,
        }

    @app.post("/api/projects", status_code=201, response_model=Project)
    def create_project(
        request: CreateProjectRequest,
        project_uuid: str | None = Query(default=None),
    ) -> Project:
        try:
            return service.create(request.path, request.format_hint, project_uuid=project_uuid)
        except (UnsupportedDatasetFormat, ValueError, OSError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/projects/{project_id}", response_model=Project)
    def get_project(project_id: str) -> Project:
        try:
            return service.project(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/projects/{project_id}/episodes")
    def episodes(project_id: str, limit: int | None = Query(default=100, ge=1, le=1000)):
        try:
            return service.reader(project_id).list_episodes(limit=limit)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/projects/{project_id}/episodes/{episode_index}/frames")
    def frames(project_id: str, episode_index: int):
        try:
            return service.reader(project_id).read_episode_frames(episode_index)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get(
        "/api/projects/{project_id}/report-signals",
        response_model=ReportSignals,
    )
    def report_signals(
        project_id: str,
        episode_index: int = Query(ge=0),
    ) -> ReportSignals:
        try:
            return service.report_signals(project_id, episode_index)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get(
        "/api/projects/{project_id}/episodes/{episode_index}/visual-quality/frame",
        response_class=Response,
    )
    def visual_quality_frame(
        project_id: str,
        episode_index: int,
        camera: str = Query(min_length=1),
        frame: int = Query(ge=0),
        width: int = Query(default=640, ge=160, le=1600),
    ) -> Response:
        try:
            content = service.visual_quality_frame(
                project_id,
                episode_index,
                camera,
                frame,
                width,
            )
            return Response(
                content=content,
                media_type="image/jpeg",
                headers={"Cache-Control": "private, max-age=3600"},
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post(
        "/api/projects/{project_id}/episodes/{episode_index}/recording",
        status_code=201,
    )
    def recording(project_id: str, episode_index: int) -> dict[str, str]:
        try:
            filename = f"{project_id}-episode-{episode_index:06d}.rrd"
            output = service.artifact_root / filename
            create_episode_recording(service.reader(project_id), episode_index, output)
            return {"recording_url": _artifact_url(filename)}
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/projects/{project_id}/episodes/{episode_index}/recording/warm")
    def warm_recording(project_id: str, episode_index: int) -> dict[str, str]:
        try:
            service.reader(project_id).episode(episode_index)
            return {"status": "warmed"}
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/projects/{project_id}/exports", status_code=201)
    def export(project_id: str, request: ExportRequest) -> dict[str, str | int]:
        try:
            output = service.export_dataset(
                project_id,
                request.format,
                request.episode_indexes,
                request.options.output_dir,
            )
            return {
                "output_path": str(output.output_path),
                "report_path": str(output.report_path),
                "format": output.format,
                "episode_count": output.episode_count,
            }
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except (UnsupportedDatasetFormat, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post(
        "/api/projects/{project_id}/cleaning/runs",
        status_code=201,
        response_model=CleaningRun,
    )
    def run_cleaning(project_id: str, request: CleaningRunRequest) -> CleaningRun:
        try:
            return service.run_cleaning(project_id, request)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/projects/{project_id}/cleaning", response_model=CleaningSummary)
    def cleaning(project_id: str) -> CleaningSummary:
        try:
            return service.cleaning_summary(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post(
        "/api/projects/{project_id}/filters/runs",
        status_code=201,
        response_model=FilterRun,
    )
    def run_filters(project_id: str) -> FilterRun:
        try:
            return service.run_filters(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/projects/{project_id}/pipeline/runs/stream")
    async def stream_pipeline(project_id: str, request: CleaningRunRequest) -> StreamingResponse:
        try:
            service.project(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        async def event_generator():
            queue: asyncio.Queue[dict] = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def emit(payload: dict) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, payload)

            def cleaning_progress(completed: int, total: int) -> None:
                emit({"event": "progress", "phase": "cleaning", "completed": completed, "total": total})

            def filters_progress(completed: int, total: int) -> None:
                emit({"event": "progress", "phase": "filters", "completed": completed, "total": total})

            async def run_work() -> None:
                try:
                    cleaning, filters = await asyncio.to_thread(
                        service.run_pipeline,
                        project_id,
                        request,
                        cleaning_progress,
                        filters_progress,
                    )
                    emit(
                        {
                            "event": "done",
                            "cleaning": cleaning.model_dump(mode="json"),
                            "filters": filters.model_dump(mode="json"),
                        }
                    )
                except Exception as error:  # noqa: BLE001 - surfaced to client via SSE
                    emit({"event": "error", "message": str(error)})

            task = asyncio.create_task(run_work())
            try:
                while True:
                    payload = await queue.get()
                    event_name = payload.get("event", "message")
                    data = json.dumps(payload, ensure_ascii=False)
                    yield f"event: {event_name}\ndata: {data}\n\n"
                    if event_name in ("done", "error"):
                        break
            finally:
                if not task.done():
                    task.cancel()

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/api/projects/{project_id}/filters", response_model=FilterSummary)
    def filters(project_id: str) -> FilterSummary:
        try:
            return service.filter_summary(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get(
        "/api/projects/{project_id}/filters/{stage_id}/episodes/{episode_index}",
        response_model=FilterDetail,
    )
    def filter_detail(project_id: str, stage_id: str, episode_index: int) -> FilterDetail:
        try:
            return service.filter_detail(project_id, stage_id, episode_index)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.patch("/api/projects/{project_id}/filters/config", response_model=FilterConfig)
    def update_filter_config(project_id: str, request: FilterConfigPatch) -> FilterConfig:
        try:
            return service.update_filter_config(project_id, request)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/api/projects/{project_id}/filters/kinematics/urdf", status_code=201)
    async def upload_filter_urdf(
        project_id: str,
        request: Request,
        filename: str = Query(default="robot.urdf"),
    ) -> dict[str, str]:
        try:
            return service.save_filter_urdf(project_id, filename, await request.body())
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/projects/{project_id}/vlm-settings", response_model=VlmSettings)
    def vlm_settings(project_id: str) -> VlmSettings:
        try:
            return service.vlm_settings(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.patch("/api/projects/{project_id}/vlm-settings", response_model=VlmSettings)
    def update_vlm_settings(project_id: str, request: VlmSettings) -> VlmSettings:
        try:
            return service.update_vlm_settings(project_id, request)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.patch(
        "/api/projects/{project_id}/episodes/{episode_index}/decision",
        response_model=EpisodeQualityResult,
    )
    def decision(
        project_id: str,
        episode_index: int,
        request: EpisodeDecisionRequest,
    ) -> EpisodeQualityResult:
        try:
            return service.update_episode_decision(project_id, episode_index, request)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/artifacts/{filename}")
    def artifact(filename: str, exp: int = 0, sig: str = "") -> FileResponse:
        name = Path(filename).name
        if not exp or exp < int(time.time()) or not hmac.compare_digest(
            _artifact_signature(name, exp), sig
        ):
            raise HTTPException(status_code=403, detail="下载链接无效或已过期")
        path = service.artifact_root / name
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(path)

    # ── 多模态对齐 API ─────────────────────────────────────────────────

    _aligner: CrossModalAligner | None = None

    def _get_aligner() -> CrossModalAligner:
        nonlocal _aligner
        if _aligner is None:
            _aligner = CrossModalAligner()
        return _aligner

    @app.get("/api/alignment/models")
    def list_alignment_models() -> dict:
        """列出所有可用的对齐模型及其安装状态"""
        from robot_data_studio.quality.multimodal_models.model_cache import (
            get_model_status,
        )
        return {"models": get_model_status()}

    @app.post("/api/alignment/models/{model_id}/download")
    def download_alignment_model(model_id: str) -> dict:
        """下载指定的对齐模型"""
        from robot_data_studio.quality.multimodal_models.model_cache import (
            ModelCache,
        )
        cache = ModelCache()
        if cache.is_cached(model_id):
            return {"status": "already_cached", "model_id": model_id}
        try:
            path = cache.download(model_id)
            return {"status": "downloaded", "model_id": model_id, "path": str(path)}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/alignment/models/{model_id}/remove")
    def remove_alignment_model(model_id: str) -> dict:
        """删除本地缓存的模型"""
        from robot_data_studio.quality.multimodal_models.model_cache import (
            ModelCache,
        )
        cache = ModelCache()
        cache.remove(model_id)
        return {"status": "removed", "model_id": model_id}

    @app.post("/api/alignment/temporal")
    def run_temporal_alignment(request: dict) -> dict:
        """运行时序对齐

        请求体:
        {
            "streams": [
                {"name": "joints", "timestamps": [...], "modality": "joint"},
                {"name": "camera", "timestamps": [...], "modality": "vision"},
                ...
            ],
            "config": { "target_fps": 30, "interpolation": "linear" }
        }
        """
        config_dict = request.get("config", {})
        config = TemporalAlignmentConfig(**config_dict)

        streams = [
            SensorStream(
                name=s["name"],
                timestamps=s["timestamps"],
                modality=s.get("modality", "other"),
            )
            for s in request.get("streams", [])
        ]

        result = align_timeline(streams, config)
        return {
            "target_fps": result.target_fps,
            "total_duration_s": result.total_duration_s,
            "aligned_frame_count": result.aligned_frame_count,
            "sensor_stats": {
                name: {
                    "native_fps": s.native_fps,
                    "sample_count": s.sample_count,
                    "coverage_ratio": s.coverage_ratio,
                    "max_gap_ms": s.max_gap_ms,
                    "avg_jitter_ms": s.avg_jitter_ms,
                    "resample_ratio": s.resample_ratio,
                }
                for name, s in result.sensor_stats.items()
            },
            "unified_timeline": result.unified_timeline[:100],  # 截断避免过大
            "issues": [
                {"sensor": i.sensor_name, "type": i.issue_type, "detail": i.detail, "severity": i.severity}
                for i in result.issues
            ],
            "alignment_score": result.alignment_score,
        }

    @app.post("/api/alignment/cross-modal")
    def run_cross_modal_alignment(request: dict) -> dict:
        """运行跨模态对齐

        请求体:
        {
            "episode_index": 0,
            "config": { "enable_vision_tactile": true, ... }
        }
        注意: 实际的视频帧和触觉帧通过文件路径传递
        """
        config_dict = request.get("config", {})
        config = CrossModalConfig(**config_dict)
        aligner = _get_aligner()
        aligner.config = config

        # 模拟结果（实际使用时需要传入真实帧数据）
        report = MultiModalAlignmentReport(
            episode_index=request.get("episode_index", 0),
            modality_pairs=[],
            results={},
            overall_score=0.0,
            issues=["请通过清洗流水线运行完整的多模态对齐"],
            recommendations=["在清洗配置中启用 multimodal_alignment 阶段"],
        )

        return {
            "episode_index": report.episode_index,
            "modality_pairs": report.modality_pairs,
            "overall_score": report.overall_score,
            "issues": report.issues,
            "recommendations": report.recommendations,
            "results": {
                key: {
                    "source_count": r.source_count,
                    "target_count": r.target_count,
                    "mean_similarity": r.mean_similarity,
                    "alignment_score": r.alignment_score,
                    "matched_pairs": r.matched_pairs[:20],
                }
                for key, r in report.results.items()
            },
        }

    @app.get("/api/alignment/config")
    def get_alignment_config() -> dict:
        """获取默认对齐配置"""
        return {
            "temporal": TemporalAlignmentConfig().__dict__,
            "cross_modal": CrossModalConfig().__dict__,
            "multimodal": MultiModalAlignmentConfig().model_dump(),
        }

    return app


app = create_app(
    artifact_root=os.environ.get("RDS_ARTIFACT_DIR", ".rds-artifacts"),
)
