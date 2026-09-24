from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

import rslstudio.api.routes
import rslstudio.core
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery
from rslstudio.api.routes import get_mission
from rslstudio.api.routes import get_project
from rslstudio.config import get_shared_state
from rslstudio.errors import InvalidMissionQuery
from rslstudio.printing import print_mission_info
from rslstudio.utils import load_metadata
from rslstudio.utils import split_args

CREATE_HELP = "创建任务"
UPDATE_HELP = "更新任务"
DELETE_HELP = "删除任务"
INFO_HELP = "获取任务信息"
NOT_IMPLEMENTED_YET = """\
尚未实现，如有特定功能需求请提交 Issue
"""

mission_typer = typer.Typer(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})


@mission_typer.command(help=CREATE_HELP)
def create(
    project: str = typer.Option(..., "--project", "-p", help="项目 ID 或名称"),
    mission_name: str = typer.Option(..., "--mission", "-m", help="任务名称"),
    metadata: Optional[str] = typer.Option(None, help="元数据文件路径（json 或 yaml）"),
    ignore_missing_tags: bool = typer.Option(False, help="忽略任务标签"),
) -> None:
    project_ids, project_patterns = split_args([project] if project else [])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    metadata_dct = load_metadata(Path(metadata)) if metadata else {}  # noqa

    client = AuthenticatedClient()
    project = get_project(client, project_query, exact_match=True)
    project_id = project.id
    project_required_tags = project.required_tags
    mission_id = rslstudio.api.routes._create_mission(
        client,
        project_id,
        mission_name,
        metadata=metadata_dct,
        ignore_missing_tags=ignore_missing_tags,
        required_tags=project_required_tags,
    )

    mission_parsed = get_mission(client, MissionQuery(ids=[mission_id]))
    print_mission_info(mission_parsed, pprint=get_shared_state().verbose)


@mission_typer.command(help=INFO_HELP)
def info(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称"),
    mission: str = typer.Option(..., "--mission", "-m", help="任务 ID 或名称"),
) -> None:
    mission_ids, mission_patterns = split_args([mission])
    project_ids, project_patterns = split_args([project] if project else [])

    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)
    mission_query = MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )

    client = AuthenticatedClient()
    mission_parsed = get_mission(client, mission_query)
    print_mission_info(mission_parsed, pprint=get_shared_state().verbose)


@mission_typer.command(help=UPDATE_HELP)
def update(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称"),
    mission: str = typer.Option(..., "--mission", "-m", help="任务 ID 或名称"),
    metadata: str = typer.Option(help="元数据文件路径（json 或 yaml）"),
) -> None:
    mission_ids, mission_patterns = split_args([mission])
    project_ids, project_patterns = split_args([project] if project else [])

    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)
    mission_query = MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )

    metadata_dct = load_metadata(Path(metadata))

    client = AuthenticatedClient()
    mission_id = get_mission(client, mission_query).id
    rslstudio.core.update_mission(client=client, mission_id=mission_id, metadata=metadata_dct)

    mission_parsed = get_mission(client, mission_query)
    print_mission_info(mission_parsed, pprint=get_shared_state().verbose)


@mission_typer.command(help=DELETE_HELP)
def delete(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称"),
    mission: str = typer.Option(..., "--mission", "-m", help="任务 ID 或名称"),
    confirm: bool = typer.Option(False, "--confirm", "-y", "--yes", help="确认删除"),
) -> None:
    project_ids, project_patterns = split_args([project] if project else [])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    mission_ids, mission_patterns = split_args([mission])
    mission_query = MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )
    if mission_patterns and not (project_patterns or project_ids):
        raise InvalidMissionQuery(
            "任务查询无法唯一确定任务。"
            "按任务名称删除时必须指定项目名称或 ID"
        )

    client = AuthenticatedClient()
    mission_parsed = get_mission(client, mission_query)
    if not confirm:
        if project:
            typer.confirm(f"删除 {project} {mission}", abort=True)
        else:
            typer.confirm(f"删除 {mission_parsed.name} {mission}", abort=True)

    rslstudio.core.delete_mission(client=client, mission_id=mission_parsed.id)


@mission_typer.command(help=NOT_IMPLEMENTED_YET)
def prune(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="项目 ID 或名称"),
    mission: str = typer.Option(..., "--mission", "-m", help="任务 ID 或名称"),
) -> None:
    """\
    删除状态异常的文件，如缺失、未上传、损坏等
    TODO: open for suggestions what this should do
    """

    raise NotImplementedError("尚未实现")
