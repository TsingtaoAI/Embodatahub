from __future__ import annotations

import logging
import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import List
from typing import Optional

import typer
from click import Context
from rich.console import Console
from typer.core import TyperGroup

from rslstudio._version import __version__
from rslstudio.api.client import AuthenticatedClient
from rslstudio.api.routes import _claim_admin
from rslstudio.api.routes import _get_api_version
from rslstudio.auth import login_flow
from rslstudio.cli._action import action_typer
from rslstudio.cli._download import download_typer
from rslstudio.cli._endpoint import endpoint_typer
from rslstudio.cli._file import file_typer
from rslstudio.cli._list import list_typer
from rslstudio.cli._mission import mission_typer
from rslstudio.cli._project import project_typer
from rslstudio.cli._run import run_typer
from rslstudio.cli._upload import upload_typer
from rslstudio.cli._verify import verify_typer
from rslstudio.cli.error_handling import ErrorHandledTyper
from rslstudio.cli.error_handling import display_error
from rslstudio.config import MAX_TABLE_SIZE
from rslstudio.config import Config
from rslstudio.config import check_config_compatibility
from rslstudio.config import get_config
from rslstudio.config import get_shared_state
from rslstudio.config import save_config
from rslstudio.errors import InvalidCLIVersion
from rslstudio.utils import format_traceback
from rslstudio.utils import get_supported_api_version

# slightly cursed lambdas so that linters don't complain about unreachable code
if (lambda: os.name)() == "posix":
    LOG_DIR = Path().home() / ".local" / "state" / "rslstudio"
elif (lambda: os.name)() == "nt":
    LOG_DIR = Path().home() / "AppData" / "Local" / "rslstudio"
else:
    raise OSError(f"Unsupported OS {os.name}")

LOG_FILE = LOG_DIR / f"{time.time_ns()}.log"
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

# setup default logging
logger = logging.getLogger(__name__)


CLI_HELP = """\
RslStudio CLI

RslStudio CLI 是 RslStudio 的命令行界面。
查看可用命令列表，请运行 `klein --help` 或访问 \
https://docs.datasets.leggedrobotics.com/usage/python/setup \
获取更多信息。
"""


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


LOG_LEVEL_MAP = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL,
}


class CommandTypes(str, Enum):
    AUTH = "认证命令"
    CORE = "核心命令"
    CRUD = "创建更新删除命令"
    ACTION = "RslStudio 执行命令"


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: Context) -> List[str]:
        _ = ctx  # suppress unused variable warning
        return list(self.commands)


app = ErrorHandledTyper(
    cls=OrderCommands,
    help=CLI_HELP,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)

app.add_typer(endpoint_typer, name="endpoint", rich_help_panel=CommandTypes.AUTH)

app.add_typer(download_typer, name="download", rich_help_panel=CommandTypes.CORE)
app.add_typer(upload_typer, name="upload", rich_help_panel=CommandTypes.CORE)
app.add_typer(verify_typer, name="verify", rich_help_panel=CommandTypes.CORE)
app.add_typer(list_typer, name="list", rich_help_panel=CommandTypes.CORE)

app.add_typer(file_typer, name="file", rich_help_panel=CommandTypes.CRUD)
app.add_typer(mission_typer, name="mission", rich_help_panel=CommandTypes.CRUD)
app.add_typer(project_typer, name="project", rich_help_panel=CommandTypes.CRUD)
app.add_typer(action_typer, name="action", rich_help_panel=CommandTypes.ACTION)
app.add_typer(run_typer, name="run", rich_help_panel=CommandTypes.ACTION)


# attach error handler to app
@app.error_handler(Exception)
def base_handler(exc: Exception) -> int:
    shared_state = get_shared_state()

    display_error(exc=exc, verbose=shared_state.verbose)
    logger.error(format_traceback(exc))

    if not shared_state.debug:
        return 1
    raise exc


@app.command(rich_help_panel=CommandTypes.AUTH)
def login(
    oAuthProvider: str = typer.Option(
        "auto",
        "--oauth-provider",
        "-p",
        help="用于登录的 OAuth 提供商。支持的提供商：google, github, fake-oauth。",
        show_default=True,
    ),
    key: Optional[str] = typer.Option(None, help="CLI 密钥"),
    headless: bool = typer.Option(False),
    user: Optional[str] = typer.Option(
        None,
        "--user",
        "-u",
        help="自动选择 fake-oauth 的用户 ID（例如 1, 2, 3）。仅适用于 fake-oauth 提供商。",
    ),
) -> None:

    # logic to resolve the "auto" default
    if oAuthProvider == "auto":
        config = get_config()
        if config.selected_endpoint == "local":
            oAuthProvider = "fake-oauth"
        else:
            oAuthProvider = "google"

    # validate oAuthProvider
    if oAuthProvider not in ["google", "github", "fake-oauth"]:
        raise typer.BadParameter(
            f"不支持的 OAuth 提供商 '{oAuthProvider}'。支持的提供商：google, github, fake-oauth。"
        )

    # validate that user parameter is only used with fake-oauth
    if user is not None and oAuthProvider != "fake-oauth":
        raise typer.BadParameter("--user 参数仅适用于 fake-oauth 提供商")

    login_flow(oAuthProvider=oAuthProvider, key=key, headless=headless, user=user)


@app.command(rich_help_panel=CommandTypes.AUTH)
def logout(all: bool = typer.Option(False, help="登出所有终端")) -> None:
    config = get_config()
    if all:
        config.endpoint_credentials.clear()
    else:
        config.endpoint_credentials.pop(config.selected_endpoint, None)
    save_config(config)


@app.command(hidden=True)
def claim():
    client = AuthenticatedClient()
    _claim_admin(client)
    print("管理员权限声明成功。")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def check_version_compatibility() -> None:
    cli_version = get_supported_api_version()
    api_version = _get_api_version()
    api_vers_str = ".".join(map(str, api_version))

    if cli_version[0] != api_version[0]:
        raise InvalidCLIVersion(
            f"您使用的 CLI 版本 ({__version__}) 不受支持。"
            f"请升级 CLI 至版本 {api_vers_str} 以继续使用。"
        )

    if cli_version[1] != api_version[1]:
        if cli_version < api_version:
            msg = f"您使用的 CLI 版本 ({__version__}) 已过时。"
            msg += f"请考虑升级 CLI 至版本 {api_vers_str}。"
            Console(file=sys.stderr).print(msg, style="red")
            logger.warning(msg)
        elif cli_version > api_version:
            msg = f"您使用的 CLI 版本 ({__version__}) 比服务器版本 ({api_vers_str}) 更新。"
            msg += "请联系管理员更新服务器。"
            Console(file=sys.stderr).print(msg, style="yellow")
            logger.warning(msg)


@app.callback()
def cli(
    verbose: bool = typer.Option(True, help="启用详细模式。"),
    debug: bool = typer.Option(True, help="启用调试模式。"),
    version: Optional[bool] = typer.Option(None, "--version", "-v", callback=_version_callback),
    log_level: Optional[LogLevel] = typer.Option(None, help="设置日志级别。"),
    max_lines: int = typer.Option(
        MAX_TABLE_SIZE,
        "--max-lines",
        help="格式化打印表格时的最大行数，-1 表示无限制。",
    ),
):
    if not check_config_compatibility():
        typer.confirm("发现不兼容的配置文件，是否覆盖？", abort=True)
        save_config(Config())

    _ = version  # suppress unused variable warning
    shared_state = get_shared_state()
    shared_state.verbose = verbose
    shared_state.debug = debug

    if max_lines < 0 and max_lines != -1:
        raise typer.BadParameter("`--max-lines` 必须为 -1 或正数")
    shared_state.max_table_size = max_lines

    if shared_state.debug and log_level is None:
        log_level = LogLevel.DEBUG
    if log_level is None:
        log_level = LogLevel.WARNING

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=LOG_LEVEL_MAP[log_level], filename=LOG_FILE, format=LOG_FORMAT)
    logger.info(f"CLI version: {__version__}")

    try:
        check_version_compatibility()
    except InvalidCLIVersion as e:
        logger.error(format_traceback(e))
        raise
    except Exception:
        err = "检查版本兼容性失败"
        Console(file=sys.stderr).print(err, style="yellow" if shared_state.verbose else None)
        logger.error(err)
