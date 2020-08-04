import click
from typing import Optional

from gitmine.constants import LOGGER

import logging
logger = logging.getLogger(LOGGER)

def go_command(repo: str, number: Optional[int]) -> None:
    """ Implementation of the *go* command.
    """
    logger.info(f"Launching browser session at repo: {repo}, issue: {nnumber}")
    url = f"https://github.com/{repo}/issues/{number if number else ''}"
    click.launch(url)
