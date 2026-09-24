from __future__ import annotations

from rich.console import Console

from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.query import FileQuery
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery
from rslstudio.api.routes import get_files
from rslstudio.printing import files_to_table


def main():
    client = AuthenticatedClient()

    ps = ProjectQuery(patterns=["*"])
    ms = MissionQuery(project_query=ps)
    fs = FileQuery(mission_query=ms, patterns=["*.bag"])

    files = get_files(client, fs)

    Console().print(files_to_table(list(files)))


if __name__ == "__main__":
    main()
