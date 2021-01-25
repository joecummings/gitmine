import logging

import click
from requests import Response


def set_verbosity(verbose: int) -> None:
    """ Sets the Log Level given a verbose number.
    """
    if verbose == 1:
        click.echo("Logging level set to INFO.")
        logging.basicConfig(level=logging.INFO)
    elif verbose == 2:
        click.echo("Logging level set to DEBUG.")
        logging.basicConfig(level=logging.DEBUG)


def catch_bad_responses(res: Response, **kwargs: str) -> None:
    """ Raise error code if response is not 200 OK.
    """
    if res.status_code == 401:
        message = f"Error Fetching {kwargs['get']}. Unauthorized 401: Bad Credentials"
        raise click.ClickException(message)

    elif res.status_code != 200:
        message = f"Error encountered with status code: {res.status_code}"
        raise click.ClickException(message)
