"""CLI 入口 — rslstudio-edge 命令"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys

from .agent import run_from_config


def main():
    parser = argparse.ArgumentParser(
        prog="rslstudio-edge",
        description="RSLStudio 边缘采集代理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  rslstudio-edge --config config.yaml
  rslstudio-edge --source /dev/video0 --mission robot-cam0
  rslstudio-edge --source rtsp://192.168.1.50/stream --mission cam1 --segment 15

环境变量 (EDGE_ 前缀):
  EDGE_SOURCE, EDGE_MISSION, EDGE_MINIO_ENDPOINT, EDGE_MINIO_ACCESS_KEY,
  EDGE_MINIO_SECRET_KEY, EDGE_SEGMENT_SECONDS, EDGE_HEALTH_PORT
        """,
    )

    # 配置文件
    parser.add_argument("--config", "-c", default=None, help="YAML 配置文件路径")

    # 快速覆盖
    parser.add_argument("--source", "-s", help="视频源")
    parser.add_argument("--mission", "-m", help="采集任务名称")
    parser.add_argument("--segment", "-t", type=int, help="分段时长（秒）")
    parser.add_argument("--resolution", "-r", default="1280x720", help="分辨率")
    parser.add_argument("--fps", type=int, default=30, help="帧率")
    parser.add_argument("--minio-endpoint", default="192.168.1.107:9000")
    parser.add_argument("--bucket", default="data")
    parser.add_argument("--health-port", type=int, default=9091)
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")

    args = parser.parse_args()

    # 日志级别
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # 检查 FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ 未找到 ffmpeg，请先安装: sudo apt install ffmpeg")
        sys.exit(1)

    # 用命令行参数设置环境变量（供 config.py 读取）
    import os
    overrides = {
        "source": args.source,
        "mission": args.mission,
        "segment_seconds": args.segment,
        "resolution": args.resolution,
        "fps": args.fps,
        "minio_endpoint": args.minio_endpoint,
        "bucket": args.bucket,
        "health_port": args.health_port,
    }
    for k, v in overrides.items():
        if v is not None:
            os.environ[f"EDGE_{k.upper()}"] = str(v)

    run_from_config(args.config)


if __name__ == "__main__":
    main()
