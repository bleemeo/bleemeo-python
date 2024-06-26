# Copyright 2015-2024 Bleemeo
#
# bleemeo.com an infrastructure monitoring solution in the Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import math
import os
import time
from collections.abc import Iterator, Sequence
from datetime import datetime, timedelta
from typing import Any
from urllib import parse

from requests import Request, Response, Session

from ._authenticator import Authenticator
from .exceptions import APIError, AuthenticationError, ConfigurationError, ThrottleError
from .resources import Resource


class Client:
    DEFAULT_ENDPOINT = "https://api.bleemeo.com"
    DEFAULT_OAUTH_CLIENT_ID = "1fc6de3e-8750-472e-baea-3ba22bb4eb56"
    DEFAULT_THROTTLE_MAX_AUTO_RETRY_DELAY = 60  # seconds
    DEFAULT_USER_AGENT = "Bleemeo Python Client"

    def __init__(
        self,
        *,
        api_url: str | None = None,
        account_id: str | None = None,
        username: str | None = None,
        password: str | None = None,
        oauth_client_id: str | None = None,
        oauth_client_secret: str | None = None,
        oauth_initial_refresh_token: str | None = None,
        custom_headers: dict[str, Any] | None = None,
        throttle_max_auto_retry_delay: int | None = None,
        load_from_env: bool = False,
    ):
        if load_from_env:
            api_url = api_url or os.environ.get("BLEEMEO_API_URL")
            account_id = account_id or os.environ.get("BLEEMEO_ACCOUNT_ID")
            username = username or os.environ.get("BLEEMEO_USER")
            password = password or os.environ.get("BLEEMEO_PASSWORD")
            oauth_client_id = oauth_client_id or os.environ.get(
                "BLEEMEO_OAUTH_CLIENT_ID"
            )
            oauth_client_secret = oauth_client_secret or os.environ.get(
                "BLEEMEO_OAUTH_CLIENT_SECRET"
            )
            oauth_initial_refresh_token = oauth_initial_refresh_token or os.environ.get(
                "BLEEMEO_OAUTH_INITIAL_REFRESH_TOKEN"
            )

        if not username and not oauth_initial_refresh_token:
            raise ConfigurationError(
                "Either a username or an initial oAuth refresh token must be provided."
            )

        self.api_url = api_url or self.DEFAULT_ENDPOINT
        self.username = username
        self.password = password
        self.oauth_client_id = oauth_client_id or self.DEFAULT_OAUTH_CLIENT_ID
        self.oauth_client_secret = oauth_client_secret
        self.oauth_initial_refresh_token = oauth_initial_refresh_token
        self.throttle_max_auto_retry_delay = (
            throttle_max_auto_retry_delay or self.DEFAULT_THROTTLE_MAX_AUTO_RETRY_DELAY
        )
        self.session = Session()
        self.session.headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
        }

        if account_id:
            self.session.headers["X-Bleemeo-Account"] = account_id
        if custom_headers:
            self.session.headers.update(custom_headers)

        self._throttle_deadline = datetime.min
        self._authenticator = Authenticator(
            self.api_url,
            self.session,
            self.oauth_client_id,
            self.oauth_client_secret,
            self.username,
            self.password,
            self.oauth_initial_refresh_token,
        )

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.logout()

    def logout(self) -> None:
        self._authenticator.logout()
        self.session.close()

    def _build_url(self, *parts: str) -> str:
        url = self.api_url
        for part in parts:
            url = parse.urljoin(url, part)
        if not url.endswith("/"):
            url = url + "/"
        return url

    def _do_request(
        self, request: Request, authenticated: bool, is_retry: bool = False
    ) -> Response:
        request.headers = (
            {} if request.json is None else {"Content-Type": "application/json"}
        )

        if authenticated:
            request.headers.update(
                {
                    "Authorization": f"Bearer {self._authenticator.get_token(force_refetch=is_retry)}"
                }
            )

        prep = self.session.prepare_request(request)
        # Merge environment settings into session
        settings = self.session.merge_environment_settings(
            prep.url, {}, None, None, None
        )
        resp = self.session.send(prep, **settings)
        if resp.status_code == 401 and authenticated and not is_retry:
            resp = self._do_request(request, authenticated=True, is_retry=True)

        return resp

    def _do_request_handling(
        self, authenticated: bool, method: str, req: Request
    ) -> Response:
        response = self._do_request(req, authenticated)
        if response.status_code >= 400:
            if response.status_code == 400:  # Bad Request
                raise APIError(f"Bad request on {req.url}", response)
            if response.status_code == 401:  # Unauthorized
                raise AuthenticationError(
                    f"Authentication failed on {req.url}", response
                )
            if response.status_code == 404:  # Not Found
                raise APIError(f"Resource {req.url} not found", response)
            if response.status_code == 429:  # Too Many Requests
                throttle_error = ThrottleError(response)
                self._throttle_deadline = throttle_error.throttle_deadline
                raise throttle_error

            raise APIError(
                f"Request {method} on {req.url} failed with status {response.status_code}",
                response,
            )
        return response

    def do(
        self,
        method: str,
        url: str,
        authenticated: bool = True,
        params: dict[str, Any] | None = None,
        data: Any | None = None,
    ) -> Response:
        time_to_wait = self._throttle_deadline - datetime.now()
        if time_to_wait > timedelta(seconds=0):
            raise ThrottleError.prevent(math.ceil(time_to_wait.total_seconds()))

        req = Request(
            method=method,
            url=self._build_url(url),
            json=data,
            params=params,
        )

        try:
            response = self._do_request_handling(authenticated, method, req)
        except ThrottleError as throttle_error:
            if (
                self.throttle_max_auto_retry_delay is None
                or throttle_error.delay_seconds > self.throttle_max_auto_retry_delay
            ):
                raise throttle_error

            time.sleep(self.throttle_max_auto_retry_delay)

            response = self._do_request_handling(authenticated, method, req)

        return response

    def get(
        self, resource: Resource, id: str, fields: Sequence[str] | None = None
    ) -> Response:
        url = parse.urljoin(resource.value, id)
        params = {"fields": ",".join(fields)} if fields else None

        return self.do("GET", url, params=params)

    def get_page(
        self,
        resource: Resource,
        *,
        page: int = 1,
        page_size: int = 25,
        params: dict[str, Any] | None = None,
    ) -> Response:
        url = resource.value
        params = params.copy() if params else {}
        params.update({"page": page, "page_size": page_size})

        return self.do("GET", url, params=params)

    def count(self, resource: Resource, params: dict[str, Any] | None = None) -> int:
        resp = self.get_page(resource, page=1, page_size=0, params=params)

        return int(resp.json()["count"])

    def iterate(
        self, resource: Resource, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        params = params.copy() if params else {}
        params.update({"page_size": 2500})

        next_url: str | None = self._build_url(resource.value)
        while next_url is not None:
            resp = self.do("GET", next_url, params=params)
            data = resp.json()
            yield from data.get("results", [])

            next_url = data.get("next", None)
            params = None  # Avoid duplicating the params, which are already given back in the next URL.

    def create(self, resource: Resource, data: Any, *fields: str) -> Response:
        url = resource.value
        params = {"fields": ",".join(fields)} if fields else None

        return self.do("POST", url, data=data, params=params)

    def update(self, resource: Resource, id: str, data: Any, *fields: str) -> Response:
        url = parse.urljoin(resource.value, id)
        params = {"fields": ",".join(fields)} if fields else None

        return self.do("PATCH", url, data=data, params=params)

    def delete(self, resource: Resource, id: str) -> Response:
        url = parse.urljoin(resource.value, id)

        return self.do("DELETE", url)
