"""Prometheus 健康检查和指标暴露"""

from __future__ import annotations

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from prometheus_client import (
    Counter, Gauge, Histogram, generate_latest,
    REGISTRY, CollectorRegistry,
)


class EdgeMetrics:
    """边缘代理指标收集"""

    def __init__(self, registry: CollectorRegistry | None = None):
        self._registry = registry or REGISTRY

        self.segments_uploaded = Counter(
            "edge_segments_uploaded_total",
            "已上传分段总数",
            ["mission"], registry=self._registry,
        )
        self.bytes_uploaded = Counter(
            "edge_bytes_uploaded_total",
            "已上传字节总数",
            ["mission"], registry=self._registry,
        )
        self.upload_duration = Histogram(
            "edge_upload_duration_seconds",
            "单次上传耗时",
            ["mission"], buckets=[0.5, 1, 2, 5, 10, 30, 60],
            registry=self._registry,
        )
        self.reconnect_total = Counter(
            "edge_reconnect_total",
            "FFmpeg 重连次数",
            ["mission"], registry=self._registry,
        )
        self.stream_healthy = Gauge(
            "edge_stream_healthy",
            "采集流健康状态 (1=正常, 0=断开)",
            ["mission", "source"], registry=self._registry,
        )
        self.stream_uptime = Gauge(
            "edge_stream_uptime_seconds",
            "采集流持续运行时间",
            ["mission"], registry=self._registry,
        )
        self.queue_depth = Gauge(
            "edge_queue_depth",
            "待上传分段队列长度",
            ["mission"], registry=self._registry,
        )
        self.errors_total = Counter(
            "edge_errors_total",
            "错误总数",
            ["mission", "type"], registry=self._registry,
        )


class HealthHandler(BaseHTTPRequestHandler):
    """轻量 HTTP 处理器 — /health 和 /metrics"""

    metrics_registry: CollectorRegistry | None = None

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, '{"status":"ok","service":"rslstudio-edge"}')
        elif self.path == "/metrics":
            data = generate_latest(self.metrics_registry)
            self._respond(200, data, "text/plain; charset=utf-8")
        else:
            self._respond(404, '{"error":"not found"}')

    def _respond(self, code: int, body: str | bytes, ct: str = "application/json"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # 静默


def start_health_server(port: int, bind: str, registry: CollectorRegistry) -> threading.Thread:
    """启动健康检查 HTTP 服务（后台线程）"""
    HealthHandler.metrics_registry = registry
    server = HTTPServer((bind, port), HealthHandler)

    def _serve():
        server.serve_forever()

    t = threading.Thread(target=_serve, daemon=True, name="health-server")
    t.start()
    return t
