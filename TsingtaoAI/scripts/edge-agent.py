#!/usr/bin/env python3
"""
边缘采集代理 — 实时视频流分段采集 → MinIO 直传

用法:
  # USB 摄像头
  python edge-agent.py --source /dev/video0 --mission my-mission

  # RTSP 流
  python edge-agent.py --source rtsp://192.168.1.50:554/stream --mission robot-cam0

  # 带平台注册（需要 API Key）
  python edge-agent.py --source /dev/video0 --mission my-mission \
      --api-key YOUR_KEY --backend http://192.168.1.107:3000

依赖:
  pip install boto3 httpx python-dotenv
  系统需安装 ffmpeg
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from dotenv import load_dotenv

# ─── 默认配置 ──────────────────────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_MINIO_ENDPOINT = os.getenv("S3_ENDPOINT", "192.168.1.107") + ":9000"
DEFAULT_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
DEFAULT_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
DEFAULT_BUCKET = "data"
DEFAULT_SEGMENT_SECONDS = 10
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("edge-agent")


# ─── 配置 ──────────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
    source: str                          # 视频源: /dev/video0 或 rtsp://...
    mission: str                         # 采集任务名称
    segment_seconds: int = DEFAULT_SEGMENT_SECONDS
    bucket: str = DEFAULT_BUCKET
    minio_endpoint: str = DEFAULT_MINIO_ENDPOINT
    minio_access_key: str = DEFAULT_ACCESS_KEY
    minio_secret_key: str = DEFAULT_SECRET_KEY
    # 可选：平台集成
    backend_url: str = DEFAULT_BACKEND_URL
    api_key: Optional[str] = None        # API Key，设置后自动注册分段到平台
    project: Optional[str] = None        # 平台项目名
    # 视频参数
    resolution: str = "1280x720"
    fps: int = 30
    codec: str = "libx264"
    preset: str = "ultrafast"
    crf: int = 23

    @property
    def s3_prefix(self) -> str:
        """S3 对象前缀：streams/{mission}/{date}/"""
        today = datetime.now().strftime("%Y%m%d")
        return f"streams/{self.mission}/{today}/"


# ─── S3 上传 ───────────────────────────────────────────────────────────

class S3Uploader:
    """MinIO S3 上传器"""

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        boto_cfg = BotoConfig(
            retries={"max_attempts": 10, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=60,
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=f"http://{cfg.minio_endpoint}",
            aws_access_key_id=cfg.minio_access_key,
            aws_secret_access_key=cfg.minio_secret_key,
            config=boto_cfg,
            region_name="us-east-1",
        )

    def upload(self, local_path: Path, remote_key: str) -> dict:
        """上传文件到 MinIO，返回对象元数据"""
        md5 = _file_md5(local_path)
        size = local_path.stat().st_size

        self.client.upload_file(
            str(local_path),
            self.cfg.bucket,
            remote_key,
            ExtraArgs={
                "Metadata": {
                    "md5": md5,
                    "mission": self.cfg.mission,
                    "source": self.cfg.source,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "ContentType": "video/mp4",
            },
        )
        return {"key": remote_key, "size": size, "md5": md5, "bucket": self.cfg.bucket}


# ─── 后端 API ──────────────────────────────────────────────────────────

class BackendClient:
    """RSLStudio 平台 API 客户端（可选）"""

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.base = cfg.backend_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": cfg.api_key or "",
        } if cfg.api_key else {}

    def _post(self, path: str, data: dict) -> dict:
        import httpx
        resp = httpx.post(
            f"{self.base}{path}", json=data, headers=self.headers, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def register_segment(self, key: str, size: int, md5: str) -> Optional[str]:
        """向平台注册一个分段文件，返回文件 UUID"""
        if not self.cfg.api_key:
            return None
        try:
            result = self._post("/files/upload/confirm", {
                "uuid": key.rsplit("/", 1)[-1].replace(".mp4", ""),
                "md5": md5,
                "size": size,
                "source": "EDGE_AGENT",
                "metadata": {
                    "mission": self.cfg.mission,
                    "type": "video_segment",
                    "source": self.cfg.source,
                },
            })
            return result.get("uuid")
        except Exception as e:
            log.warning(f"平台注册失败 (非致命): {e}")
            return None


# ─── FFmpeg 采集 ───────────────────────────────────────────────────────

class FFmpegCapture:
    """FFmpeg 分段视频采集"""

    def __init__(self, cfg: AgentConfig, work_dir: Path):
        self.cfg = cfg
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._process: Optional[subprocess.Popen] = None
        self._segment_index = 0

    def _ffmpeg_cmd(self) -> list[str]:
        """构建 FFmpeg 分段录制命令"""
        segment_pattern = str(self.work_dir / f"seg_%06d.mp4")

        # 探测输入格式
        if self.cfg.source.startswith("/dev/video"):
            input_args = ["-f", "v4l2", "-framerate", str(self.cfg.fps)]
        elif self.cfg.source.startswith("rtsp://"):
            input_args = ["-rtsp_transport", "tcp", "-i", self.cfg.source]
        else:
            input_args = ["-i", self.cfg.source]

        return [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            *input_args,
            "-c:v", self.cfg.codec,
            "-preset", self.cfg.preset,
            "-crf", str(self.cfg.crf),
            "-vf", f"scale={self.cfg.resolution},fps={self.cfg.fps}",
            "-an",                          # 暂不录制音频
            "-f", "segment",
            "-segment_time", str(self.cfg.segment_seconds),
            "-segment_format", "mp4",
            "-reset_timestamps", "1",
            "-strftime", "0",
            segment_pattern,
        ]

    def start(self) -> None:
        """启动 FFmpeg 采集进程"""
        cmd = self._ffmpeg_cmd()
        log.info(f"🎬 启动采集: {' '.join(cmd[:6])} ...")
        self._process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        # 等待第一个分段文件出现
        time.sleep(2)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read().decode() if self._process.stderr else ""
            raise RuntimeError(f"FFmpeg 启动失败: {stderr}")

    def stop(self) -> None:
        """停止采集"""
        if self._process and self._process.poll() is None:
            log.info("⏹ 停止采集...")
            self._process.send_signal(signal.SIGINT)
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def collect_segments(self) -> list[Path]:
        """收集已完成的 .mp4 分段文件，不包括正在写入的"""
        all_segs = sorted(self.work_dir.glob("seg_*.mp4"))
        if not all_segs:
            return []

        # 保留最后一个（可能正在写入中）
        completed = all_segs[:-1] if len(all_segs) > 1 else []
        result = []
        for seg in completed:
            idx = int(seg.stem.split("_")[1])
            if idx > self._segment_index:
                result.append(seg)
        if result:
            self._segment_index = max(int(s.stem.split("_")[1]) for s in result)
        return result


# ─── 工具函数 ──────────────────────────────────────────────────────────

def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ─── 主循环 ────────────────────────────────────────────────────────────

class EdgeAgent:
    """边缘采集代理主控"""

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.work_dir = Path(f"/tmp/edge-agent-{cfg.mission}")
        self.capture = FFmpegCapture(cfg, self.work_dir)
        self.uploader = S3Uploader(cfg)
        self.backend = BackendClient(cfg)
        self.stats = {"segments": 0, "bytes": 0, "errors": 0}
        self._stop = False

    def run(self) -> None:
        """主循环"""
        signal.signal(signal.SIGINT, self._on_stop)
        signal.signal(signal.SIGTERM, self._on_stop)

        log.info("=" * 60)
        log.info(f"🚀 边缘采集代理启动")
        log.info(f"   采集源:   {self.cfg.source}")
        log.info(f"   任务名:   {self.cfg.mission}")
        log.info(f"   分段时长: {self.cfg.segment_seconds}s")
        log.info(f"   MinIO:    {self.cfg.minio_endpoint}/{self.cfg.bucket}")
        log.info(f"   S3 前缀:  {self.cfg.s3_prefix}")
        if self.cfg.api_key:
            log.info(f"   平台注册: {self.cfg.backend_url} ✅")
        else:
            log.info(f"   平台注册: 未启用（设置 --api-key 以自动注册）")
        log.info("=" * 60)

        self.capture.start()

        try:
            self._loop()
        finally:
            self._cleanup()

    def _loop(self) -> None:
        """采集 → 上传 → 清理循环"""
        while not self._stop and self.capture.running:
            segments = self.capture.collect_segments()

            for seg in segments:
                if self._stop:
                    break
                try:
                    self._process_segment(seg)
                except Exception as e:
                    log.error(f"处理分段失败 {seg.name}: {e}")
                    self.stats["errors"] += 1

            time.sleep(0.5)

    def _process_segment(self, seg: Path) -> None:
        """处理单个分段：上传 + 注册 + 清理"""
        timestamp = datetime.now().strftime("%H%M%S")
        remote_key = f"{self.cfg.s3_prefix}{timestamp}_{seg.name}"

        # 上传
        t0 = time.time()
        result = self.uploader.upload(seg, remote_key)
        elapsed = time.time() - t0
        speed = result["size"] / elapsed / 1024 / 1024 if elapsed > 0 else 0

        self.stats["segments"] += 1
        self.stats["bytes"] += result["size"]

        log.info(
            f"📤 #{self.stats['segments']:04d}  {seg.name}  "
            f"{_format_size(result['size'])}  {speed:.1f} MB/s  "
            f"→ s3://{result['bucket']}/{result['key']}"
        )

        # 可选：注册到平台
        file_id = self.backend.register_segment(
            result["key"], result["size"], result["md5"]
        )
        if file_id:
            log.debug(f"   平台注册: {file_id}")

        # 清理本地分段
        seg.unlink()

    def _on_stop(self, signum, frame):
        log.info("收到停止信号，正在退出...")
        self._stop = True

    def _cleanup(self) -> None:
        """停止采集，上传剩余分段，清理临时目录"""
        self.capture.stop()

        # 上传残留分段
        remaining = sorted(self.work_dir.glob("seg_*.mp4"))
        for seg in remaining:
            try:
                self._process_segment(seg)
            except Exception as e:
                log.error(f"清理上传失败 {seg.name}: {e}")

        # 删除临时目录
        import shutil
        try:
            shutil.rmtree(self.work_dir)
        except Exception:
            pass

        # 打印统计
        log.info("=" * 60)
        log.info(f"📊 采集完成")
        log.info(f"   总分段数: {self.stats['segments']}")
        log.info(f"   总数据量: {_format_size(self.stats['bytes'])}")
        log.info(f"   错误数:   {self.stats['errors']}")
        log.info(f"   MinIO:    {self.cfg.minio_endpoint}/{self.cfg.bucket}")
        log.info("=" * 60)


# ─── 命令行入口 ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="边缘采集代理 — 实时视频 → 分段 MP4 → MinIO 直传",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --source /dev/video0 --mission my-robot-cam
  %(prog)s --source rtsp://192.168.1.50:554/stream --mission robot-cam0
  %(prog)s --source /dev/video0 --mission demo --api-key xxx --project my-project
        """,
    )
    parser.add_argument("--source", "-s", required=True,
                        help="视频源: /dev/video0 或 rtsp://host/stream")
    parser.add_argument("--mission", "-m", required=True,
                        help="采集任务名称")
    parser.add_argument("--segment", "-t", type=int, default=DEFAULT_SEGMENT_SECONDS,
                        help=f"分段时长（秒），默认 {DEFAULT_SEGMENT_SECONDS}")
    parser.add_argument("--resolution", "-r", default="1280x720",
                        help="视频分辨率，默认 1280x720")
    parser.add_argument("--fps", type=int, default=30,
                        help="帧率，默认 30")
    parser.add_argument("--minio-endpoint", default=DEFAULT_MINIO_ENDPOINT,
                        help=f"MinIO 地址，默认 {DEFAULT_MINIO_ENDPOINT}")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET,
                        help=f"S3 Bucket，默认 {DEFAULT_BUCKET}")
    parser.add_argument("--backend", default=DEFAULT_BACKEND_URL,
                        help=f"平台后端地址，默认 {DEFAULT_BACKEND_URL}")
    parser.add_argument("--api-key", default=None,
                        help="平台 API Key（可选，设置后自动注册分段）")
    parser.add_argument("--project", default=None,
                        help="平台项目名（配合 --api-key 使用）")
    parser.add_argument("--crf", type=int, default=23,
                        help="视频质量 CRF，越小质量越高（默认 23）")

    args = parser.parse_args()

    # 验证 FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ 未找到 ffmpeg，请先安装: sudo apt install ffmpeg")
        sys.exit(1)

    cfg = AgentConfig(
        source=args.source,
        mission=args.mission,
        segment_seconds=args.segment,
        bucket=args.bucket,
        minio_endpoint=args.minio_endpoint,
        backend_url=args.backend,
        api_key=args.api_key,
        project=args.project,
        resolution=args.resolution,
        fps=args.fps,
        crf=args.crf,
    )

    agent = EdgeAgent(cfg)
    agent.run()


if __name__ == "__main__":
    main()
