from typing import Callable, List, Optional, TypeVar

import click

from gitmine.commands.config import config_command, get_or_create_github_config
from gitmine.commands.get import get_command
from gitmine.commands.go import go_command
from gitmine.utils import set_verbosity
from gitmine.version import __version__


@click.group()
@click.version_option(__version__)
@click.pass_context
def gitmine(ctx: click.Context) -> None:
    """Simple CLI for querying assigned Issues and PR reviews from Github."""
    # Set the context object
    ctx.obj = get_or_create_github_config()


_verbose_cmd = [
    click.option(
        "-v",
        "--verbose",
        count=True,
        help="Give more output. Option is additive, and can be used up to two times.",
    )
]

T = TypeVar("T")


def add_options(
    options: List[T],
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    def _add_options(func: Callable[..., None]) -> Callable[..., None]:
        for option in reversed(options):
            func = option(func)  # type: ignore
        return func

    return _add_options


@gitmine.command()
@click.argument("prop", nargs=1, required=True, type=click.Choice(["username", "token"]))
@click.argument("value", nargs=1, required=False, type=click.STRING)
@add_options(_verbose_cmd)
@click.pass_context
def config(
    ctx: click.Context,
    prop: str,
    value: str,
    verbose: int,
) -> None:
    """Set or Access Github Config information. Currently, config requires a Github username and Bearer token.

    [username|token] is the property to be set if *value* is also provided. If not, will return the current value of *prop* if it exists.\n
    VALUE is the value of property to be set.
    """
    set_verbosity(verbose)
    config_command(ctx, prop, value)


@gitmine.command()
@click.option(
    "--color/--no-color",
    default=True,
    help="Color code Issues/PRs according to elapsed time.",
)
@click.option(
    "--asc/--desc",
    default=False,
    help="Print Issues/PRs in ascending/descending order of elapsed time.",
)
@click.option(
    "--repo",
    "-r",
    type=click.STRING,
    help="Specify a repo from which to get Issues / PRs.",
)
@click.option(
    "--unassigned",
    "-u",
    is_flag=True,
    default=False,
    help="Get all unassigned Issues / PRs from your repositories.",
)
@click.argument("spec", nargs=1, required=True, type=click.Choice(["issues", "prs", "all"]))
@add_options(_verbose_cmd)
@click.pass_context
def get(
    ctx: click.Context,
    spec: str,
    color: bool,
    asc: bool,
    repo: str,
    unassigned: bool,
    verbose: int,
) -> None:
    """Get assigned Github Issues and/or Github PRs.

    [issues|prs|all] is what information to pull.
    """
    set_verbosity(verbose)
    get_command(ctx, spec, color, asc, repo, unassigned)


@gitmine.command()
@click.argument("repo", nargs=1, required=True, type=click.STRING)
@click.argument("number", nargs=1, required=False, type=click.INT)
@add_options(_verbose_cmd)
@click.pass_context
def go(
    ctx: click.Context,  # pylint: disable=unused-argument
    repo: str,
    number: Optional[int],
    verbose: int,
) -> None:
    """Open a browser page for the given repositiory / issue.

    REPO is the full name of the repository to query.\n
    NUMBER is the issue number of the repository to query. If this is not provided, will open a page to the main page of the repository.
    """
    set_verbosity(verbose)
    go_command(repo, number)
