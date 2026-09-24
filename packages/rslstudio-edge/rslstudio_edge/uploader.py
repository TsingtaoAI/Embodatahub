"""MinIO/S3 上传器 — 带重试和指标收集"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig

from .config import MinioConfig

log = logging.getLogger("edge.uploader")


class Uploader:
    """S3 上传器，支持断点续传"""

    def __init__(self, cfg: MinioConfig):
        boto_cfg = BotoConfig(
            retries={"max_attempts": 10, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=120,
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=cfg.access_key,
            aws_secret_access_key=cfg.secret_key,
            config=boto_cfg,
            region_name="us-east-1",
        )
        self.bucket = cfg.bucket
        self._total_bytes = 0
        self._total_segments = 0
        self._errors = 0

    def upload(self, local_path: Path, remote_key: str, metadata: dict | None = None) -> dict:
        """上传文件，返回 {key, size, md5, elapsed}"""
        md5 = _file_md5(local_path)
        size = local_path.stat().st_size
        extra = {"ContentType": "video/mp4"}
        if metadata:
            extra["Metadata"] = {k: str(v) for k, v in metadata.items()}

        t0 = time.time()
        self.client.upload_file(str(local_path), self.bucket, remote_key, ExtraArgs=extra)
        elapsed = time.time() - t0

        self._total_bytes += size
        self._total_segments += 1

        return {"key": remote_key, "size": size, "md5": md5, "elapsed": elapsed}

    @property
    def stats(self) -> dict:
        return {
            "total_segments": self._total_segments,
            "total_bytes": self._total_bytes,
            "errors": self._errors,
        }


def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
