from __future__ import annotations

import logging
from pathlib import Path
from typing import List
from typing import Optional

import typer

import rslstudio.core
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import FileQuery
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery
from rslstudio.config import get_shared_state
from rslstudio.utils import split_args

logger = logging.getLogger(__name__)

HELP = """\
从 RslStudio 下载文件。
"""


download_typer = typer.Typer(name="download", no_args_is_help=True, invoke_without_command=True, help=HELP)


@download_typer.callback()
def download(
    files: Optional[List[str]] = typer.Argument(None, help="文件名、ID 或模式"),
    projects: Optional[List[str]] = typer.Option(None, "--project", "-p", help="项目名称、ID 或模式"),
    missions: Optional[List[str]] = typer.Option(None, "--mission", "-m", help="任务名称、ID 或模式"),
    dest: str = typer.Option(prompt="目标路径", help="保存文件的本地路径"),
    nested: bool = typer.Option(False, help="按项目名称/任务名称嵌套目录保存文件"),
    overwrite: bool = typer.Option(
        False,
        help="若文件已存在且大小或哈希不匹配则覆盖",
    ),
    include_corrupt_files: bool = typer.Option(
        False,
        help="下载标记为损坏的文件（可能有风险，请谨慎使用）",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="跳过所有确认提示",
    ),
    allow_corrupt: bool = typer.Option(
        False,
        "--allow-corrupt",
        help="跳过下载损坏文件的确认提示",
    ),
    create_dirs: bool = typer.Option(
        False,
        "--create-dirs",
        help="自动创建缺失的目标目录（无需确认）",
    ),
) -> None:
    if include_corrupt_files:
        typer.secho(
            "警告：--include-corrupt-files 会下载标记为损坏的文件。"
            "这些文件可能有害，请勿盲目执行或打开。",
            fg=typer.colors.YELLOW,
            err=True,
        )
        if not (yes or allow_corrupt):
            typer.confirm("是否继续？可使用 --yes 或 --allow-corrupt 跳过此提示。", abort=True)

    # create destination directory
    dest_dir = Path(dest)
    if not dest_dir.exists():
        if not (yes or create_dirs):
            typer.confirm(
                f"目标路径 {dest_dir} 不存在，是否创建？可使用 --yes 或 --create-dirs 跳过此提示。",
                abort=True,
            )
    dest_dir.mkdir(parents=True, exist_ok=True)

    # get file query
    file_ids, file_patterns = split_args(files or [])
    mission_ids, mission_patterns = split_args(missions or [])
    project_ids, project_patterns = split_args(projects or [])

    project_query = ProjectQuery(patterns=project_patterns, ids=project_ids)
    mission_query = MissionQuery(
        patterns=mission_patterns,
        ids=mission_ids,
        project_query=project_query,
    )
    file_query = FileQuery(patterns=file_patterns, ids=file_ids, mission_query=mission_query)

    rslstudio.core.download(
        client=AuthenticatedClient(),
        query=file_query,
        allow_corrupt_files=include_corrupt_files,
        base_dir=dest_dir,
        nested=nested,
        overwrite=overwrite,
        verbose=get_shared_state().verbose,
    )
