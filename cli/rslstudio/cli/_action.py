from __future__ import annotations

import time
from typing import Optional
from uuid import UUID

import httpx
import typer

import rslstudio.api.routes
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery
from rslstudio.config import get_shared_state
from rslstudio.printing import print_action_templates_table
from rslstudio.printing import print_run_info
from rslstudio.utils import is_valid_uuid4
from rslstudio.utils import split_args

HELP = """\
从预定义模板启动 RslStudio 执行。

您可以列出可用执行模板，在特定任务上启动新的执行，并可选择
实时跟踪其日志。
"""

action_typer = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=HELP,
)

LIST_HELP = "列出执行模板（定义）。要列出单个运行记录，请使用 `klein run list`。"
GET_HELP = "获取指定执行模板的详细信息。"
RUN_HELP = "从模板启动新的执行。"


@action_typer.command(help=LIST_HELP, name="list")
def list_actions() -> None:
    client = AuthenticatedClient()
    templates = list(rslstudio.api.routes.get_action_templates(client))

    if not templates:
        typer.echo("未找到执行模板。")
        return

    print_action_templates_table(templates, pprint=get_shared_state().verbose)


@action_typer.command(help=RUN_HELP)
def run(
    template_name: str = typer.Argument(..., help="要运行的模板名称或 ID。"),
    mission: str = typer.Option(..., "--mission", "-m", help="要运行执行的任务 ID 或名称。"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称（用于限定任务范围）。"),
    follow: bool = typer.Option(False, "--follow", "-f", help="跟踪执行运行的日志。"),
) -> None:
    """
    Submits an action to run on a specific mission and optionally follows its logs.
    """
    client = AuthenticatedClient()
    pprint = get_shared_state().verbose

    try:
        project_ids, project_patterns = split_args([project] if project else [])
        project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

        mission_ids, mission_patterns = split_args([mission])
        mission_query = MissionQuery(
            ids=mission_ids,
            patterns=mission_patterns,
            project_query=project_query,
        )
        mission_obj = rslstudio.api.routes.get_mission(client, mission_query)
        mission_uuid = mission_obj.id
    except rslstudio.errors.MissionNotFound:
        typer.secho(f"错误：未找到任务 '{mission}'。", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except rslstudio.errors.InvalidMissionQuery:
        typer.secho(
            "错误：任务查询不明确，请尝试使用 -p 指定项目。",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"解析任务时出错：{e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 2. Resolve Template to UUID
    try:
        if is_valid_uuid4(template_name):
            template_uuid = UUID(template_name)
        else:
            templates = rslstudio.api.routes.get_action_templates(client)
            found_template = next((t for t in templates if t.name == template_name), None)

            if not found_template:
                typer.secho(
                    f"错误：未找到执行模板 '{template_name}'。",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1)
            template_uuid = found_template.uuid
    except Exception as e:
        typer.secho(f"解析模板时出错：{e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        action_uuid_str = rslstudio.api.routes.submit_action(client, mission_uuid, template_uuid)
        typer.secho(f"执行已提交，运行 ID：{action_uuid_str}", fg=typer.colors.GREEN)

    except httpx.HTTPStatusError as e:
        typer.secho(f"提交执行时出错：{e.response.text}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except (KeyError, Exception) as e:
        typer.secho(f"发生意外错误：{e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if follow:
        exit_code = rslstudio.printing.follow_run_logs(client, action_uuid_str)
        if exit_code != 0:
            raise typer.Exit(code=exit_code)

    elif pprint:
        # Not following, but in verbose mode. Show run info.
        try:
            time.sleep(0.5)  # Give API a moment
            run_details = rslstudio.api.routes.get_run(client, action_uuid_str)
            rslstudio.printing.print_run_info(run_details, pprint=True)
        except Exception:
            # Non-critical, we already printed the ID.
            pass
