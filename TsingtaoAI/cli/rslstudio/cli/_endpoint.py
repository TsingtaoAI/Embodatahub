"""
at the moment the endpoint command lets you specify the api and s3 endpoints
eventually it will be sufficient to just specify the api endpoint and the s3 endpoint will
be provided by the api
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from rslstudio.config import Endpoint
from rslstudio.config import add_endpoint
from rslstudio.config import endpoint_table
from rslstudio.config import get_config
from rslstudio.config import select_endpoint

HELP = """\
在不同的 RslStudio 托管服务器之间切换。

终端地址用于确定要连接的 API 服务器\
（默认为 https://datasets.leggedrobotics.com 的 API 服务器）。
"""

endpoint_typer = typer.Typer(
    name="endpoint",
    help=HELP,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)


@endpoint_typer.callback()
def endpoint(
    name: Optional[str] = typer.Argument(None, help="要使用的终端名称"),
    api: Optional[str] = typer.Argument(None, help="要使用的 API 终端地址"),
    s3: Optional[str] = typer.Argument(None, help="要使用的 S3 终端地址"),
) -> None:
    config = get_config()
    console = Console()

    if not any([name, api, s3]):
        console.print(endpoint_table(config))
    elif name is not None and not any([api, s3]):
        try:
            select_endpoint(config, name)
        except ValueError:
            console.print(f"未找到终端 {name}。\n", style="red")
            console.print(endpoint_table(config))
    elif not (name and api and s3):
        raise typer.BadParameter("要添加新终端，必须同时指定 api 和 s3 终端地址")
    else:
        new_endpoint = Endpoint(name, api, s3)
        add_endpoint(config, new_endpoint)
