"""FFmpeg 视频采集 — 分段录制 + 自动重连"""

from __future__ import annotations

import logging
import subprocess
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import VideoConfig

log = logging.getLogger("edge.capture")


class CaptureError(Exception):
    """采集错误"""
    pass


class FFmpegCapture:
    """FFmpeg 分段视频采集，支持断流自动重连"""

    MAX_RECONNECT_ATTEMPTS = 20
    RECONNECT_BASE_DELAY = 2.0
    RECONNECT_MAX_DELAY = 120.0

    def __init__(self, cfg: VideoConfig, work_dir: Path):
        self.cfg = cfg
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._process: Optional[subprocess.Popen] = None
        self._segment_index = 0
        self._reconnect_count = 0
        self._healthy = False
        self._started_at: Optional[datetime] = None

    def _ffmpeg_cmd(self) -> list[str]:
        segment_pattern = str(self.work_dir / "seg_%06d.mp4")

        if "/dev/video" in self.cfg.source:
            input_args = ["-f", "v4l2", "-framerate", str(self.cfg.fps),
                          "-i", self.cfg.source]
        elif self.cfg.source.startswith("rtsp://"):
            input_args = ["-rtsp_transport", "tcp",
                          "-stimeout", "5000000",
                          "-i", self.cfg.source]
        else:
            input_args = ["-i", self.cfg.source]

        return [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            *input_args,
            "-c:v", self.cfg.codec,
            "-preset", self.cfg.preset,
            "-crf", str(self.cfg.crf),
            "-vf", f"scale={self.cfg.resolution},fps={self.cfg.fps}",
            "-an",
            "-f", "segment",
            "-segment_time", str(self.cfg.segment_seconds),
            "-segment_format", "mp4",
            "-reset_timestamps", "1",
            segment_pattern,
        ]

    def start(self) -> None:
        """启动采集，失败自动重试"""
        while self._reconnect_count < self.MAX_RECONNECT_ATTEMPTS:
            try:
                self._launch_ffmpeg()
                self._healthy = True
                self._started_at = datetime.now()
                self._reconnect_count = 0
                return
            except CaptureError as e:
                self._reconnect_count += 1
                delay = min(
                    self.RECONNECT_BASE_DELAY ** self._reconnect_count,
                    self.RECONNECT_MAX_DELAY,
                )
                log.warning(
                    f"⏳ 采集启动失败 (尝试 {self._reconnect_count}/{self.MAX_RECONNECT_ATTEMPTS}): {e}"
                )
                log.info(f"   {delay:.0f}s 后重试...")
                time.sleep(delay)

        raise CaptureError(
            f"无法启动采集，已达最大重试次数 ({self.MAX_RECONNECT_ATTEMPTS})"
        )

    def _launch_ffmpeg(self) -> None:
        cmd = self._ffmpeg_cmd()
        log.info(f"🎬 FFmpeg: {' '.join(cmd[:5])} ...")
        self._process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        time.sleep(1.5)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read().decode(errors="replace") if self._process.stderr else ""
            raise CaptureError(f"FFmpeg 立即退出: {stderr[-200:]}")

    def monitor(self) -> bool:
        """监控采集进程，自动重连"""
        if self._process is None:
            return False
        exit_code = self._process.poll()
        if exit_code is None:
            return True  # 正常运行

        # 进程退出 — 尝试重连
        stderr = ""
        try:
            stderr = self._process.stderr.read().decode(errors="replace")[-200:]
        except Exception:
            pass
        log.warning(f"⚠️ FFmpeg 退出 (code={exit_code}): {stderr}")
        self._healthy = False
        self._try_reconnect()
        return self._healthy

    def _try_reconnect(self) -> None:
        for attempt in range(1, self.MAX_RECONNECT_ATTEMPTS + 1):
            delay = min(self.RECONNECT_BASE_DELAY ** attempt, self.RECONNECT_MAX_DELAY)
            log.info(f"🔄 重连 {attempt}/{self.MAX_RECONNECT_ATTEMPTS} ({delay:.0f}s 后)...")
            time.sleep(delay)
            try:
                self._launch_ffmpeg()
                self._healthy = True
                self._reconnect_count += 1
                log.info("✅ 重连成功")
                return
            except CaptureError:
                continue
        log.error("❌ 重连失败，已达最大尝试次数")

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            log.info("⏹ 停止采集...")
            self._process.send_signal(signal.SIGINT)
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._healthy = False

    @property
    def healthy(self) -> bool:
        return self._healthy

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def uptime_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        return (datetime.now() - self._started_at).total_seconds()

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count

    def collect_segments(self) -> list[Path]:
        """收集已完成的 .mp4 分段（排除正在写入的最后一个）"""
        all_segs = sorted(self.work_dir.glob("seg_*.mp4"))
        if not all_segs:
            return []
        completed = all_segs[:-1] if len(all_segs) > 1 else []
        result = []
        for seg in completed:
            idx = int(seg.stem.split("_")[1])
            if idx > self._segment_index:
                result.append(seg)
        if result:
            self._segment_index = max(int(s.stem.split("_")[1]) for s in result)
        return result
