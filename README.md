# Bleemeo Python [![Python 3.8 at least](https://img.shields.io/badge/python-%3E%3D3.8-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/release/python-380/) [![GitHub License](https://img.shields.io/github/license/bleemeo/bleemeo-python)](https://github.com/bleemeo/bleemeo-python/blob/main/LICENSE)

Python library for interacting with the Bleemeo API

## Requirements

- Python3.8 or later
- An account on [Bleemeo](https://bleemeo.com/)

## Installation

Take a look at [venv](https://docs.python.org/3/tutorial/venv.html).
This tool provides isolated Python environments, which are more practical than installing packages system-wide.

After you’ve created and activated a virtual environment, run the command:

```shell
python -m pip install --upgrade bleemeo
```

## Documentation

The Python library is documented using docstring
in [the source code](https://github.com/bleemeo/bleemeo-python/bleemeo).

Some examples of library usage can be found in [examples](./examples).

## Basic usage

Listing the first 10 agents of your account:

```python
from bleemeo import Client, Resource, APIError


def list_agents():
    with Client(load_from_env=True) as client:
        try:
            resp_page = client.get_page(Resource.AGENT, page=1, page_size=10,
                                        params={"active": True, "fields": "id,fqdn,display_name"})
            for agent in resp_page.json()["results"]:
                print(f"* Agent {agent['display_name']} (fqdn = {agent['fqdn']}, id = {agent['id']})")
        except APIError as e:
            print(f"API error: {e}:\n{e.response.text}")


if __name__ == '__main__':
    list_agents()
```

Save this file as list_agents.py.

Run it with:

```shell
BLEEMEO_USER=user-email@domain.com BLEEMEO_PASSWORD=password python3 list_agents.py
```

> More examples can be found in [examples](./examples)

To run an example from a clone of this repository, run the following:

```shell
BLEEMEO_USER=user-email@domain.com BLEEMEO_PASSWORD=password python3 examples/list_metrics.py
```

## Environment

At least the following options should be configured (as environment variables or with options):

- Credentials OR initial refresh token
- All other configuration options are optional and could be omitted

> Ways to provide those options are referenced in the [Configuration](#configuration) section.

## Configuration

**For environment variables to be taken into account, the parameter `load_from_env` of the `Client` constructor must be
set to `True`.**

| Property                      | Constructor parameter(s)                  | Env variable(s)                                           | Default values                                                       |
|-------------------------------|-------------------------------------------|-----------------------------------------------------------|----------------------------------------------------------------------|
| Credentials                   | `username` & `password`                   | `BLEEMEO_USER` & `BLEEMEO_PASSWORD`                       | None. This option is required (unless initial refresh token is used) |
| Bleemeo account header        | `account_id`                              | `BLEEMEO_ACCOUNT_ID`                                      | The first account associated with used credentials.                  |
| OAuth client ID/secret        | `oauth_client_id` & `oauth_client_secret` | `BLEEMEO_OAUTH_CLIENT_ID` & `BLEEMEO_OAUTH_CLIENT_SECRET` | The default SDK OAuth client ID                                      |
| API URL                       | `api_url`                                 | `BLEEMEO_API_URL`                                         | `https://api.bleemeo.com`                                            |
| Initial refresh token         | `oauth_initial_refresh_token`             | `BLEEMEO_OAUTH_INITIAL_REFRESH_TOKEN`                     | None. This is an alternative to username & password credentials.     |
| Custom headers                | `custom_headers`                          | -                                                         | `{"User-Agent": "Bleemeo Python Client"}`                            |
| Throttle max auto retry delay | `throttle_max_auto_retry_delay`           | -                                                         | 1 minute.                                                            |
