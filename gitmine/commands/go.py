import click
from typing import Optional


def go_command(repo: str, number: Optional[int]) -> None:
    """ Implementation of the *go* command.
    """

    url = f"https://github.com/{repo}/issues/{number if number else ''}"
    click.launch(url)
