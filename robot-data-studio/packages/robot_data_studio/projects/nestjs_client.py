"""
HTTP client for calling the RSLStudio NestJS backend to persist
RDS dataset metadata, cleaning results, and filter results.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from robot_data_studio.lerobot.models import DatasetMetadata, EpisodeSummary
from robot_data_studio.quality import CleaningSummary, FilterSummary

logger = logging.getLogger(__name__)

RSLSTUDIO_API_URL = os.environ.get(
    "RSLSTUDIO_API_URL", "http://localhost:3000"
).rstrip("/")


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST JSON to the NestJS backend and return the JSON response."""
    url = f"{RSLSTUDIO_API_URL}{path}"
    data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        logger.error(
            "NestJS API error %s %s: %s",
            exc.code,
            path,
            exc.read().decode("utf-8", errors="replace")[:500],
        )
        raise
    except URLError as exc:
        logger.error("NestJS API unreachable %s: %s", path, exc)
        raise


def _get_json(path: str) -> dict[str, Any]:
    """GET JSON from the NestJS backend."""
    url = f"{RSLSTUDIO_API_URL}{path}"
    req = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        logger.error(
            "NestJS API error %s %s: %s",
            exc.code,
            path,
            exc.read().decode("utf-8", errors="replace")[:500],
        )
        raise
    except URLError as exc:
        logger.error("NestJS API unreachable %s: %s", path, exc)
        raise


def create_rds_dataset(
    name: str,
    path: str,
    metadata: DatasetMetadata,
    project_uuid: str,
) -> dict[str, Any]:
    """Create a dataset record in the NestJS database, linked to a project."""
    return _post_json(
        "/rds/datasets",
        {
            "name": name,
            "path": path,
            "format": metadata.format,
            "version": metadata.version,
            "totalEpisodes": metadata.total_episodes,
            "totalFrames": metadata.total_frames,
            "fps": metadata.fps,
            "robotType": metadata.robot_type,
            "videoKeys": metadata.video_keys,
            "features": metadata.features,
            "projectUuid": project_uuid,
        },
    )


def save_structured_results(
    dataset_uuid: str,
    episodes: list[EpisodeSummary],
    cleaning_summary: CleaningSummary,
    filter_summary: FilterSummary,
) -> dict[str, Any]:
    """Save the complete structured processing results to NestJS.

    Args:
        dataset_uuid: UUID of the dataset in NestJS
        episodes: List of episode summaries from the reader
        cleaning_summary: Complete cleaning summary with per-episode results
        filter_summary: Complete filter summary with per-episode-per-stage results
    """
    episode_payloads = [
        {
            "episodeIndex": ep.episode_index,
            "durationSeconds": ep.duration_seconds,
            "length": ep.length,
            "tasks": ep.tasks,
            "subtasks": [
                subtask.model_dump(mode="json") for subtask in (ep.subtasks or [])
            ],
            "dataFile": ep.data_file,
            "videoFiles": ep.video_files,
        }
        for ep in episodes
    ]

    cleaning_payloads = [
        {
            "episodeIndex": result.episode_index,
            "score": result.score,
            "status": result.status,
            "source": result.source,
            "perAttributeScores": result.per_attribute_scores,
            "findings": [
                finding.model_dump(mode="json")
                for finding in (result.findings or [])
            ],
            "reviewNote": result.review_note,
            "scorerVersion": cleaning_summary.scorer_version,
        }
        for result in cleaning_summary.results
    ]

    filter_payloads = []
    if filter_summary and filter_summary.episodes:
        for episode_filter in filter_summary.episodes:
            for stage_id, status in episode_filter.stage_status.items():
                filter_payloads.append({
                    "episodeIndex": episode_filter.episode_index,
                    "stageId": stage_id,
                    "count": status.count,
                    "skippedReason": status.skipped_reason or "",
                    "findings": [
                        finding.model_dump(mode="json")
                        for finding in (status.findings or [])
                    ],
                })

    payload = {
        "dataset": {
            "name": "",
            "path": "",
            "format": "",
            "version": "",
            "totalEpisodes": len(episodes),
            "totalFrames": sum(ep.length for ep in episodes),
            "fps": 0,
            "robotType": "",
            "projectUuid": "",
        },
        "episodes": episode_payloads,
        "cleaningResults": cleaning_payloads,
        "filterResults": filter_payloads,
    }

    return _post_json(f"/rds/datasets/{dataset_uuid}/results", payload)


def get_rds_datasets(project_uuid: str) -> list[dict[str, Any]]:
    """Get all datasets for a project."""
    return _get_json(f"/rds/projects/{project_uuid}/datasets")
