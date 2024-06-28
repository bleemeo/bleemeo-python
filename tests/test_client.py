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

import json
import unittest
from typing import Any, Protocol
from unittest import mock

from bleemeo import Client, ConfigurationError, Resource
from bleemeo._authenticator import Authenticator


class _MockResponse:
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self.content = content

    def json(self) -> Any:
        return json.loads(self.content)


class _ClientTestCase:
    def __init__(
        self,
        client_method: str,
        client_params: dict[str, Any],
        response: _MockResponse,
        expected_exception: type[Exception] | None = None,
        expected_json: dict[str, Any] | None = None,
        expected_retval: Any | None = None,
    ) -> None:
        self.client_method = client_method
        self.client_params = client_params
        self.response = response
        self.expected_exception = expected_exception
        self.expected_json = expected_json
        self.expected_retval = expected_retval


class ClientMethod(Protocol):
    def __call__(self, **params: Any) -> Any: ...


class _Executor:
    def __init__(self, fn: ClientMethod, params: dict[str, Any]) -> None:
        self._fn = fn
        self._params = params
        self.result: Any | None = None

    def execute(self) -> None:
        self.result = self._fn(**self._params)


class ClientTest(unittest.TestCase):
    def test_configuration_validation(self) -> None:
        # Initializing a Client without credentials nor initial refresh token should raise an exception
        self.assertRaises(ConfigurationError, Client)

    def test_client_methods(self) -> None:
        test_cases = [
            _ClientTestCase(
                client_method="get",
                client_params={
                    "resource": Resource.METRIC,
                    "id": "1",
                    "fields": ("id",),
                },
                response=_MockResponse(200, b'{"id":"1"}'),
                expected_json={"id": "1"},
            ),
            _ClientTestCase(
                client_method="get_page",
                client_params={"resource": Resource.AGENT, "page_size": 2},
                response=_MockResponse(
                    200, b'{"results":[{"id":"1"},{"id":"2"}],"count":2}'
                ),
                expected_json={"results": [{"id": "1"}, {"id": "2"}], "count": 2},
            ),
            _ClientTestCase(
                client_method="count",
                client_params={"resource": Resource.WIDGET},
                response=_MockResponse(
                    200, b'{"results":[{"id":"1"},{"id":"2"},{"id":"3"}],"count":3}'
                ),
                expected_json={
                    "results": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
                    "count": 3,
                },
                expected_retval=3,
            ),
            _ClientTestCase(
                client_method="create",
                client_params={
                    "resource": Resource.DASHBOARD,
                    "data": {"name": "D"},
                    "fields": "id,name",
                },
                response=_MockResponse(201, b'{"id":"1","name":"D"}'),
                expected_json={"id": "1", "name": "D"},
            ),
            _ClientTestCase(
                client_method="update",
                client_params={
                    "resource": Resource.ACCOUNT,
                    "id": "1",
                    "data": {"name": "A"},
                    "fields": ("id", "name"),
                },
                response=_MockResponse(200, b'{"id":"1","name":"A"}'),
                expected_json={"id": "1", "name": "A"},
            ),
            _ClientTestCase(
                client_method="delete",
                client_params={"resource": Resource.TAG, "id": "1"},
                response=_MockResponse(204, b""),
            ),
        ]

        with mock.patch.object(Authenticator, "get_token", return_value="token"):
            for tc in test_cases:
                with self.subTest(
                    f"{tc.client_method} - {tc.client_params['resource']}"
                ):
                    with mock.patch.object(
                        Client,
                        "_send",
                        return_value=tc.response,
                    ):
                        client = Client(username="test")
                        method = getattr(client, tc.client_method)
                        executor = _Executor(method, tc.client_params)

                        if tc.expected_exception is not None:
                            self.assertRaises(tc.expected_exception, executor.execute)
                        else:
                            executor.execute()

                        if tc.expected_retval is not None:
                            self.assertEqual(tc.expected_retval, executor.result)
                        elif tc.expected_json is not None:
                            self.assertEqual(tc.expected_json, executor.result.json())  # type: ignore


if __name__ == "__main__":
    unittest.main()
