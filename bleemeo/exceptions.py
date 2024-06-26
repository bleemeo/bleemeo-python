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
        super(APIError, self).__init__(f"Throttle error: request must be retried after {delay_seconds}s.", response)
        self.throttle_deadline = datetime.now() + timedelta(seconds=int(delay_seconds))
