from __future__ import annotations

from typing import Optional

import typer

import rslstudio.api.routes
import rslstudio.core
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import FileQuery
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery
from rslstudio.api.routes import get_file
from rslstudio.config import get_shared_state
from rslstudio.printing import print_file_info
from rslstudio.utils import split_args

INFO_HELP = "get information about a file"
DELETE_HELP = "delete a file"


file_typer = typer.Typer(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})


@file_typer.command(help=INFO_HELP)
def info(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="project id or name"),
    mission: Optional[str] = typer.Option(None, "--mission", "-m", help="mission id or name"),
    file: str = typer.Option(..., "--file", "-f", help="file id or name"),
) -> None:
    project_ids, project_patterns = split_args([project] if project else [])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    mission_ids, mission_patterns = split_args([mission] if mission else [])
    mission_query = MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )

    file_ids, file_patterns = split_args([file])
    file_query = FileQuery(
        ids=file_ids,
        patterns=file_patterns,
        mission_query=mission_query,
    )

    client = AuthenticatedClient()
    file_parsed = get_file(client, file_query)
    print_file_info(file_parsed, pprint=get_shared_state().verbose)


@file_typer.command(help=DELETE_HELP)
def delete(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="project id or name"),
    mission: Optional[str] = typer.Option(None, "--mission", "-m", help="mission id or name"),
    file: str = typer.Option(..., "--file", "-f", help="file id or name"),
    confirm: bool = typer.Option(False, "--confirm", "-y", "--yes", help="confirm deletion"),
) -> None:
    if not confirm:
        typer.confirm(f"delete {project} {mission}", abort=True)

    project_ids, project_patterns = split_args([project] if project else [])
    project_query = ProjectQuery(ids=project_ids, patterns=project_patterns)

    mission_ids, mission_patterns = split_args([mission] if mission else [])
    mission_query = MissionQuery(
        ids=mission_ids,
        patterns=mission_patterns,
        project_query=project_query,
    )

    file_ids, file_patterns = split_args([file])
    file_query = FileQuery(
        ids=file_ids,
        patterns=file_patterns,
        mission_query=mission_query,
    )

    client = AuthenticatedClient()
    file_parsed = get_file(client, file_query)
    rslstudio.core.delete_files(client=client, file_ids=[file_parsed.id])
