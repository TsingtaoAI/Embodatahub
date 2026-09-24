from __future__ import annotations

import time
import urllib.parse
import webbrowser
from getpass import getpass
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from typing import Optional

from rslstudio.config import CONFIG_PATH
from rslstudio.config import Credentials
from rslstudio.config import get_config
from rslstudio.config import save_config

DEFAULT_CALLBACK_PORT = 8000
CLI_CALLBACK_ENDPOINT = "/cli/callback"
OAUTH_SLUG = "/auth/"
AUTH_TOKEN_FETCH_ERROR = "获取认证令牌失败。"


def _has_browser() -> bool:
    try:
        webbrowser.get()
        return True
    except webbrowser.Error:
        return False


def _headless_auth(*, url: str) -> None:

    print(f"请手动打开以下 URL 进行认证：{url}")
    print("输入登录后获取的认证令牌：")
    auth_token = getpass("认证令牌：")
    refresh_token = getpass("刷新令牌：")

    if auth_token and refresh_token:
        config = get_config()
        config.credentials = Credentials(auth_token=auth_token, refresh_token=refresh_token)
        save_config(config)
        print(f"认证完成。令牌已保存至 {CONFIG_PATH}。")
    else:
        raise ValueError("请提供令牌。")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith(CLI_CALLBACK_ENDPOINT):
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"无效路径")
            return

        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        try:
            auth_token = params.get("authtoken")
            refresh_token = params.get("refreshtoken")
            if not auth_token or not refresh_token:
                raise ValueError("Missing callback tokens")

            creds = Credentials(auth_token=auth_token[0], refresh_token=refresh_token[0])
            config = get_config()
            config.credentials = creds
            save_config(config)
            self.server.auth_completed = True  # type: ignore[attr-defined]
        except Exception:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(AUTH_TOKEN_FETCH_ERROR.encode("utf-8"))
            self.server.auth_error = AUTH_TOKEN_FETCH_ERROR  # type: ignore[attr-defined]
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"认证成功，您可以关闭此窗口。")

    def log_message(self, *args, **kwargs):
        _ = args, kwargs
        pass  # suppress logging


def _browser_auth(*, url: str, server: HTTPServer) -> None:
    server.auth_completed = False  # type: ignore[attr-defined]
    server.auth_error = None  # type: ignore[attr-defined]
    webbrowser.open(url)

    try:
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            server.timeout = max(0.1, remaining)
            server.handle_request()
            auth_error = getattr(server, "auth_error", None)
            if auth_error:
                raise RuntimeError(auth_error)
            if getattr(server, "auth_completed", False):
                break
    finally:
        server.server_close()

    if not server.auth_completed:
        raise RuntimeError("认证超时或失败，请重试。")
    print(f"认证完成。令牌已保存至 {CONFIG_PATH}。")


def _create_callback_server(preferred_port: int = DEFAULT_CALLBACK_PORT) -> tuple[HTTPServer, int]:
    try:
        server = HTTPServer(("", preferred_port), OAuthCallbackHandler)
        return server, preferred_port
    except OSError:
        server = HTTPServer(("", 0), OAuthCallbackHandler)  # bind to any available port
        return server, int(server.server_address[1])


def _direct_oauth_auth(*, endpoint: str, provider: str, user: str) -> None:
    """
    Directly authenticate with fake OAuth by programmatically following the OAuth flow.
    This bypasses the browser entirely for automated testing.
    """
    import requests

    print(f"正在使用 {provider} 以用户 {user} 身份认证...")

    try:
        # Step 1: Get the authorization code from fake OAuth
        # The fake OAuth server will auto-redirect when user parameter is provided
        fake_oauth_url = "http://localhost:8004/oauth/authorize"
        callback_url = f"{endpoint}/auth/{provider}/callback"

        params = {
            "client_id": "some-random-string-it-does-not-matter",
            "redirect_uri": callback_url,
            "response_type": "code",
            "state": "cli-direct",
            "user": user,
        }

        # Make request to fake OAuth - it will redirect with the auth code
        response = requests.get(fake_oauth_url, params=params, allow_redirects=False)

        if response.status_code not in [301, 302, 303, 307, 308]:
            raise RuntimeError(f"预期收到 OAuth 提供商的重定向，但收到状态码 {response.status_code}")

        # Extract the redirect location
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError("未收到 OAuth 提供商的重定向地址")

        # Parse the callback URL to extract the auth code
        parsed = urllib.parse.urlparse(location)
        query_params = urllib.parse.parse_qs(parsed.query)

        if "code" not in query_params:
            raise RuntimeError(f"重定向中无授权码：{location}")

        auth_code = query_params["code"][0]
        state = query_params.get("state", [None])[0]

        print("已收到授权码，正在交换令牌...")

        # Step 2: Exchange the code for tokens by calling the backend callback
        # Use a session to preserve cookies
        session = requests.Session()
        callback_params = {"code": auth_code}
        if state:
            callback_params["state"] = state

        callback_response = session.get(callback_url, params=callback_params, allow_redirects=False)

        # The backend should set cookies and redirect
        if callback_response.status_code not in [301, 302, 303, 307, 308]:
            raise RuntimeError(f"预期收到回调的重定向，但收到状态码 {callback_response.status_code}")

        # Extract tokens from cookies
        auth_token = session.cookies.get("authtoken")
        refresh_token = session.cookies.get("refreshtoken")

        if not auth_token or not refresh_token:
            raise RuntimeError("从回调响应获取令牌失败")

        # Save tokens
        config = get_config()
        config.credentials = Credentials(auth_token=auth_token, refresh_token=refresh_token)
        save_config(config)
        print(f"认证完成。令牌已保存至 {CONFIG_PATH}。")

    except requests.RequestException as e:
        raise RuntimeError(f"OAuth 流程失败：{e}")


def login_flow(
    *,
    oAuthProvider: str,
    key: Optional[str] = None,
    headless: bool = False,
    user: Optional[str] = None,
) -> None:
    config = get_config()
    # use cli key login
    if key is not None:
        config.credentials = Credentials(api_key=key)
        save_config(config)
        return

    # If user parameter is provided with fake-oauth, use direct OAuth flow
    if user is not None and oAuthProvider == "fake-oauth":
        _direct_oauth_auth(endpoint=config.endpoint.api, provider=oAuthProvider, user=user)
        return

    # normal flow: either browser-based or headless OAuth
    # if headless is False and browser is available, use browser-based flow with callback server
    if not headless and _has_browser():
        server, callback_port = _create_callback_server()
        state = f"cli-port-{callback_port}"
        oauth_url = f"{config.endpoint.api}{OAUTH_SLUG}{oAuthProvider}?state={state}"
        if user is not None:
            oauth_url += f"&user={user}"
        _browser_auth(url=oauth_url, server=server)
    else:
        oauth_url = f"{config.endpoint.api}{OAUTH_SLUG}{oAuthProvider}?state=cli-no-redirect"
        if user is not None:
            oauth_url += f"&user={user}"
        _headless_auth(url=oauth_url)
