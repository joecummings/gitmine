import logging
import logging.config
import sys

import click

from gitmine.constants import LOGGER, LOGGER_PATH, VERBOSE_MAP

try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection  # type: ignore

HTTP_CONNECTION = HTTPConnection("localhost", 8080, timeout=10)

logging.config.fileConfig(LOGGER_PATH)


def set_verbosity(verbose: int) -> None:
    """
    Sets the Log Level given a verbose number
    The requests logger is also set https://stackoverflow.com/questions/16337511/log-all-requests-from-the-python-requests-module
    """
    if verbose > 0:

        log_level = getattr(logging, VERBOSE_MAP.get(min(verbose, 3), ""), None)

        if not isinstance(log_level, int):
            raise click.BadParameter("Incorrect verbosity usage")

        HTTP_CONNECTION.set_debuglevel(1 if log_level < 20 else 0)
        # Set all the available loggers

        for key in logging.Logger.manager.loggerDict:  # type: ignore
            logger = logging.getLogger(key)
            logger.setLevel(log_level)


def catch_bad_responses(res, **kwargs) -> None:
    """ Raise error code if response is not 200 OK
    """
    if res.status_code == 401:
        message = f"Error Fetching {kwargs['get']}. Unauthorized 401: Bad Credentials"
        raise click.ClickException(message)

    elif res.status_code != 200:
        message = f"Error encountered with status code: {res.status_code}"
        raise click.ClickException(message)
