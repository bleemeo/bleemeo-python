from typing import Optional
from urllib import parse

import requests

from .exceptions import AuthenticationError, APIError


class Authenticator:

    def __init__(self,
                 api_url: str,
                 session: requests.Session,
                 oauth_id: str,
                 oauth_secret: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 oauth_initial_refresh_token: Optional[str] = None,
                 ):
        self.api_url = api_url
        self._insecure = not api_url.startswith("https://")
        self.session = session
        self.oauth_client_id = oauth_id
        self.oauth_client_secret = oauth_secret
        self.username = username
        self.password = password
        self.oauth_initial_refresh_token = oauth_initial_refresh_token

        self.__current_token: Optional[str] = None
        self.__current_refresh: Optional[str] = None

    def get_token(self, force_refetch=False) -> str:
        if not self.__current_token or force_refetch:
            self.__authenticate()

        return self.__current_token

    def __authenticate(self):
        url = parse.urljoin(self.api_url, "/o/token/")

        if self.__current_refresh or self.oauth_initial_refresh_token:
            refresh_token = self.__current_refresh or self.oauth_initial_refresh_token
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.oauth_client_id,
                "client_secret": self.oauth_client_secret,
            }

            response = self.session.post(
                url,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-type": "application/x-www-form-urlencoded",
                },
                data=data,
                timeout=10,
                verify=not self._insecure,
            )
            if response.status_code == 200:
                response_data = response.json()
                self.__current_token = response_data["access_token"]
                self.__current_refresh = response_data["refresh_token"]

                if self.oauth_initial_refresh_token:  # Won't be used no more
                    self.oauth_initial_refresh_token = None

                return

        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.oauth_client_id,
            "client_secret": self.oauth_client_secret,
        }

        response = self.session.post(
            url,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Content-type": "application/x-www-form-urlencoded",
            },
            data=data,
            timeout=10,
            verify=not self._insecure,
        )
        if response.status_code != 200:
            raise AuthenticationError(f"Failed to retrieve OAuth, status={response.status_code}", response)

        response_data = response.json()
        self.__current_token = response_data["access_token"]
        self.__current_refresh = response_data["refresh_token"]

    def logout(self):
        if not self.__current_refresh:
            return

        url = parse.urljoin(self.api_url, "/o/revoke_token/")
        data = {
            "token": self.__current_refresh,
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
            verify=not self._insecure,
        )
        if response.status_code != 200:
            raise APIError(f"Failed to revoke token, status={response.status_code}", response)

        self.__current_token = None
        self.__current_refresh = None
