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

from datetime import datetime, timedelta

import requests


class ConfigurationError(Exception):
    pass


class APIError(Exception):
    def __init__(self, message: str, response: requests.Response) -> None:
        super(Exception, self).__init__(message)
        self.response = response


class AuthenticationError(APIError):
    pass


class ThrottleError(APIError):
    def __init__(self, response: requests.Response) -> None:
        delay_seconds = response.headers.get("Retry-After") or 30
        super(APIError, self).__init__(
            f"Throttle error: request must be retried after {delay_seconds}s.", response
        )
        self.throttle_deadline = datetime.now() + timedelta(seconds=int(delay_seconds))
