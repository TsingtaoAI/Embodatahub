"""边缘采集代理主控 — 编排采集 → 上传 → 清理流水线"""

from __future__ import annotations

import logging
import shutil
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

from prometheus_client import CollectorRegistry

from .capture import FFmpegCapture
from .config import AgentConfig, load_config
from .metrics import EdgeMetrics, start_health_server
from .uploader import Uploader

log = logging.getLogger("edge.agent")


def _format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


class EdgeAgent:
    """边缘采集代理"""

    def __init__(self, config: AgentConfig):
        self.cfg = config
        self.work_dir = Path(f"/tmp/rslstudio-edge-{config.mission}")
        self.capture = FFmpegCapture(config.video, self.work_dir)
        self.uploader = Uploader(config.minio)
        self.registry = CollectorRegistry()
        self.metrics = EdgeMetrics(self.registry)
        self._stop = False
        self._queue_depth = 0

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._on_stop)
        signal.signal(signal.SIGTERM, self._on_stop)

        # 启动健康检查
        start_health_server(self.cfg.health.port, self.cfg.health.bind, self.registry)

        self._print_banner()

        try:
            self.capture.start()
            self.metrics.stream_healthy.labels(
                mission=self.cfg.mission, source=self.cfg.video.source
            ).set(1)
            self._loop()
        except Exception as e:
            log.error(f"代理异常: {e}")
            raise
        finally:
            self._cleanup()

    def _loop(self) -> None:
        while not self._stop:
            # 监控采集进程健康
            if not self.capture.monitor():
                self.metrics.stream_healthy.labels(
                    mission=self.cfg.mission, source=self.cfg.video.source
                ).set(0)
            else:
                self.metrics.stream_healthy.labels(
                    mission=self.cfg.mission, source=self.cfg.video.source
                ).set(1)
                self.metrics.stream_uptime.labels(
                    mission=self.cfg.mission
                ).set(self.capture.uptime_seconds)

            # 收集已完成分段
            segments = self.capture.collect_segments()
            self._queue_depth = len(segments)
            self.metrics.queue_depth.labels(mission=self.cfg.mission).set(self._queue_depth)

            for seg in segments:
                if self._stop:
                    break
                self._process_segment(seg)

            time.sleep(0.5)

    def _process_segment(self, seg: Path) -> None:
        ts = datetime.now(timezone.utc).strftime("%H%M%S")
        key = f"{self.cfg.s3_prefix}{ts}_{seg.name}"

        try:
            result = self.uploader.upload(seg, key, metadata={
                "mission": self.cfg.mission,
                "source": self.cfg.video.source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            log.error(f"上传失败 {seg.name}: {e}")
            self.metrics.errors_total.labels(
                mission=self.cfg.mission, type="upload"
            ).inc()
            return

        speed = result["size"] / result["elapsed"] / 1e6 if result["elapsed"] > 0 else 0
        total = self.uploader.stats["total_segments"]
        log.info(
            f"📤 #{total:04d}  {seg.name}  "
            f"{_format_size(result['size'])}  {speed:.1f} MB/s  "
            f"→ s3://{self.cfg.minio.bucket}/{key}"
        )

        self.metrics.segments_uploaded.labels(mission=self.cfg.mission).inc()
        self.metrics.bytes_uploaded.labels(mission=self.cfg.mission).inc(result["size"])
        self.metrics.upload_duration.labels(mission=self.cfg.mission).observe(result["elapsed"])

        seg.unlink()
        self._queue_depth = max(0, self._queue_depth - 1)

    def _on_stop(self, signum, frame):
        log.info("收到停止信号，正在退出...")
        self._stop = True

    def _cleanup(self) -> None:
        self.capture.stop()

        # 上传残留分段
        remaining = sorted(self.work_dir.glob("seg_*.mp4"))
        for seg in remaining:
            try:
                self._process_segment(seg)
            except Exception as e:
                log.error(f"清理上传失败 {seg.name}: {e}")
                self.metrics.errors_total.labels(
                    mission=self.cfg.mission, type="cleanup"
                ).inc()

        try:
            shutil.rmtree(self.work_dir)
        except Exception:
            pass

        self.metrics.stream_healthy.labels(
            mission=self.cfg.mission, source=self.cfg.video.source
        ).set(0)

        stats = self.uploader.stats
        log.info("=" * 60)
        log.info("📊 采集会话完成")
        log.info(f"   任务:     {self.cfg.mission}")
        log.info(f"   总分段:   {stats['total_segments']}")
        log.info(f"   总数据:   {_format_size(stats['total_bytes'])}")
        log.info(f"   重连次:   {self.capture.reconnect_count}")
        log.info(f"   错误数:   {stats['errors']}")
        log.info(f"   S3:       s3://{self.cfg.minio.bucket}/{self.cfg.s3_prefix}")
        log.info(f"   健康检查: http://{self.cfg.health.bind}:{self.cfg.health.port}/health")
        log.info("=" * 60)

    def _print_banner(self) -> None:
        log.info("=" * 60)
        log.info("🚀 RSLStudio Edge Agent v1.0")
        log.info(f"   采集源:   {self.cfg.video.source}")
        log.info(f"   任务:     {self.cfg.mission}")
        log.info(f"   分辨率:   {self.cfg.video.resolution} @ {self.cfg.video.fps}fps")
        log.info(f"   分段:     {self.cfg.video.segment_seconds}s")
        log.info(f"   存储:     {self.cfg.minio.endpoint_url}/{self.cfg.minio.bucket}")
        log.info(f"   平台集成: {'✅ 已启用' if self.cfg.backend else '⏭ 未启用'}")
        log.info(f"   健康检查: http://{self.cfg.health.bind}:{self.cfg.health.port}/health")
        log.info("=" * 60)


def run_from_config(config_path: str | None = None) -> None:
    """从配置文件启动代理"""
    cfg = load_config(config_path)
    agent = EdgeAgent(cfg)
    agent.run()
