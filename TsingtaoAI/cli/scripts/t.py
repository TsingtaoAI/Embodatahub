from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.pagination import _get_files_paginated
from rslstudio.api.pagination import _get_missions_paginated
from rslstudio.api.pagination import _get_projects_paginated
from rslstudio.api.query import FileQuery
from rslstudio.api.query import MissionQuery
from rslstudio.api.query import ProjectQuery

ps = ProjectQuery()
ms = MissionQuery()
fs = FileQuery()

client = AuthenticatedClient()


for project in _get_projects_paginated(client, ps):
    print(project)


for mission in _get_missions_paginated(client, ms):
    print(mission)


for file in _get_files_paginated(client, fs):
    print(file)
