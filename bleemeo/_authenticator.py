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

import threading
from urllib import parse

import requests

from .exceptions import APIError, AuthenticationError


class Authenticator:
    def __init__(
        self,
        api_url: str,
        session: requests.Session,
        oauth_id: str,
        oauth_secret: str | None = None,
        username: str | None = None,
        password: str | None = None,
        oauth_initial_refresh_token: str | None = None,
    ):
        self.api_url = api_url
        self.session = session
        self.oauth_client_id = oauth_id
        self.oauth_client_secret = oauth_secret
        self.username = username
        self.password = password

        self._lock = threading.Lock()
        self._current_token: str | None = None
        self._current_refresh: str | None = oauth_initial_refresh_token

    @property
    def tokens(self) -> tuple[str, str]:
        with self._lock:
            if not isinstance(self._current_token, str):
                self.__authenticate()

            return str(self._current_token), str(self._current_refresh)

    def get_token(self, force_refetch: bool = False) -> str:
        with self._lock:
            if not self._current_token or force_refetch:
                self.__authenticate()

            return str(self._current_token)

    def __authenticate(self) -> None:
        url = parse.urljoin(self.api_url, "/o/token/")

        if self._current_refresh:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self._current_refresh,
                "client_id": self.oauth_client_id,
            }

            if self.oauth_client_secret:
                data["client_secret"] = self.oauth_client_secret

            response = self.session.post(
                url,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=data,
                timeout=10,
            )
            if response.status_code == 200:
                response_data = response.json()
                self._current_token = response_data["access_token"]
                self._current_refresh = response_data["refresh_token"]

                return

            if not self.username:
                raise AuthenticationError(
                    "The provided initial refresh token is invalid.", response
                )

        data = {
            "grant_type": "password",
            "username": str(self.username),
            "password": self.password or "",
            "client_id": self.oauth_client_id,
        }

        if self.oauth_client_secret:
            data["client_secret"] = self.oauth_client_secret

        response = self.session.post(
            url,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=data,
            timeout=10,
        )
        if response.status_code != 200:
            raise AuthenticationError(
                f"Failed to retrieve OAuth, status={response.status_code}", response
            )

        response_data = response.json()
        self._current_token = response_data["access_token"]
        self._current_refresh = response_data["refresh_token"]

    def logout(self) -> None:
        with self._lock:
            if not self._current_refresh:
                return

            url = parse.urljoin(self.api_url, "/o/revoke_token/")
            data = {
                "token": self._current_refresh,
                "client_id": self.oauth_client_id,
                "token_type_hint": "refresh_token",
            }

            if self.oauth_client_secret:
                data["client_secret"] = self.oauth_client_secret

            response = self.session.post(
                url,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-type": "application/x-www-form-urlencoded",
                },
                data=data,
                timeout=10,
            )
            if response.status_code != 200:
                raise APIError(
                    f"Failed to revoke token, status={response.status_code}", response
                )

            self._current_token = None
            self._current_refresh = None
