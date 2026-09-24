from __future__ import annotations

from pathlib import Path
from typing import List
from typing import Optional

import typer

import rslstudio.core
import rslstudio.utils
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery
from rslstudio.cli._file_validator import FileValidator
from rslstudio.cli._file_validator import _report_skipped_files
from rslstudio.config import get_shared_state
from rslstudio.errors import MissionNotFound
from rslstudio.utils import load_metadata
from rslstudio.utils import split_args

HELP = """\
上传文件到 RslStudio。
"""

upload_typer = typer.Typer(
    name="upload",
    no_args_is_help=True,
    invoke_without_command=True,
    help=HELP,
)


def _build_mission_query(mission: str, project: Optional[str]) -> MissionQuery:
    """Constructs the MissionQuery object from CLI args."""
    mission_ids, mission_patterns = split_args([mission])
    project_ids, project_patterns = split_args([project] if project else [])

    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)
    return MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )


def _handle_no_files_to_upload(original_count: int, uploaded_count: int) -> None:
    """Checks if any files are left to upload and exits if not."""
    if uploaded_count > 0:
        return

    if original_count > 0:
        typer.echo(
            typer.style("所有路径均被跳过，没有文件可上传。", fg=typer.colors.RED),
            err=True,
        )
    else:
        typer.echo(typer.style("未提供要上传的文件。", fg=typer.colors.RED), err=True)
    raise typer.Exit(code=1)


@upload_typer.callback()
def upload(
    files: List[str] = typer.Argument(help="要上传的文件"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称"),
    mission: str = typer.Option(..., "--mission", "-m", help="任务 ID 或名称"),
    create: bool = typer.Option(False, help="如果任务不存在则创建"),
    metadata: Optional[str] = typer.Option(None, help="元数据文件路径（json 或 yaml）"),
    fix_filenames: bool = typer.Option(
        False,
        help="上传前修复文件名（不会修改本地文件名）",
    ),
    skip: bool = typer.Option(
        False,
        "--skip",
        "-s",
        help="跳过不支持的文件类型、命名错误的文件或目录（而不是报错）",
    ),
    experimental_datatypes: bool = typer.Option(False, help="允许实验性数据类型（yaml, svo2, db3, tum）"),
    ignore_missing_tags: bool = typer.Option(False, help="忽略任务标签"),
) -> None:
    original_file_paths = [Path(file) for file in files]
    mission_query = _build_mission_query(mission, project)

    validator = FileValidator(
        skip=skip,
        experimental_datatypes=experimental_datatypes,
    )

    # This function will raise an error if skip=False and a file is invalid
    files_to_upload = validator.filter_files(original_file_paths)

    _report_skipped_files(validator.skipped_files)

    _handle_no_files_to_upload(original_count=len(original_file_paths), uploaded_count=len(files_to_upload))

    try:
        rslstudio.core.upload(
            client=AuthenticatedClient(),
            query=mission_query,
            file_paths=files_to_upload,
            create=create,
            metadata=load_metadata(Path(metadata)) if metadata else None,
            ignore_missing_metadata=ignore_missing_tags,
            verbose=get_shared_state().verbose,
        )
        typer.echo(
            typer.style(
                f"\n成功上传了 {len(files_to_upload)} 个文件。",
                fg=typer.colors.GREEN,
            )
        )

    except MissionNotFound:
        if create:
            raise  # dont change the error message
        raise MissionNotFound("未找到任务。请使用 `--create` 创建。")
