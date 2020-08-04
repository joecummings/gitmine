import click

from typing import Optional

try: 
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection

from gitmine.commands.config import config_command, get_or_create_github_config
from gitmine.commands.get import get_command
from gitmine.commands.go import go_command
from gitmine.constants import LOGGER, LOGGER_PATH

import logging
import logging.config
logging.config.fileConfig(LOGGER_PATH)

@click.group()
@click.option(
    "--verbosity", "-v",
    default="ERROR",
    metavar="LVL",
    help="{CRITICAL | ERROR | WARNING | INFO | DEBUG}"
)
@click.pass_context
def gitmine(ctx: click.Context, verbosity: str):
    """ Simple CLI for querying assigned Issues and PR reviews from Github.
    """
    log_level = getattr(logging, verbosity.upper(), None)
    
    if not isinstance(log_level, int):
        raise click.BadParameter("Verbosity must be CRITICAL, ERROR, WARNING, INFO or DEBUG")
    
    #Set the requests logger https://stackoverflow.com/questions/16337511/log-all-requests-from-the-python-requests-module
    HTTPConnection.debuglevel = 1 if log_level <= 20 else 0
    #Set all the available loggers
    for key in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(key)
        logger.setLevel(log_level)

    #Set the context object
    ctx.obj = get_or_create_github_config()


@gitmine.command()
@click.option(
    "--encrypt/--no-encrypt",
    default=False,
    help="Encrypt your credentials. Undo encryption by re-setting the config without the flag."
)
@click.argument(
    "prop", nargs=1, required=True, type=click.Choice(["username", "token"])
)
@click.argument("value", nargs=1, required=False, type=click.STRING)
@click.pass_context
def config(ctx: click.Context, prop: str, value: str, encrypt: bool) -> None:
    """ Set or Access Github Config information. Currently, config requires a Github username and Bearer token.

    [username|token] is the property to be set if *value* is also provided. If not, will return the current value of *prop* if it exists.\n
    VALUE is the value of property to be set.
    """
    config_command(ctx, prop, value, encrypt)


@gitmine.command()
@click.option(
    "--color/--no-color",
    default=True,
    help="Color code Issues/PRs according to elapsed time.",
)
@click.option(
    "--asc/--desc",
    default=False,
    help="Print Issues/PRs in ascending/descending order of elapsed time",
)
@click.argument(
    "spec", nargs=1, required=True, type=click.Choice(["issues", "prs", "all"])
)
@click.pass_context
def get(ctx: click.Context, spec: str, color: bool, asc: bool) -> None:
    """ Get assigned Github Issues and/or Github PRs.

    [issues|prs|all] is what information to pull. Can be {issues, prs, all}.
    """
    get_command(ctx, spec, color, asc)


@gitmine.command()
@click.argument("repo", nargs=1, required=True, type=click.STRING)
@click.argument("number", nargs=1, required=False, type=click.INT)
@click.pass_context
def go(ctx: click.Context, repo: str, number: Optional[int]) -> None:
    """ Open a browser page for the given repositiory / issue.

    REPO is the full name of the repository to query.\n
    NUMBER is the issue number of the repository to query. If this is not provided, will open a page to the main page of the repository.
    """
    go_command(repo, number)


def main():
    gitmine(obj={})

if __name__ == "__main__":
    main()
