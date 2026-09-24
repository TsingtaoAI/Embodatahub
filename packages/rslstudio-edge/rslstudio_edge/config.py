"""配置管理 — YAML 文件 + 环境变量覆盖"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass
class MinioConfig:
    endpoint: str = "192.168.1.107:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "data"
    secure: bool = False

    @property
    def endpoint_url(self) -> str:
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}"


@dataclass
class VideoConfig:
    source: str = "/dev/video0"
    resolution: str = "1280x720"
    fps: int = 30
    codec: str = "libx264"
    preset: str = "ultrafast"
    crf: int = 23
    segment_seconds: int = 10


@dataclass
class BackendConfig:
    url: str = "http://localhost:3000"
    api_key: Optional[str] = None
    project: Optional[str] = None
    enabled: bool = False

    def __bool__(self) -> bool:
        return self.enabled and self.api_key is not None


@dataclass
class HealthConfig:
    port: int = 9091
    bind: str = "0.0.0.0"


@dataclass
class AgentConfig:
    mission: str = "default"
    minio: MinioConfig = field(default_factory=MinioConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    backend: BackendConfig = field(default_factory=BackendConfig)
    health: HealthConfig = field(default_factory=HealthConfig)

    @property
    def s3_prefix(self) -> str:
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        return f"streams/{self.mission}/{today}/"


def load_config(path: Optional[str] = None) -> AgentConfig:
    """加载配置：YAML 文件 → 环境变量覆盖"""
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

    cfg = AgentConfig()

    # 1. YAML 文件
    if path:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    # 2. 解析各节
    if "mission" in data:
        cfg.mission = data["mission"]

    if "minio" in data:
        m = data["minio"]
        cfg.minio = MinioConfig(
            endpoint=m.get("endpoint", cfg.minio.endpoint),
            access_key=m.get("access_key", cfg.minio.access_key),
            secret_key=m.get("secret_key", cfg.minio.secret_key),
            bucket=m.get("bucket", cfg.minio.bucket),
            secure=m.get("secure", cfg.minio.secure),
        )

    if "video" in data:
        v = data["video"]
        cfg.video = VideoConfig(
            source=v.get("source", cfg.video.source),
            resolution=v.get("resolution", cfg.video.resolution),
            fps=v.get("fps", cfg.video.fps),
            codec=v.get("codec", cfg.video.codec),
            preset=v.get("preset", cfg.video.preset),
            crf=v.get("crf", cfg.video.crf),
            segment_seconds=v.get("segment_seconds", cfg.video.segment_seconds),
        )

    if "backend" in data:
        b = data["backend"]
        cfg.backend = BackendConfig(
            url=b.get("url", cfg.backend.url),
            api_key=b.get("api_key", cfg.backend.api_key),
            project=b.get("project", cfg.backend.project),
            enabled=b.get("enabled", cfg.backend.enabled),
        )

    if "health" in data:
        h = data["health"]
        cfg.health = HealthConfig(
            port=h.get("port", cfg.health.port),
            bind=h.get("bind", cfg.health.bind),
        )

    # 3. 环境变量覆盖（EDGE_ 前缀）
    _env_override(cfg)

    return cfg


def _env_override(cfg: AgentConfig) -> None:
    for key, val in os.environ.items():
        if not key.startswith("EDGE_"):
            continue
        k = key[5:].lower()
        if k == "MISSION":
            cfg.mission = val
        elif k == "MINIO_ENDPOINT":
            cfg.minio.endpoint = val
        elif k == "MINIO_ACCESS_KEY":
            cfg.minio.access_key = val
        elif k == "MINIO_SECRET_KEY":
            cfg.minio.secret_key = val
        elif k == "MINIO_BUCKET":
            cfg.minio.bucket = val
        elif k == "SOURCE":
            cfg.video.source = val
        elif k == "RESOLUTION":
            cfg.video.resolution = val
        elif k == "FPS":
            cfg.video.fps = int(val)
        elif k == "SEGMENT_SECONDS":
            cfg.video.segment_seconds = int(val)
        elif k == "BACKEND_URL":
            cfg.backend.url = val
        elif k == "API_KEY":
            cfg.backend.api_key = val
            cfg.backend.enabled = True
        elif k == "HEALTH_PORT":
            cfg.health.port = int(val)
