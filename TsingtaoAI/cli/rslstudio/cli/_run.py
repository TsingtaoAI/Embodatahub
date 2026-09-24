from __future__ import annotations

import os
import re
import sys
import tarfile
import time
from typing import List
from typing import Optional

import requests
import typer

import rslstudio.api.routes
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import RunQuery
from rslstudio.config import get_shared_state
from rslstudio.models import LogEntry
from rslstudio.models import Run
from rslstudio.printing import print_run_info
from rslstudio.printing import print_run_logs
from rslstudio.printing import print_runs_table
from rslstudio.utils import split_args

HELP = """\
管理和查看执行记录。

您可以列出执行记录，获取特定运行的详细信息，流式查看其日志，
取消正在进行的运行，以及重试失败的运行。
"""

run_typer = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=HELP,
)

LIST_HELP = "列出执行记录。可按任务或项目筛选。"
INFO_HELP = "获取指定执行运行的详细信息。"
LOGS_HELP = "流式查看指定执行运行的日志。"
CANCEL_HELP = "取消正在进行的执行运行。"
RETRY_HELP = "重试失败的执行运行。"
DOWNLOAD_HELP = "下载指定执行运行的产出物。"


@run_typer.command(help=LIST_HELP, name="list")
def list_runs(
    mission: Optional[str] = typer.Option(None, "--mission", "-m", help="按任务 ID 或名称筛选。"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="按项目 ID 或名称筛选。"),
) -> None:
    """
    List action runs.
    """
    client = AuthenticatedClient()

    mission_ids, mission_patterns = split_args([mission] if mission else [])
    project_ids, project_patterns = split_args([project] if project else [])

    query = RunQuery(
        mission_ids=mission_ids,
        mission_patterns=mission_patterns,
        project_ids=project_ids,
        project_patterns=project_patterns,
    )

    runs = list(rslstudio.api.routes.get_runs(client, query=query))
    print_runs_table(runs, pprint=get_shared_state().verbose)


@run_typer.command(name="info", help=INFO_HELP)
def get_info(run_id: str = typer.Argument(..., help="要获取信息的运行 ID。")) -> None:
    """
    Get detailed information for a single run.
    """
    client = AuthenticatedClient()
    run: Run = rslstudio.api.routes.get_run(client, run_id=run_id)
    print_run_info(run, pprint=get_shared_state().verbose)


@run_typer.command(help=LOGS_HELP)
def logs(
    run_id: str = typer.Argument(..., help="要获取日志的运行 ID。"),
    follow: bool = typer.Option(False, "--follow", "-f", help="实时跟踪日志输出。"),
) -> None:
    """
    Fetch and display logs for a specific run.
    """
    client = AuthenticatedClient()

    if follow:
        typer.echo(f"正在查看运行 {run_id} 的日志。按 Ctrl+C 停止。")
        try:

            # TODO: fine for now, but ideally we would have a streaming endpoint
            # currently there is no following, thus we just poll every 2 seconds
            # from the get_run endpoint
            last_log_index = 0
            while True:
                run: Run = rslstudio.api.routes.get_run(client, run_id=run_id)
                log_entries: List[LogEntry] = run.logs
                new_log_entries = log_entries[last_log_index:]
                if new_log_entries:
                    print_run_logs(new_log_entries, pprint=get_shared_state().verbose)
                    last_log_index += len(new_log_entries)

                time.sleep(2)

        except KeyboardInterrupt:
            typer.echo("已停止跟踪日志。")
            sys.exit(0)
    else:
        log_entries = rslstudio.api.routes.get_run(client, run_id=run_id).logs
        print_run_logs(log_entries, pprint=get_shared_state().verbose)


def _get_filename_from_cd(cd: str) -> Optional[str]:
    """Extract filename from Content-Disposition header."""
    if not cd:
        return None
    fname = re.findall("filename=(.+)", cd)
    if len(fname) == 0:
        return None
    return fname[0].strip().strip('"')


@run_typer.command(name="download", help=DOWNLOAD_HELP)
def download_artifacts(
    run_id: str = typer.Argument(..., help="要下载产出物的运行 ID。"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="保存产出物的路径或文件名。"),
    extract: bool = typer.Option(
        False,
        "--extract",
        "-x",
        help="下载后自动解压归档文件。",
    ),
) -> None:
    """
    Download the artifacts (.tar.gz) for a finished run.
    """
    client = AuthenticatedClient()

    # Fetch Run Details
    try:
        run: Run = rslstudio.api.routes.get_run(client, run_id=run_id)
    except Exception as e:
        typer.secho(f"获取运行详情失败：{e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    if not run.artifact_url:
        typer.secho(
            f"未找到运行 {run_id} 的产出物。该运行可能尚未完成或产出物已过期。",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(1)

    typer.echo(f"正在下载运行 {run_id} 的产出物...")

    # Stream Download
    try:
        with requests.get(run.artifact_url, stream=True) as r:
            r.raise_for_status()

            # Determine Filename
            filename = output
            if not filename:
                filename = _get_filename_from_cd(r.headers.get("content-disposition"))

            if not filename:
                filename = f"{run_id}.tar.gz"

            # If output is a directory, join with filename
            if output and os.path.isdir(output):
                filename = os.path.join(
                    output,
                    _get_filename_from_cd(r.headers.get("content-disposition")) or f"{run_id}.tar.gz",
                )

            total_length = int(r.headers.get("content-length", 0))

            # Write to file with Progress Bar
            with open(filename, "wb") as f:
                with typer.progressbar(length=total_length, label=f"保存至 {filename}") as progress:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(len(chunk))

            typer.secho(f"\n成功下载至 {filename}", fg=typer.colors.GREEN)

            # Extraction Logic
            if extract:
                try:
                    # Determine extraction directory (based on filename without extension)
                    # e.g., "downloads/my-run.tar" -> "downloads/my-run"
                    base_name = os.path.basename(filename)
                    folder_name = base_name.split(".")[0]

                    # Get the parent directory of the downloaded file
                    parent_dir = os.path.dirname(os.path.abspath(filename))
                    extract_path = os.path.join(parent_dir, folder_name)

                    typer.echo(f"正在解压至：{extract_path}...")

                    with tarfile.open(filename, "r:gz") as tar:

                        # Safety check: filter_data prevents extraction outside target dir (CVE-2007-4559)
                        # Available in Python 3.12+, for older python use generic extractall
                        if hasattr(tarfile, "data_filter"):
                            tar.extractall(path=extract_path, filter="data")
                        else:
                            tar.extractall(path=extract_path)

                    typer.secho("解压成功。", fg=typer.colors.GREEN)

                except tarfile.TarError as e:
                    typer.secho(f"解压归档文件失败：{e}", fg=typer.colors.RED)

    except requests.exceptions.RequestException as e:
        typer.secho(f"下载文件时出错：{e}", fg=typer.colors.RED)
        raise typer.Exit(1)
