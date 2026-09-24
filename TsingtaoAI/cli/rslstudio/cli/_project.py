from __future__ import annotations

from typing import Optional

import typer

import rslstudio.api.routes
import rslstudio.core
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import ProjectQuery
from rslstudio.api.routes import get_project
from rslstudio.config import get_shared_state
from rslstudio.printing import print_project_info
from rslstudio.utils import split_args

project_typer = typer.Typer(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})


NOT_IMPLEMENTED_YET = """\
尚未实现，如有特定功能需求请提交 Issue
"""

CREATE_HELP = "创建项目"
INFO_HELP = "获取项目信息"
UPDATE_HELP = "更新项目"
DELETE_HELP = "删除项目"


@project_typer.command(help=CREATE_HELP)
def create(
    project: str = typer.Option(..., "--project", "-p", help="项目名称"),
    description: str = typer.Option(..., "--description", "-d", help="项目描述"),
) -> None:
    client = AuthenticatedClient()
    project_id = rslstudio.api.routes._create_project(client, project, description)

    project_parsed = get_project(client, ProjectQuery(ids=[project_id]))
    print_project_info(project_parsed, pprint=get_shared_state().verbose)


@project_typer.command(help=INFO_HELP)
def info(project: str = typer.Option(..., "--project", "-p", help="项目 ID 或名称")) -> None:
    project_ids, project_patterns = split_args([project])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    client = AuthenticatedClient()
    project_parsed = get_project(client=client, query=project_query)
    print_project_info(project_parsed, pprint=get_shared_state().verbose)


@project_typer.command(help=UPDATE_HELP)
def update(
    project: str = typer.Option(..., "--project", "-p", help="项目 ID 或名称"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="项目描述"),
    new_name: Optional[str] = typer.Option(None, "--new-name", "-n", "--name", help="新项目名称"),
) -> None:
    if description is None and new_name is None:
        raise typer.BadParameter("没有需要更新的内容，请提供 --description 或 --new-name")

    project_ids, project_patterns = split_args([project])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    client = AuthenticatedClient()
    project_id = get_project(client=client, query=project_query, exact_match=True).id
    rslstudio.core.update_project(client=client, project_id=project_id, description=description, new_name=new_name)

    project_parsed = get_project(client, ProjectQuery(ids=[project_id]))
    print_project_info(project_parsed, pprint=get_shared_state().verbose)


@project_typer.command(help=DELETE_HELP)
def delete(project: str = typer.Option(..., "--project", "-p", help="项目 ID 或名称")) -> None:
    project_ids, project_patterns = split_args([project])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    client = AuthenticatedClient()
    project_id = get_project(client=client, query=project_query, exact_match=True).id
    rslstudio.core.delete_project(client=client, project_id=project_id)


@project_typer.command(help=NOT_IMPLEMENTED_YET)
def prune() -> None:
    raise NotImplementedError(NOT_IMPLEMENTED_YET)
