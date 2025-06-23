# Copyright 2015-2025 Bleemeo
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

from requests import PreparedRequest, Request, Response, Session

from ._authenticator import Authenticator
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    ResourceNotFoundError,
    ThrottleError,
)
from .resources import Resource


class Client:
    """
    A Client is a helper to interact with the Bleemeo API,
    providing methods to retrieve, list, create, update and delete resources.
    """

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
        throttle_max_auto_retry_delay: int
        | None = DEFAULT_THROTTLE_MAX_AUTO_RETRY_DELAY,
        load_from_env: bool = False,
    ):
        """
        The credentials (username or initial refresh token) are the only mandatory parameters.
        They can alternatively be provided as environment variables, by setting `load_from_env` to True.
        See the [README](https://github.com/bleemeo/bleemeo-python/#configuration) for extended details.

        Args:
            api_url (str | None): Base URL to access the Bleemeo API.
            account_id (str | None): Your Bleemeo account ID.
            username (str | None): Your Bleemeo username.
            password (str | None): Your Bleemeo password.
            oauth_client_id (str | None): Your Bleemeo OAuth client ID.
            oauth_client_secret (str | None): Your Bleemeo OAuth client secret.
            oauth_initial_refresh_token (str | None): An initial OAuth refresh token
                (as an alternative to username/password credentials).
            custom_headers (dict[str, Any]): Additional headers to pass to the Bleemeo API.
            throttle_max_auto_retry_delay (int | None): Maximum number of seconds to wait
                for retrying a throttled request (can be set to 0 or None not to retry at all).
            load_from_env (bool): Whether to load environment variables as Client parameters.

        Raises:
            ConfigurationError: If neither credentials nor initial refresh token are provided.
        """
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
                "Either a username or an initial OAuth refresh token must be provided."
            )

        self.api_url = api_url or self.DEFAULT_ENDPOINT
        self.username = username
        self.password = password
        self.oauth_client_id = oauth_client_id or self.DEFAULT_OAUTH_CLIENT_ID
        self.oauth_client_secret = oauth_client_secret
        self.oauth_initial_refresh_token = oauth_initial_refresh_token
        self.throttle_max_auto_retry_delay = throttle_max_auto_retry_delay
        self.session = Session()
        self.session.headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "application/json",
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

    @property
    def account_id(self) -> str | None:
        return (
            str(self.session.headers["X-Bleemeo-Account"])
            if "X-Bleemeo-Account" in self.session.headers
            else None
        )

    @account_id.setter
    def account_id(self, account_id: str | None) -> None:
        if account_id:
            self.session.headers["X-Bleemeo-Account"] = account_id
        else:
            del self.session.headers["X-Bleemeo-Account"]

    @property
    def tokens(self) -> tuple[str, str]:
        """tokens returns a tuple containing the current access and refresh tokens."""
        return self._authenticator.tokens

    def logout(self) -> None:
        """logout revokes the OAuth token, preventing it from being reused."""
        self._authenticator.logout()
        self.session.close()

    def _build_url(self, *parts: str) -> str:
        raw_url = self.api_url
        for part in parts:
            raw_url = parse.urljoin(raw_url, part)

        url = parse.urlparse(raw_url)
        url_with_slash = parse.ParseResult(
            url.scheme,
            url.netloc,
            url.path if url.path.endswith("/") else url.path + "/",
            url.params,
            url.query,
            url.fragment,
        )

        return url_with_slash.geturl()

    def _send(self, req: PreparedRequest, settings: Any) -> Response:
        """_send wraps `Session.send()` to make it easily mockable."""
        return self.session.send(req, **settings)

    def _do_request(
        self, request: Request, authenticated: bool, is_retry: bool = False
    ) -> Response:
        if request.headers is None:
            request.headers = {}

        if "Content-Type" not in request.headers and request.json:
            request.headers["Content-Type"] = "application/json"

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

        resp = self._send(prep, settings)
        if resp.status_code == 401 and authenticated and not is_retry:
            resp = self._do_request(request, authenticated=True, is_retry=True)

        return resp

    def _do_with_error_handling(self, authenticated: bool, req: Request) -> Response:
        response = self._do_request(req, authenticated)
        if response.status_code >= 400:
            if response.status_code == 400:  # Bad Request
                raise BadRequestError(response)
            if response.status_code == 401:  # Unauthorized
                raise AuthenticationError(
                    f"Authentication failed on {req.url}", response
                )
            if response.status_code == 404:  # Not Found
                raise ResourceNotFoundError(req.url, response)
            if response.status_code == 429:  # Too Many Requests
                throttle_error = ThrottleError(response)
                self._throttle_deadline = throttle_error.throttle_deadline
                raise throttle_error

            raise APIError(
                f"Request {req.method} on {req.url} failed with status {response.status_code}",
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
        """
        do is a lower-level method to build and execute the request according to the given parameters.
        It raises errors depending on the received response, and handles throttled requests retry.

        When possible, prefer the higher-level get, get_page, count, iterate, create, update and delete.

        Args:
            method (str): The HTTP method to execute the request as.
            url (str): The (relative) URL on which to execute the request.
            authenticated (bool): Whether the request should be authenticated.
            params (dict[str, Any]): The parameters to pass to the request.
            data (Any | None): The body of the request in case of a POST or a PATCH.

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
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
            response = self._do_with_error_handling(authenticated, req)
        except ThrottleError as throttle_error:
            if (
                not self.throttle_max_auto_retry_delay
                or throttle_error.delay_seconds > self.throttle_max_auto_retry_delay
            ):
                raise throttle_error

            time.sleep(throttle_error.delay_seconds)

            response = self._do_with_error_handling(authenticated, req)

        return response

    def get(
        self, resource: Resource | str, id: str, fields: Sequence[str] | None = None
    ) -> Response:
        """
        get retrieves the resource with the given id with only the given fields, if any.

        Args:
            resource (Resource | str): The kind of resource to retrieve.
            id (str): The id of the resource to retrieve.
            fields (Sequence[str] | None, optional): Specific fields to retrieve. Defaults to None (only the default ones).

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        url = parse.urljoin(
            resource.value if isinstance(resource, Resource) else resource, id
        )
        params = {"fields": ",".join(fields)} if fields else None

        return self.do("GET", url, params=params)

    def get_page(
        self,
        resource: Resource | str,
        *,
        page: int = 1,
        page_size: int = 25,
        params: dict[str, Any] | None = None,
    ) -> Response:
        """
        get_page retrieves a given-page-sized list of resources matching the given params at the given page.
        To collect all the resources matching some params (i.e., instead of querying all pages one by one),
        prefer using the `iterate()` method which is faster.

        Args:
            resource (Resource | str): The kind of resource to retrieve.
            page (int): The number of the page to retrieve.
            page_size (int): The size of the page to retrieve.
            params (dict[str, Any]): The parameters the resources should match.

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        url = resource.value if isinstance(resource, Resource) else resource
        params = params.copy() if params else {}
        params.update({"page": page, "page_size": page_size})

        return self.do("GET", url, params=params)

    def count(
        self, resource: Resource | str, params: dict[str, Any] | None = None
    ) -> int:
        """
        count returns the number of resources matching the given params.

        Args:
            resource (Resource | str): The kind of resource to count.
            params (dict[str, Any]): The parameters the resources should match.

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        resp = self.get_page(resource, page=1, page_size=0, params=params)

        return int(resp.json()["count"])

    def iterate(
        self, resource: Resource | str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """
        iterate yields the resources of the given kind matching the given params.

        Args:
            resource (Resource | str): The kind of resource to iterate.
            params (dict[str, Any]): The parameters the resources should match.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        params = params.copy() if params else {}
        params.setdefault("page_size", 2500)

        next_url: str | None = self._build_url(
            resource.value if isinstance(resource, Resource) else resource
        )
        while next_url is not None:
            resp = self.do("GET", next_url, params=params)
            data = resp.json()
            yield from data.get("results", [])

            next_url = data.get("next", None)
            params = None  # Avoid duplicating the params, which are already given back in the next URL.

    def create(
        self, resource: Resource | str, data: Any, fields: Sequence[str] | None = None
    ) -> Response:
        """
        create creates a new resource of the given kind with the given data.
        Fields expected to be returned can be specified as varargs.

        Args:
            resource (Resource | str): The kind of resource to create.
            data (Any): The body of the POST request.
            fields (Sequence[str] | None): Specific fields to retrieve. Defaults to None (only the default ones).

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        url = resource.value if isinstance(resource, Resource) else resource
        params = {"fields": ",".join(fields)} if fields else None

        return self.do("POST", url, data=data, params=params)

    def update(
        self,
        resource: Resource | str,
        id: str,
        data: Any,
        fields: Sequence[str] | None = None,
    ) -> Response:
        """
        update updates the resource of the given kind and id with the given data.
        Since the request is sent as a PATCH, only the fields specified in the body (data) will be updated.
        Fields expected to be returned can be specified as varargs.

        Args:
            resource (Resource | str): The kind of resource to update.
            id (str): The ID of the resource to update.
            data (Any): The body of the PATCH request.
            fields (Sequence[str] | None): Specific fields to retrieve. Defaults to None (only the default ones).

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        url = parse.urljoin(
            resource.value if isinstance(resource, Resource) else resource, id
        )
        params = {"fields": ",".join(fields)} if fields else None

        return self.do("PATCH", url, data=data, params=params)

    def delete(self, resource: Resource | str, id: str) -> Response:
        """
        delete deletes the resource of the given kind and id from the server.

        Args:
            resource (Resource | str): The kind of resource to delete.
            id (str): The ID of the resource to delete.

        Returns:
            Response: The response to the request.

        Raises:
            AuthenticationError: If the authentication fails.
            ThrottleError: If too many requests are sent too close.
            APIError: When receiving a non-successful status code not covered by the above exceptions.
        """
        url = parse.urljoin(
            resource.value if isinstance(resource, Resource) else resource, id
        )

        return self.do("DELETE", url)
