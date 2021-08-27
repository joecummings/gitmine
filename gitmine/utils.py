import logging
from typing import Callable, Mapping

import click
from furl import furl
import requests
from requests import Response, Session


def set_verbosity(verbose: int) -> None:
    """Sets the Log Level given a verbose number."""
    if verbose == 1:
        click.echo("Logging level set to INFO.")
        logging.basicConfig(level=logging.INFO)
    elif verbose >= 2:
        click.echo("Logging level set to DEBUG.")
        logging.basicConfig(level=logging.DEBUG)


def safe_request(
    request_func: Callable[..., Response],
    url: furl,
    headers: Mapping[str, str],
    params: Mapping[str, str],
) -> Response:
    """Wrapper around request to safely return ConnectionError's and bad responses."""
    try:
        response = request_func(url, params=params, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise click.ClickException(e)

    if response.status_code == 401:
        message = "Unauthorized Error 401: Bad Credentials"
        raise click.ClickException(message)

    elif response.status_code != 200:
        message = f"Error encountered with status code: {response.status_code}"
        raise click.ClickException(message)

    return response


class SafeSession(Session):
    """Wrapper around Requests Session obj to safely query API."""

    def safe_get(
        self, url: furl, *, headers: Mapping[str, str], params: Mapping[str, str]
    ) -> Response:
        return safe_request(self.get, url, headers, params)
