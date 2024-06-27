import json
import unittest
from typing import Any, Callable
from unittest import mock

from bleemeo import ConfigurationError, Client, Resource
from bleemeo._authenticator import Authenticator


class _MockResponse:
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self.content = content

    def json(self) -> Any:
        return json.loads(self.content)


class ClientTest(unittest.TestCase):
    def test_configuration_validation(self) -> None:
        # Initializing a Client without credentials nor initial refresh token should raise an exception
        self.assertRaises(ConfigurationError, Client)

    def test_client_do(self) -> None:
        test_cases = [
            {
                "client_method": "get",
                "client_params": {"resource": Resource.METRIC, "id": "000"},
                "resp_code": 200,
                "resp_content": b'{"id":"000"}',
                "expected_exception": None,
                "expected_value": None,
                "expected_json": {"id": "000"}
            }
        ]

        with mock.patch.object(Authenticator, "get_token", return_value="token"):
            for tc in test_cases:
                with self.subTest():
                    with mock.patch.object(Client, "_send",
                                           return_value=_MockResponse(tc["resp_code"], tc["resp_content"])):
                        client = Client(username="test")
                        method = getattr(client, tc["client_method"])
                        executor: Callable[[], Any] = lambda: method(**tc["client_params"])

                        if tc["expected_exception"] is not None:
                            result = self.assertRaises(tc["expected_exception"], executor)
                        else:
                            result = executor()

                        if tc["expected_value"] is not None:
                            self.assertEqual(tc["expected_value"], result)
                        elif tc["expected_json"] is not None:
                            self.assertEqual(tc["expected_json"], result.json())


if __name__ == '__main__':
    unittest.main()
