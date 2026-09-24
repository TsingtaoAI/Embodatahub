from __future__ import annotations

LOGIN_MESSAGE = "请使用 `klein login` 登录。"
UPDATE_MESSAGE = "请使用 `pip install --upgrade rslstudio` 更新 CLI。"


class ParsingError(Exception): ...


class InvalidFileQuery(Exception): ...


class InvalidMissionQuery(Exception): ...


class InvalidProjectQuery(Exception): ...


class MissionExists(Exception): ...


class ProjectExists(Exception): ...


class MissionNotFound(Exception): ...


class ProjectNotFound(Exception): ...


class FileNotFound(Exception): ...


class AccessDenied(Exception): ...


class InvalidCLIVersion(Exception): ...


class FileTypeNotSupported(Exception): ...


class FileNameNotSupported(Exception): ...


class DatatypeNotSupported(Exception): ...


class InvalidMissionMetadata(Exception): ...


class MissionValidationError(Exception): ...


class ProjectValidationError(Exception): ...


class NotAuthenticated(Exception):
    def __init__(self) -> None:
        super().__init__(LOGIN_MESSAGE)


class UpdateCLIVersion(Exception):
    def __init__(self) -> None:
        super().__init__(UPDATE_MESSAGE)


class RunNotFound(Exception): ...
