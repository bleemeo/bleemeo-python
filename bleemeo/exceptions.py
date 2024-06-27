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

from datetime import datetime, timedelta

import requests


class ConfigurationError(Exception):
    """A ConfigurationError is raised when a misconfiguration is detected."""

    pass


class APIError(Exception):
    """
    An APIError is raised when the API returns a non-successful status code.
    It serves as superclass for AuthenticationError and ThrottleError.
    """

    def __init__(self, message: str, response: requests.Response) -> None:
        super(Exception, self).__init__(message)
        self.response = response


class AuthenticationError(APIError):
    """An AuthenticationError is raised when the API returns a 401 - Unauthorized status code."""

    pass


class ThrottleError(APIError):
    """
    A ThrottleError is raised when the API returns a 429 - Too Many Requests status code.
    It contains the delay and the deadline until a new request can safely be sent.
    If the error is not raised from the throttle-prevention mechanism, it also contains the API response.
    """

    def __init__(
        self,
        response: requests.Response | None = None,
        delay_seconds: int | None = None,
    ) -> None:
        ds = 30
        if delay_seconds is not None:
            ds = delay_seconds
        elif response is not None and "Retry-After":
            ds = int(response.headers.get("Retry-After") or 30)

        super(APIError, self).__init__(
            f"Throttle error: request must be retried after {ds}s.", response
        )
        self.delay_seconds = ds
        self.throttle_deadline = datetime.now() + timedelta(seconds=ds)

    @classmethod
    def prevent(cls, delay_seconds: int) -> ThrottleError:
        """prevent can be used to build a ThrottleError without actually sending the request to the API."""
        return cls(response=None, delay_seconds=delay_seconds)
