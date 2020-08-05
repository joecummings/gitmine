import logging
from typing import Optional

import click

from gitmine.constants import LOGGER

logger = logging.getLogger(LOGGER)


def go_command(repo: str, number: Optional[int]) -> None:
    """ Implementation of the *go* command.
    """
    logger.info(f"Launching browser session at repo: {repo}, issue: {number}")
    url = f"https://github.com/{repo}/issues/{number if number else ''}"
    click.launch(url)
