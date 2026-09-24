from __future__ import annotations

import logging
from pathlib import Path
from typing import List
from typing import Optional

import typer

import rslstudio.core
from rslstudio.api.client import AuthenticatedClient
from rslstudio.cli._file_validator import FileValidator
from rslstudio.cli._file_validator import _report_skipped_files
from rslstudio.cli._upload import _build_mission_query
from rslstudio.config import get_shared_state
from rslstudio.printing import print_file_verification_status

logger = logging.getLogger(__name__)

HELP = """\
验证文件是否上传正确。
"""

verify_typer = typer.Typer(name="verify", invoke_without_command=True, help=HELP)


def _handle_no_files_to_process(original_count: int, processed_count: int, action: str = "verify") -> None:
    """Checks if any files are left and exits if not."""
    if processed_count > 0:
        return

    if original_count > 0:
        typer.echo(
            typer.style(f"All paths were skipped. No files to {action}.", fg=typer.colors.RED),
            err=True,
        )
    else:
        typer.echo(
            typer.style(f"No files provided to {action}.", fg=typer.colors.RED),
            err=True,
        )
    raise typer.Exit(code=1)


@verify_typer.callback()
def verify(
    files: List[str] = typer.Argument(help="要验证的文件"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称"),
    mission: str = typer.Option(..., "--mission", "-m", help="任务 ID 或名称"),
    skip: bool = typer.Option(
        False,
        "--skip",
        "-s",
        help="跳过不支持的文件类型、命名错误的文件或目录（而不是报错）",
    ),
    experimental_datatypes: bool = typer.Option(False, help="允许实验性数据类型（yaml, svo2, db3, tum）"),
    skip_hash: bool = typer.Option(None, help="跳过哈希检查"),
    check_file_hash: bool = typer.Option(
        True,
        help="检查文件哈希。如果为 True，则检查文件名和文件哈希。",
    ),
    check_file_size: bool = typer.Option(
        True,
        help="检查文件大小。如果为 True，则检查文件名和文件大小。",
    ),
) -> None:
    # get all filepaths
    original_file_paths = [Path(file) for file in files]

    # get mission query
    mission_query = _build_mission_query(mission, project)

    validator = FileValidator(
        skip=skip,
        experimental_datatypes=experimental_datatypes,
    )
    files_to_verify = validator.filter_files(original_file_paths)

    # Report skipped files (if any)
    _report_skipped_files(validator.skipped_files)

    # Check if we have anything left to do
    _handle_no_files_to_process(
        original_count=len(original_file_paths),
        processed_count=len(files_to_verify),
        action="verify",
    )

    verbose = get_shared_state().verbose
    file_status = rslstudio.core.verify(
        client=AuthenticatedClient(),
        query=mission_query,
        file_paths=files_to_verify,
        skip_hash=skip_hash,
        check_file_hash=check_file_hash,
        check_file_size=check_file_size,
        verbose=verbose,
    )
    print_file_verification_status(file_status, pprint=verbose)
