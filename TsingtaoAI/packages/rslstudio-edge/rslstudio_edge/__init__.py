"""RSLStudio Edge Agent — 实时视频采集 → MinIO 直传"""

from .agent import EdgeAgent, run_from_config
from .config import AgentConfig, load_config

__version__ = "1.0.0"
__all__ = ["EdgeAgent", "AgentConfig", "load_config", "run_from_config"]
