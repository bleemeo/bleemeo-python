import os
from typing import Optional, Iterator, Any
from urllib import parse

from requests import Response, Request, Session
from requests.adapters import HTTPAdapter

from .authenticator import Authenticator
from .exceptions import ConfigurationError, APIError, AuthenticationError, ThrottleError
from .resources import Resource


class Client:
    DEFAULT_ENDPOINT = "https://api.bleemeo.com"
    DEFAULT_OAUTH_CLIENT_ID = "1fc6de3e-8750-472e-baea-3ba22bb4eb56"
    DEFAULT_USER_AGENT = "Bleemeo Python Client"

    def __init__(
            self,
            api_url: Optional[str] = None,
            account_id: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            oauth_client_id: Optional[str] = None,
            oauth_client_secret: Optional[str] = None,
            oauth_initial_refresh_token: Optional[str] = None,
            custom_headers: Optional[dict] = None,
            load_from_env: bool = False,
    ):
        if load_from_env:
            api_url = api_url or os.environ.get("BLEEMEO_API_URL")
            account_id = account_id or os.environ.get("BLEEMEO_ACCOUNT_ID")
            username = username or os.environ.get("BLEEMEO_USER")
            password = password or os.environ.get("BLEEMEO_PASSWORD")
            oauth_client_id = oauth_client_id or os.environ.get("BLEEMEO_OAUTH_CLIENT_ID")
            oauth_client_secret = oauth_client_secret or os.environ.get("BLEEMEO_OAUTH_CLIENT_SECRET")
            oauth_initial_refresh_token = oauth_initial_refresh_token or os.environ.get(
                "BLEEMEO_OAUTH_INITIAL_REFRESH_TOKEN")

        if not username and not oauth_initial_refresh_token:
            raise ConfigurationError("Either a username or an initial oAuth refresh token must be provided.")

        self.api_url = api_url or self.DEFAULT_ENDPOINT
        self.username = username
        self.password = password
        self.oauth_client_id = oauth_client_id or self.DEFAULT_OAUTH_CLIENT_ID
        self.oauth_client_secret = oauth_client_secret
        self.oauth_initial_refresh_token = oauth_initial_refresh_token
        self.session = Session()
        self.session.mount("https://", HTTPAdapter(max_retries=5))
        self.session.headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
        }

        if account_id:
            self.session.headers["X-Bleemeo-Account"] = account_id
        if custom_headers:
            self.session.headers.update(custom_headers)

        self._authenticator = Authenticator(self.api_url, self.session, self.oauth_client_id, self.oauth_client_secret,
                                            self.username, self.password, self.oauth_initial_refresh_token)

    def logout(self):
        self._authenticator.logout()

    def _build_url(self, *parts: str) -> str:
        url = self.api_url
        for part in parts:
            url = parse.urljoin(url, part)
        if not url.endswith("/"):
            url = url + "/"
        return url

    def _do_request(self, request: Request, authenticated: bool, is_retry=False) -> Response:
        request.headers = {} if request.json is None else {"Content-Type": "application/json"}

        if authenticated:
            request.headers.update({"Authorization": f"Bearer {self._authenticator.get_token(force_refetch=is_retry)}"})

        resp = self.session.send(self.session.prepare_request(request))
        if resp.status_code == 401 and authenticated and not is_retry:
            resp = self._do_request(request, authenticated=True, is_retry=True)

        return resp

    def do_request(self, method: str, url: str, authenticated=True, params: Optional[dict] = None,
                   data: Optional[Any] = None) -> Response:
        req = Request(
            method=method,
            url=url,
            json=data,
            params=params,
        )

        response = self._do_request(req, authenticated)
        if response.status_code >= 400:
            if response.status_code == 400:  # Bad Request
                raise APIError(f"Bad request on {url}", response)
            if response.status_code == 401:  # Unauthorized
                raise AuthenticationError(f"Authentication failed on {url}", response)
            if response.status_code == 404:  # Not Found
                raise APIError(f"Resource {url} not found", response)
            if response.status_code == 429:  # Too Many Requests
                raise ThrottleError(response)

            raise APIError(f"Request {method} on {url} failed with status {response.status_code}", response)

        return response

    def get(self, resource: Resource, id: str, *fields: str) -> Response:
        url = self._build_url(resource.value, id)
        params = {"fields": ",".join(fields)} if fields else None

        return self.do_request("GET", url, params=params)

    def get_page(self, resource: Resource, *, page: int, page_size: int, params: Optional[dict] = None) -> Response:
        url = self._build_url(resource.value)
        params = params.copy() if params else {}
        params.update({"page": page, "page_size": page_size})

        return self.do_request("GET", url, params=params)

    def count(self, resource: Resource, params: Optional[dict] = None) -> int:
        resp = self.get_page(resource, page=1, page_size=0, params=params)

        return resp.json()["count"]

    def iterate(self, resource: Resource, params: Optional[dict] = None) -> Iterator[dict]:
        params = params.copy() if params else {}
        params.update({"page": 1, "page_size": 2500})

        next_url: Optional[str] = self._build_url(resource.value)
        while next_url is not None:
            resp = self.do_request("GET", next_url, params=params)
            data = resp.json()
            yield from data.get("results", [])

            next_url = data.get("next", None)
            params = None  # Avoid duplicating the params, which are already given back in the next URL.

    def create(self, resource: Resource, data: Any, *fields: str) -> Response:
        url = self._build_url(resource.value)
        params = {"fields": ",".join(fields)} if fields else None

        return self.do_request("POST", url, data=data, params=params)

    def update(self, resource: Resource, id: str, data: Any, *fields: str) -> Response:
        url = self._build_url(resource.value, id)
        params = {"fields": ",".join(fields)} if fields else None

        return self.do_request("PATCH", url, data=data, params=params)

    def delete(self, resource: Resource, id: str) -> Response:
        url = self._build_url(resource.value, id)

        return self.do_request("DELETE", url)
